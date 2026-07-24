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
 * Strategy for invoking the real MetaEditor compiler on one platform. {@link MqlCompilerService}
 * tries each configured launcher in order and uses the command from the first one that reports
 * itself available, so the same service works unmodified whether the user is on macOS (Wine
 * bundled inside MetaTrader 5.app, driven via the {@code mt5} CLI wrapper), Windows (native
 * {@code metaeditor64.exe}), or Linux (explicit Wine binary + exe). See docs/REVAMP_PLAN.md Phase 1
 * for why this replaced the single hardcoded macOS-only path (and the broken
 * {@code OSUtils.isWine() == !isWindowsOS()} assumption in the old run configuration).
 */
public interface MqlCompilerLauncher {

    /** Short name for logging/diagnostics, e.g. {@code "mt5 CLI"}, {@code "MetaEditor"}, {@code "Wine"}. */
    @NotNull
    String name();

    /**
     * Builds the command that compiles {@code source}, or {@code null} if this launcher isn't
     * available/configured on this machine right now. Must be cheap and side-effect-free (at most
     * a filesystem probe) &mdash; it never spawns a process itself; {@link MqlCompilerService} does
     * that with whichever command is returned.
     */
    @Nullable
    GeneralCommandLine commandFor(@NotNull File source);
}
