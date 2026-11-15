/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.junit.jupiter.api.Test;

import java.util.List;

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

    /** Lines as macOS ps showed them during a real gate run (Java's process API saw only "wine64" for these). */
    @Test
    void aRealWineBacktestIsBusy() {
        String home = "/Users/x/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5";
        StrategyTester.State s = StrategyTester.scan(List.of(
                "/bin/zsh -c eval '~/riggwire-data/gate_runs/run_ebc2.sh'",
                home + "/terminal64.exe /portable /config:Z:\\tmp\\mt5_backtest.ini",
                "C:\\Program Files\\MetaTrader 5\\metatester64.exe /run /address:0.0.0.0:2002 /password:MetaTester"));
        assertThat(s.known()).isTrue();
        assertThat(s.terminal()).isTrue();
        assertThat(s.tester()).isTrue();
    }

    @Test
    void theBridgeStartingABacktestIsBusy() {
        assertThat(StrategyTester.scan(List.of("bash /Users/x/.local/bin/mt5 backtest --symbol EURUSDR --model 1")).driver()).isTrue();
        assertThat(StrategyTester.scan(List.of("mt5 backtest")).driver()).isTrue();
        assertThat(StrategyTester.scan(List.of("bash /Users/x/.local/bin/mt5 compile EA.mq5", "grep mt5 backtest-notes")).driver()).isFalse();
    }

    @Test
    void anIdleTableIsIdleAndAnUnreadableOneIsBusy() {
        StrategyTester.State idle = StrategyTester.scan(List.of("/bin/zsh", "/Applications/CLion.app/Contents/MacOS/clion"));
        assertThat(idle.terminal() || idle.tester() || idle.driver()).isFalse();
        assertThat(StrategyTester.State.UNKNOWN.known()).isFalse();
        assertThat(StrategyTester.State.UNKNOWN.terminal()).isTrue();
    }
}
