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
 * {@code .exe} path is the command line). Cached for a few seconds: the annotator asks on every pass.
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
            if (runs(text, "metatester64")) {
                found[0] = true;
            }
            if (runs(text, "terminal64")) {
                found[1] = true;
            }
        });
        testerRunning = found[0];
        terminalRunning = found[1];
        checkedAt = now;
    }

    /**
     * True when {@code commandLine} runs {@code exe}: its {@code .exe} path, after a folder separator
     * (native, or Wine's {@code C:\\...\\terminal64.exe}). A shell or script that merely mentions the
     * name ({@code pgrep -f terminal64}) is not MetaTrader.
     */
    static boolean runs(@NotNull String commandLine, @NotNull String exe) {
        String line = commandLine.toLowerCase(Locale.ROOT);
        for (int at = line.indexOf(exe + ".exe"); at >= 0; at = line.indexOf(exe + ".exe", at + 1)) {
            if (at > 0 && (line.charAt(at - 1) == '\\' || line.charAt(at - 1) == '/')) {
                int end = at + exe.length() + 4;
                if (end == line.length() || Character.isWhitespace(line.charAt(end)) || line.charAt(end) == '"') {
                    return true;
                }
            }
        }
        return false;
    }

    @NotNull
    private static String describe(@NotNull ProcessHandle p) {
        ProcessHandle.Info info = p.info();
        Optional<String> line = info.commandLine();
        return line.orElseGet(() -> info.command().orElse("")).toLowerCase(Locale.ROOT);
    }
}
