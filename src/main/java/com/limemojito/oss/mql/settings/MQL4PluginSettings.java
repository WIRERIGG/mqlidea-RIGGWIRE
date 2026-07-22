/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.settings;

import com.intellij.openapi.application.ApplicationManager;

public interface MQL4PluginSettings {

    boolean isUseEnDocs();

    void setUseEnDocs(boolean v);

    boolean performErrorAnalysis();

    void setPerformErrorAnalysis(boolean v);

    int getHealingDelayMinutes();

    void setHealingDelayMinutes(int minutes);

    boolean isAutoHealEnabled();

    void setAutoHealEnabled(boolean v);

    String getGrokModel();

    void setGrokModel(String model);

    String getClaudeModel();

    void setClaudeModel(String model);

    static MQL4PluginSettings getInstance() {
        return ApplicationManager.getApplication().getComponent(MQL4PluginSettings.class);
    }
}
