/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.intellij.execution.process.CapturingProcessHandler;
import com.intellij.execution.process.ProcessOutput;
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
            ProcessOutput out = new CapturingProcessHandler(cmd).runProcess((int) COMPILE_TIMEOUT_MS);
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
        } catch (Exception e) {
            LOG.warn("compile failed for " + source, e);
            return CompileResult.unavailable();
        }
    }

    /** Reads the UTF-16 {@code <basename>.log} MetaEditor writes next to the source, or null if absent. */
    @Nullable
    private static String readLog(@NotNull File source) {
        String name = source.getName();
        int dot = name.lastIndexOf('.');
        String logName = (dot >= 0 ? name.substring(0, dot) : name) + ".log";
        File log = new File(source.getParentFile(), logName);
        if (!log.isFile()) {
            return null;
        }
        try {
            byte[] bytes = Files.readAllBytes(log.toPath());
            // MetaEditor logs are UTF-16 (LE with BOM); StandardCharsets.UTF_16 honours the BOM.
            return new String(bytes, StandardCharsets.UTF_16);
        } catch (Exception e) {
            LOG.warn("Failed to read compile log " + log, e);
            return null;
        }
    }
}
