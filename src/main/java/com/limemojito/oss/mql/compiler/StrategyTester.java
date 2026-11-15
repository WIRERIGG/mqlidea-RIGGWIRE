/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.openapi.util.SystemInfo;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.concurrent.TimeUnit;

/**
 * Whether MetaTrader is running, read from the process table. Under Wine (macOS, Linux) Java's
 * process API sees only {@code wine64} with no arguments, so the table comes from {@code ps}, which
 * shows the {@code .exe} path Wine runs. When the table can't be read, everything counts as running:
 * a backtest is refused rather than started beside one we can't see. Cached for a few seconds: the
 * annotator asks on every pass.
 */
public final class StrategyTester {

    /** What the process table says. */
    record State(boolean known, boolean tester, boolean terminal, boolean driver) {
        static final State UNKNOWN = new State(false, true, true, true);
    }

    private static final long TTL_NANOS = 5_000_000_000L;
    private static volatile long checkedAt;
    private static volatile State state = State.UNKNOWN;

    private StrategyTester() {
    }

    /** A {@code metatester64} agent is running: a backtest or optimisation is in progress. */
    public static boolean isRunning() {
        refresh();
        return state.tester;
    }

    /**
     * MetaTrader 5 is busy: {@code terminal64} or a tester agent runs, or an {@code mt5 backtest}
     * driver is starting one. Also true when the process table can't be read.
     */
    public static boolean isTerminalBusy() {
        refresh();
        return state.terminal || state.tester || state.driver;
    }

    /** False when the process table couldn't be read (and every question answers "running"). */
    public static boolean isKnown() {
        refresh();
        return state.known;
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
        List<String> table = SystemInfo.isWindows ? nativeTable() : psTable();
        state = table == null ? State.UNKNOWN : scan(table);
        checkedAt = now;
    }

    @NotNull
    static State scan(@NotNull List<String> commandLines) {
        boolean tester = false;
        boolean terminal = false;
        boolean driver = false;
        for (String line : commandLines) {
            tester |= runs(line, "metatester64");
            terminal |= runs(line, "terminal64");
            driver |= drivesBacktest(line);
        }
        return new State(true, tester, terminal, driver);
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

    /**
     * True when {@code commandLine} is the {@code mt5} bridge running {@code backtest}: it holds the
     * terminal for a few seconds before {@code terminal64} appears.
     */
    static boolean drivesBacktest(@NotNull String commandLine) {
        String[] words = commandLine.trim().split("\\s+");
        for (int i = 0; i + 1 < words.length; i++) {
            String w = words[i];
            if ((w.equals("mt5") || w.endsWith("/mt5")) && words[i + 1].equals("backtest")) {
                return true;
            }
        }
        return false;
    }

    /** Windows runs MetaTrader natively: the process API shows its path. */
    @NotNull
    private static List<String> nativeTable() {
        List<String> lines = new ArrayList<>();
        ProcessHandle.allProcesses().forEach(p -> {
            ProcessHandle.Info info = p.info();
            lines.add(info.commandLine().orElseGet(() -> info.command().orElse("")));
        });
        return lines;
    }

    /** Every process's command line from {@code ps}, or null when it can't be read. */
    @Nullable
    private static List<String> psTable() {
        try {
            Process ps = new ProcessBuilder("/bin/ps", "-axww", "-o", "command=").redirectErrorStream(true).start();
            List<String> lines = new ArrayList<>();
            try (BufferedReader in = new BufferedReader(new InputStreamReader(ps.getInputStream(), StandardCharsets.UTF_8))) {
                for (String line = in.readLine(); line != null; line = in.readLine()) {
                    lines.add(line);
                }
            }
            if (!ps.waitFor(5, TimeUnit.SECONDS)) {
                ps.destroyForcibly();
                return null;
            }
            return ps.exitValue() == 0 && !lines.isEmpty() ? lines : null;
        } catch (IOException e) {
            return null;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        }
    }
}
