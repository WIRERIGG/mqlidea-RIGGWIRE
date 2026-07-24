/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.limemojito.oss.mql.util.OSUtils;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.util.List;

/**
 * Linux (and other non-macOS, non-Windows) launcher: an explicit Wine binary plus an explicit
 * MetaEditor exe path, replacing the broken assumption in the old run configuration
 * ({@code MQL4CompilerCommandLineState:126}, {@code OSUtils.isWine() == !isWindowsOS()}) that a bare
 * {@code wine} exists on {@code PATH} &mdash; it doesn't on macOS (Wine lives inside
 * MetaTrader 5.app, reached via {@link Mt5CliLauncher} instead) and isn't guaranteed on Linux either.
 *
 * <p>This launcher only reports itself available when <b>both</b> a Wine binary and a MetaEditor
 * exe can actually be found; otherwise it is a no-op (per docs/REVAMP_PLAN.md's honesty principle:
 * an explicit "unavailable" beats a silently wrong guess). The Wine binary is looked up via the
 * {@code mql.wine.path} system property or {@code MQL_WINE_PATH} environment variable first (for
 * explicit configuration), then a handful of common install locations.</p>
 */
public final class WineLauncher implements MqlCompilerLauncher {

    private static final List<String> COMMON_WINE_PATHS = List.of(
            "/usr/bin/wine64", "/usr/bin/wine",
            "/usr/local/bin/wine64", "/usr/local/bin/wine",
            "/opt/homebrew/bin/wine64", "/opt/homebrew/bin/wine");

    @Override
    @NotNull
    public String name() {
        return "Wine";
    }

    @Override
    @Nullable
    public GeneralCommandLine commandFor(@NotNull File source) {
        if (OSUtils.isWindowsOS()) {
            return null; // MetaEditorLauncher covers Windows directly; no need to shell through Wine
        }
        String wine = findWineBinary();
        if (wine == null) {
            return null;
        }
        File exe = MetaEditorLauncher.findMetaEditorExe();
        if (exe == null) {
            return null;
        }
        GeneralCommandLine cmd = new GeneralCommandLine(wine, exe.getAbsolutePath(),
                "/compile:" + source.getAbsolutePath(), "/log")
                .withParentEnvironmentType(GeneralCommandLine.ParentEnvironmentType.CONSOLE);
        cmd.getEnvironment().put("WINEDEBUG", "-all"); // silence Wine's own warnings/debug noise
        return cmd;
    }

    @Nullable
    private static String findWineBinary() {
        String configured = System.getProperty("mql.wine.path");
        if (configured == null) {
            configured = System.getenv("MQL_WINE_PATH");
        }
        if (configured != null && new File(configured).canExecute()) {
            return configured;
        }
        for (String candidate : COMMON_WINE_PATHS) {
            File f = new File(candidate);
            if (f.isFile() && f.canExecute()) {
                return candidate;
            }
        }
        return null;
    }
}
