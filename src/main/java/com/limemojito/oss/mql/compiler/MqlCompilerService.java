/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.intellij.execution.process.CapturingProcessHandler;
import com.intellij.execution.process.ProcessOutput;
import com.intellij.openapi.progress.ProcessCanceledException;
import com.intellij.openapi.progress.ProgressIndicator;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.components.Service;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.vfs.VirtualFile;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Compiles a single MQL program with the real MetaEditor compiler and returns structured diagnostics.
 * The command actually run is picked by trying a small ordered list of {@link MqlCompilerLauncher}
 * strategies and using the first one that reports itself available: {@link Mt5CliLauncher} (macOS,
 * via the {@code mt5} Wine wrapper — the one exercised on this development machine),
 * {@link MetaEditorLauncher} (Windows, native {@code metaeditor64.exe}), then {@link WineLauncher}
 * (Linux/other, explicit Wine binary + exe). If none is available, {@link #compile} returns
 * {@link CompileResult#unavailable()} rather than guessing (see docs/REVAMP_PLAN.md Phase 1).
 *
 * <p>Results are memoised per file by modification stamp, so re-analysing unchanged content never
 * re-spawns the compiler (the flagship must not hammer Wine on every daemon pass). The last result
 * per file is also kept (even when the compiler was unavailable) so UI such as the status-bar
 * widget can show "not compiled" vs. "compiler N/A" vs. an actual error/warning count.</p>
 */
@Service(Service.Level.PROJECT)
public final class MqlCompilerService {

    private static final Logger LOG = Logger.getInstance(MqlCompilerService.class);
    private static final long COMPILE_TIMEOUT_MS = 60_000;

    @NotNull
    private final List<MqlCompilerLauncher> launchers;

    /** path -> (modificationStamp, result); only ever holds results where the compiler was available. */
    private final Map<String, Cached> cache = new ConcurrentHashMap<>();

    /** path -> most recent result (available or not) for UI display; not used to skip recompiling. */
    private final Map<String, CompileResult> lastResults = new ConcurrentHashMap<>();

    public MqlCompilerService() {
        this(List.of(new Mt5CliLauncher(), new MetaEditorLauncher(), new WineLauncher()));
    }

    /** Visible for testing: inject explicit launchers instead of the OS-probed defaults. */
    public MqlCompilerService(@NotNull List<MqlCompilerLauncher> launchers) {
        this.launchers = List.copyOf(launchers);
    }

    public record CompileResult(@NotNull List<CompilerDiagnostic> diagnostics,
                                boolean compilerAvailable,
                                int errors,
                                int warnings) {
        static CompileResult unavailable() {
            return new CompileResult(Collections.emptyList(), false, 0, 0);
        }
    }

    private record Cached(long stamp, @NotNull CompileResult result) {
    }

    /** Compiles {@code file} (or returns the memoised result if its content is unchanged). Never throws. */
    @NotNull
    public CompileResult compile(@NotNull VirtualFile file) {
        String path = file.getPath();
        long stamp = file.getModificationStamp();
        Cached hit = cache.get(path);
        if (hit != null && hit.stamp == stamp) {
            return hit.result;
        }
        File source = new File(path);
        GeneralCommandLine cmd = firstAvailableCommand(source);
        CompileResult result = cmd != null ? runCompile(cmd, source) : CompileResult.unavailable();
        lastResults.put(path, result);
        if (result.compilerAvailable()) {
            cache.put(path, new Cached(stamp, result));
        }
        return result;
    }

    /** Forces a fresh compile of {@code file}, discarding any memoised result for it first. Never throws. */
    @NotNull
    public CompileResult recompile(@NotNull VirtualFile file) {
        cache.remove(file.getPath());
        return compile(file);
    }

    /**
     * The most recent compile result for {@code file} without triggering a new compile, or null if
     * {@code file} has never been passed to {@link #compile}/{@link #recompile}. Used by the
     * status-bar widget so it never has to spawn a compile itself just to render.
     */
    @Nullable
    public CompileResult getLastResult(@NotNull VirtualFile file) {
        return lastResults.get(file.getPath());
    }

    @Nullable
    private GeneralCommandLine firstAvailableCommand(@NotNull File source) {
        for (MqlCompilerLauncher launcher : launchers) {
            GeneralCommandLine cmd = launcher.commandFor(source);
            if (cmd != null) {
                return cmd;
            }
        }
        return null;
    }

    @NotNull
    private CompileResult runCompile(@NotNull GeneralCommandLine cmd, @NotNull File source) {
        try {
            // Delete any log left by a PREVIOUS compile before launching. MetaEditor writes the log
            // during a real compile, so after the run a present log is necessarily fresh; if the
            // compiler didn't actually (re)compile — e.g. metaeditor64.exe handed the request to an
            // already-open GUI instance and exited immediately — the log stays absent and we fall
            // back to stdout instead of silently reporting a STALE previous result (or a false
            // "0 errors" clean bill).
            File staleLog = logFileFor(source);
            try {
                Files.deleteIfExists(staleLog.toPath());
            } catch (Exception e) {
                LOG.warn("Could not clear stale compile log " + staleLog, e);
            }
            CapturingProcessHandler handler = new CapturingProcessHandler(cmd);
            // Honour daemon cancellation: with an indicator the Wine/MetaEditor process is
            // destroyed when the annotation pass is cancelled, instead of blocking the thread and
            // leaking a ~60s process. Falls back to a plain timed run when no indicator is present.
            ProgressIndicator indicator = ProgressManager.getInstance().getProgressIndicator();
            ProcessOutput out = indicator != null
                    ? handler.runProcessWithProgressIndicator(indicator, (int) COMPILE_TIMEOUT_MS, true)
                    : handler.runProcess((int) COMPILE_TIMEOUT_MS);
            String log = readLog(source);
            if (log == null) {
                // fall back to stdout/stderr if the .log wasn't produced
                log = out.getStdout() + "\n" + out.getStderr();
            }
            List<CompilerDiagnostic> diags = CompilerOutputParser.parse(log);
            int[] sum = CompilerOutputParser.parseSummary(log);
            int errors = sum != null ? sum[0] : (int) diags.stream()
                    .filter(d -> d.severity() == CompilerDiagnostic.Severity.ERROR).count();
            int warnings = sum != null ? sum[1] : (int) diags.stream()
                    .filter(d -> d.severity() == CompilerDiagnostic.Severity.WARNING).count();
            return new CompileResult(diags, true, errors, warnings);
        } catch (ProcessCanceledException pce) {
            throw pce; // never swallow cancellation — let the daemon abort cleanly
        } catch (Exception e) {
            LOG.warn("compile failed for " + source, e);
            return CompileResult.unavailable();
        }
    }

    /** The {@code <basename>.log} MetaEditor writes next to {@code source} (whether or not it exists). */
    @NotNull
    static File logFileFor(@NotNull File source) {
        String name = source.getName();
        int dot = name.lastIndexOf('.');
        String logName = (dot >= 0 ? name.substring(0, dot) : name) + ".log";
        return new File(source.getParentFile(), logName);
    }

    /** Reads the {@code <basename>.log} MetaEditor writes next to the source, or null if absent. */
    @Nullable
    private static String readLog(@NotNull File source) {
        File log = logFileFor(source);
        if (!log.isFile()) {
            return null;
        }
        try {
            return decodeMqlLog(Files.readAllBytes(log.toPath()));
        } catch (Exception e) {
            LOG.warn("Failed to read compile log " + log, e);
            return null;
        }
    }

    /**
     * Decodes a MetaEditor compile log. MetaEditor writes UTF-16 <b>little-endian</b>, sometimes with
     * a BOM and sometimes without. {@link StandardCharsets#UTF_16} would silently default a BOM-less
     * log to big-endian and produce byte-swapped mojibake — which the diagnostic regexes then match
     * nothing in, reporting a false "0 errors". So: honour an explicit BOM if present, otherwise
     * assume little-endian (MetaEditor's actual output) rather than the JVM default.
     */
    @NotNull
    public static String decodeMqlLog(@NotNull byte[] bytes) {
        if (bytes.length >= 2) {
            int b0 = bytes[0] & 0xFF;
            int b1 = bytes[1] & 0xFF;
            if (b0 == 0xFF && b1 == 0xFE) {
                return new String(bytes, 2, bytes.length - 2, StandardCharsets.UTF_16LE);
            }
            if (b0 == 0xFE && b1 == 0xFF) {
                return new String(bytes, 2, bytes.length - 2, StandardCharsets.UTF_16BE);
            }
        }
        return new String(bytes, StandardCharsets.UTF_16LE);
    }
}
