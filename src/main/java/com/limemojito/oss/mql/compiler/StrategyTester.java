/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.jetbrains.annotations.NotNull;

import java.util.Locale;
import java.util.Optional;

/**
 * Whether MetaTrader is running, read from the process table (native or under Wine, where the
 * {@code .exe} path is in the arguments). Cached for a few seconds: the annotator asks on every pass.
 */
public final class StrategyTester {

    private static final long TTL_NANOS = 5_000_000_000L;
    private static volatile long checkedAt;
    private static volatile boolean testerRunning;
    private static volatile boolean terminalRunning;

    private StrategyTester() {
    }

    /** A {@code metatester64} agent is running: a backtest or optimisation is in progress. */
    public static boolean isRunning() {
        refresh();
        return testerRunning;
    }

    /** A {@code terminal64} (MetaTrader 5 itself) is running. */
    public static boolean isTerminalRunning() {
        refresh();
        return terminalRunning;
    }

    /** Reads the process table now, ignoring the cache: for decisions like starting a backtest. */
    public static void refreshNow() {
        checkedAt = 0;
        refresh();
    }

    private static void refresh() {
        long now = System.nanoTime();
        if (checkedAt != 0 && now - checkedAt < TTL_NANOS) {
            return;
        }
        boolean[] found = new boolean[2];
        ProcessHandle.allProcesses().forEach(p -> {
            String text = describe(p);
            if (text.contains("metatester64")) {
                found[0] = true;
            }
            if (text.contains("terminal64")) {
                found[1] = true;
            }
        });
        testerRunning = found[0];
        terminalRunning = found[1];
        checkedAt = now;
    }

    @NotNull
    private static String describe(@NotNull ProcessHandle p) {
        ProcessHandle.Info info = p.info();
        Optional<String> line = info.commandLine();
        return line.orElseGet(() -> info.command().orElse("")).toLowerCase(Locale.ROOT);
    }
}
