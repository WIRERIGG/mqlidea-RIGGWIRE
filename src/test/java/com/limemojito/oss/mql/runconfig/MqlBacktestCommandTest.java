/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;

import static org.assertj.core.api.Assertions.assertThat;

class MqlBacktestCommandTest {

    @Test
    void alwaysPassesNoKill() {
        assertThat(MqlBacktestCommand.arguments("mt5", "EURJPY", "2024.01.01", "2024.06.30", 1, ""))
                .containsExactly("mt5", "backtest", "--symbol", "EURJPY", "--from", "2024.01.01", "--to", "2024.06.30",
                        "--model", "1", "--no-kill");
        assertThat(MqlBacktestCommand.arguments("mt5", "EURJPY", "2024.01.01", "2024.06.30", 4, "900"))
                .endsWith("--no-kill", "--timeout", "900");
    }

    @Test
    void emptySettingsKeepTheBridgeDefaults() {
        assertThat(MqlBacktestCommand.environment("", "", "", null)).isEmpty();
        assertThat(MqlBacktestCommand.environment("RIGGWIRE_TC_CHECK/RIGGWIRE_FINAL.ex5", "H1", "50000", "/tmp/in.txt"))
                .isEqualTo(Map.of("MT5_EA_NAME", "RIGGWIRE_TC_CHECK\\RIGGWIRE_FINAL.ex5", "MT5_PERIOD", "H1",
                        "MT5_TESTER_DEPOSIT", "50000", "MT5_TESTER_INPUTS", "/tmp/in.txt"));
    }

    @Test
    void validation() {
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024.01.01", "2024.06.30", 1, "", "", "", "")).isNull();
        assertThat(MqlBacktestCommand.problem("", "2024.01.01", "2024.06.30", 1, "", "", "", "")).isEqualTo("No symbol");
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024-01-01", "2024.06.30", 1, "", "", "", "")).contains("YYYY.MM.DD");
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024.07.01", "2024.06.30", 1, "", "", "", "")).contains("after");
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024.01.01", "2024.06.30", 5, "", "", "", "")).contains("model");
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024.01.01", "2024.06.30", 1, "M7", "", "", "")).contains("timeframe");
        assertThat(MqlBacktestCommand.problem("EURJPY", "2024.01.01", "2024.06.30", 1, "", "", "", "EA.mq5")).contains(".ex5");
        assertThat(MqlBacktestCommand.problem("EURJPY; rm", "2024.01.01", "2024.06.30", 1, "", "", "", "")).contains("Not a symbol");
    }

    @Test
    void readsTheReportLineTheBridgePrints() {
        String out = "[OK] Backtest complete\n  Report: /Users/x/MetaTrader 5/ex_pbr_2023H1.htm\n";
        Matcher m = MqlBacktestState.REPORT.matcher(out);
        assertThat(m.find()).isTrue();
        assertThat(m.group(1)).isEqualTo("/Users/x/MetaTrader 5/ex_pbr_2023H1.htm");
        assertThat(MqlBacktestState.exitMeaning(1)).contains("without a report");
        assertThat(MqlBacktestState.exitMeaning(3)).isEqualTo("timed out");
        assertThat(MqlBacktestState.exitMeaning(5)).contains("already running");
        assertThat(MqlBacktestState.exitMeaning(6)).contains("another backtest");
        assertThat(List.of(0, 1, 2, 3, 4, 5, 6).stream().map(MqlBacktestState::exitMeaning)).doesNotHaveDuplicates();
    }
}
