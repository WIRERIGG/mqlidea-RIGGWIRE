/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.Executor;
import com.intellij.execution.configurations.ConfigurationFactory;
import com.intellij.execution.configurations.RunConfiguration;
import com.intellij.execution.configurations.RunConfigurationBase;
import com.intellij.execution.configurations.RunProfileState;
import com.intellij.execution.configurations.RuntimeConfigurationException;
import com.intellij.execution.runners.ExecutionEnvironment;
import com.intellij.openapi.options.SettingsEditor;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.InvalidDataException;
import com.intellij.openapi.util.WriteExternalException;
import com.limemojito.oss.mql.compiler.Mt5CliLauncher;
import com.limemojito.oss.mql.runconfig.ui.MqlBacktestEditor;
import org.jdom.Element;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.util.Objects;

import static com.limemojito.oss.mql.runconfig.MQL4RunCompilerConfiguration.readValueChild;
import static com.limemojito.oss.mql.runconfig.MQL4RunCompilerConfiguration.writeValueChild;

/** A Strategy Tester run through the {@code mt5 backtest} bridge. Empty settings keep the bridge's defaults. */
public class MqlBacktestConfiguration extends RunConfigurationBase<RunProfileState> {

    /** The EA's {@code .ex5} under {@code MQL5\Experts}; empty = the bridge's EA. */
    @NotNull
    public String expert = "";
    @NotNull
    public String symbol = "";
    @NotNull
    public String from = "2025.01.01";
    @NotNull
    public String to = "2025.06.30";
    /** MetaTrader's tick model; 1 (1 minute OHLC) by default, since open-prices-only fills can mislead. */
    public int model = 1;
    /** Chart timeframe; empty = the bridge's (M5). */
    @NotNull
    public String period = "";
    @NotNull
    public String deposit = "";
    /** A {@code .set} or {@code Name=Value} file of EA inputs, or empty. */
    @NotNull
    public String inputsFile = "";
    @NotNull
    public String timeout = "";

    protected MqlBacktestConfiguration(@NotNull Project project, @NotNull ConfigurationFactory factory, String name) {
        super(project, factory, name);
    }

    @NotNull
    @Override
    public SettingsEditor<? extends RunConfiguration> getConfigurationEditor() {
        return new MqlBacktestEditor(getProject());
    }

    @Override
    public void checkConfiguration() throws RuntimeConfigurationException {
        if (Mt5CliLauncher.findMt5() == null) {
            throw new RuntimeConfigurationException("The mt5 bridge isn't installed at ~/.local/bin/mt5");
        }
        String problem = MqlBacktestCommand.problem(symbol, from, to, model, period, deposit, timeout, expert);
        if (problem != null) {
            throw new RuntimeConfigurationException(problem);
        }
        if (!inputsFile.isEmpty() && !new File(inputsFile).isFile()) {
            throw new RuntimeConfigurationException("Inputs file not found: " + inputsFile);
        }
    }

    @Nullable
    @Override
    public RunProfileState getState(@NotNull Executor executor, @NotNull ExecutionEnvironment environment) {
        return new MqlBacktestState(this, environment);
    }

    @Override
    public void writeExternal(@NotNull Element element) throws WriteExternalException {
        super.writeExternal(element);
        writeValueChild(element, "expert", expert);
        writeValueChild(element, "symbol", symbol);
        writeValueChild(element, "from", from);
        writeValueChild(element, "to", to);
        writeValueChild(element, "model", Integer.toString(model));
        writeValueChild(element, "period", period);
        writeValueChild(element, "deposit", deposit);
        writeValueChild(element, "inputs", inputsFile);
        writeValueChild(element, "timeout", timeout);
    }

    @Override
    public void readExternal(@NotNull Element element) throws InvalidDataException {
        super.readExternal(element);
        expert = Objects.toString(readValueChild(element, "expert"), "");
        symbol = Objects.toString(readValueChild(element, "symbol"), "");
        from = Objects.toString(readValueChild(element, "from"), from);
        to = Objects.toString(readValueChild(element, "to"), to);
        try {
            model = Integer.parseInt(Objects.toString(readValueChild(element, "model"), "1"));
        } catch (NumberFormatException e) {
            model = 1;
        }
        period = Objects.toString(readValueChild(element, "period"), "");
        deposit = Objects.toString(readValueChild(element, "deposit"), "");
        inputsFile = Objects.toString(readValueChild(element, "inputs"), "");
        timeout = Objects.toString(readValueChild(element, "timeout"), "");
    }
}
