/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;

/**
 * macOS launcher: runs the user's {@code mt5} Wine wrapper (see {@code ~/.claude/skills/mt5-wine-bridge}),
 * which drives MetaTrader 5's bundled Wine prefix. This is the launcher that ships and is exercised
 * on this development machine; it is unavailable (and simply skipped) wherever the wrapper isn't
 * installed at {@code ~/.local/bin/mt5}.
 */
public final class Mt5CliLauncher implements MqlCompilerLauncher {

    @Override
    @NotNull
    public String name() {
        return "mt5 CLI";
    }

    @Override
    @Nullable
    public GeneralCommandLine commandFor(@NotNull File source) {
        String mt5 = findMt5();
        if (mt5 == null) {
            return null;
        }
        return new GeneralCommandLine(mt5, "compile", source.getAbsolutePath())
                .withParentEnvironmentType(GeneralCommandLine.ParentEnvironmentType.CONSOLE);
    }

    /** Locates the {@code mt5} wrapper at {@code ~/.local/bin/mt5}, or null if it isn't installed there. */
    @Nullable
    private static String findMt5() {
        File local = new File(System.getProperty("user.home", ""), ".local/bin/mt5");
        if (local.isFile() && local.canExecute()) {
            return local.getAbsolutePath();
        }
        return null;
    }
}
