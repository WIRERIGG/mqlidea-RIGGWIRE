/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;

/**
 * The {@code mt5 backtest} invocation for a backtest configuration, and its validation. Always
 * {@code --no-kill}: the plugin never stops a running MetaTrader; it refuses to start instead.
 */
final class MqlBacktestCommand {

    /** MetaTrader's tick models are 0 (every tick) to 4 (every tick based on real ticks). */
    private static final int MODEL_COUNT = 5;

    private static final Pattern DATE = Pattern.compile("\\d{4}\\.\\d{2}\\.\\d{2}");
    private static final Pattern SYMBOL = Pattern.compile("[A-Za-z0-9._#-]+");
    private static final Pattern PERIOD = Pattern.compile("M1|M2|M3|M4|M5|M6|M10|M12|M15|M20|M30|H1|H2|H3|H4|H6|H8|H12|D1|W1|MN1");

    private MqlBacktestCommand() {
    }

    /** The first problem with these settings, or null when they are runnable. */
    @Nullable
    static String problem(@NotNull String symbol, @NotNull String from, @NotNull String to, int model,
                          @NotNull String period, @NotNull String deposit, @NotNull String timeout, @NotNull String expert) {
        if (!SYMBOL.matcher(symbol).matches()) {
            return symbol.isEmpty() ? "No symbol" : "Not a symbol name: " + symbol;
        }
        if (!DATE.matcher(from).matches() || !DATE.matcher(to).matches()) {
            return "Dates are YYYY.MM.DD";
        }
        if (from.compareTo(to) > 0) {
            return "The start date is after the end date";
        }
        if (model < 0 || model >= MODEL_COUNT) {
            return "Unknown tick model " + model;
        }
        if (!period.isEmpty() && !PERIOD.matcher(period).matches()) {
            return "Not a timeframe: " + period;
        }
        if (!deposit.isEmpty() && !deposit.matches("\\d+")) {
            return "The deposit is a whole number";
        }
        if (!timeout.isEmpty() && !timeout.matches("\\d+")) {
            return "The timeout is a number of seconds";
        }
        if (!expert.isEmpty() && !expert.toLowerCase().endsWith(".ex5")) {
            return "The EA is the .ex5 path under MQL5\\Experts, e.g. RIGGWIRE\\RIGGWIRE_FINAL.ex5";
        }
        return null;
    }

    @NotNull
    static List<String> arguments(@NotNull String mt5, @NotNull String symbol, @NotNull String from, @NotNull String to,
                                  int model, @NotNull String timeout) {
        List<String> args = new ArrayList<>(List.of(mt5, "backtest", "--symbol", symbol, "--from", from, "--to", to,
                "--model", Integer.toString(model), "--no-kill"));
        if (!timeout.isEmpty()) {
            args.add("--timeout");
            args.add(timeout);
        }
        return args;
    }

    /** The bridge's environment overrides; empty settings keep the bridge's own defaults. */
    @NotNull
    static Map<String, String> environment(@NotNull String expert, @NotNull String period, @NotNull String deposit,
                                           @Nullable String inputsFile) {
        Map<String, String> env = new LinkedHashMap<>();
        if (!expert.isEmpty()) {
            env.put("MT5_EA_NAME", expert.replace('/', '\\'));
        }
        if (!period.isEmpty()) {
            env.put("MT5_PERIOD", period);
        }
        if (!deposit.isEmpty()) {
            env.put("MT5_TESTER_DEPOSIT", deposit);
        }
        if (inputsFile != null) {
            env.put("MT5_TESTER_INPUTS", inputsFile);
        }
        return env;
    }
}
