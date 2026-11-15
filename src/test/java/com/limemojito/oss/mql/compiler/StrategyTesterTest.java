/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

/** Only MetaTrader itself counts; shells and scripts that mention it (seen live: a pgrep loop) don't. */
class StrategyTesterTest {

    @Test
    void theExecutableCounts() {
        assertThat(StrategyTester.runs("C:\\Program Files\\MetaTrader 5\\terminal64.exe /portable /config:Z:\\tmp\\mt5_backtest.ini", "terminal64")).isTrue();
        assertThat(StrategyTester.runs("C:\\Program Files\\MetaTrader 5\\Terminal64.EXE", "terminal64")).isTrue();
        assertThat(StrategyTester.runs("\"C:\\Program Files\\MetaTrader 5\\metatester64.exe\" /agent", "metatester64")).isTrue();
        assertThat(StrategyTester.runs("/opt/mt5/terminal64.exe", "terminal64")).isTrue();
    }

    @Test
    void mentionsDoNotCount() {
        assertThat(StrategyTester.runs("pgrep -fl terminal64|metatester", "terminal64")).isFalse();
        assertThat(StrategyTester.runs("python3 -c while not pgrep('terminal64'): sleep", "terminal64")).isFalse();
        assertThat(StrategyTester.runs("zsh -c pgrep -f terminal64.exe", "terminal64")).isFalse();
        assertThat(StrategyTester.runs("/bin/zsh /Users/x/.local/bin/mt5 backtest --symbol EURJPY --no-kill", "terminal64")).isFalse();
        assertThat(StrategyTester.runs("C:\\MT5\\terminal64.exe.bak", "terminal64")).isFalse();
    }
}
