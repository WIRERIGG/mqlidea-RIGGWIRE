/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.configurations.ConfigurationFactory;
import com.intellij.execution.configurations.ConfigurationTypeBase;
import com.intellij.execution.configurations.RunConfiguration;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.MQL4Icons;
import org.jetbrains.annotations.NotNull;

public class MqlBacktestConfigurationType extends ConfigurationTypeBase {

    private static final String ID = "MqlBacktestConfigurationTypeId";

    public MqlBacktestConfigurationType() {
        super(ID, "MQL5 Backtest", "Run an EA in the MetaTrader 5 Strategy Tester (mt5 backtest)", MQL4Icons.File);
        addFactory(new ConfigurationFactory(this) {
            @NotNull
            @Override
            public RunConfiguration createTemplateConfiguration(@NotNull Project project) {
                return new MqlBacktestConfiguration(project, this, "MQL5 Backtest");
            }

            @Override
            @NotNull
            public String getId() {
                return getName();
            }
        });
    }

    @NotNull
    public static MqlBacktestConfigurationType getInstance() {
        return CONFIGURATION_TYPE_EP.findExtensionOrFail(MqlBacktestConfigurationType.class);
    }
}
