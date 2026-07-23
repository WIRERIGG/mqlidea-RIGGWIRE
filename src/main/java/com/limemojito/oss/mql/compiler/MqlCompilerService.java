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
 * Phase 1 ships the macOS launcher — the {@code mt5} Wine wrapper (see docs/REVAMP_PLAN.md); the
 * Windows {@code metaeditor64.exe} and explicit-{@code wine} strategies are added in a later slice.
 *
 * <p>Results are memoised per file by modification stamp, so re-analysing unchanged content never
 * re-spawns the compiler (the flagship must not hammer Wine on every daemon pass).</p>
 */
@Service(Service.Level.PROJECT)
public final class MqlCompilerService {

    private static final Logger LOG = Logger.getInstance(MqlCompilerService.class);
    private static final long COMPILE_TIMEOUT_MS = 60_000;

    /** path -> (modificationStamp, result) so unchanged content is never recompiled. */
    private final Map<String, Cached> cache = new ConcurrentHashMap<>();

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
        String mt5 = findMt5();
        if (mt5 == null) {
            return CompileResult.unavailable();
        }
        String path = file.getPath();
        long stamp = file.getModificationStamp();
        Cached hit = cache.get(path);
        if (hit != null && hit.stamp == stamp) {
            return hit.result;
        }
        CompileResult result = runCompile(mt5, new File(path));
        if (result.compilerAvailable()) {
            cache.put(path, new Cached(stamp, result));
        }
        return result;
    }

    @NotNull
    private CompileResult runCompile(@NotNull String mt5, @NotNull File source) {
        try {
            GeneralCommandLine cmd = new GeneralCommandLine(mt5, "compile", source.getAbsolutePath())
                    .withParentEnvironmentType(GeneralCommandLine.ParentEnvironmentType.CONSOLE);
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
            LOG.warn("mt5 compile failed for " + source, e);
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

    /** Locates the {@code mt5} wrapper: {@code ~/.local/bin/mt5} first, else assume it's on PATH. */
    @Nullable
    private static String findMt5() {
        File local = new File(System.getProperty("user.home", ""), ".local/bin/mt5");
        if (local.isFile() && local.canExecute()) {
            return local.getAbsolutePath();
        }
        return null;
    }
}
