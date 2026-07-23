/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.settings;

import com.intellij.openapi.components.PersistentStateComponent;
import com.intellij.openapi.components.State;
import com.intellij.openapi.components.Storage;
import com.intellij.util.xmlb.XmlSerializerUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

@State(name = "MQL4.PluginSettings", storages = {@Storage("mql4-plugin.xml")})
public class MQL4PluginSettingsImpl implements MQL4PluginSettings, PersistentStateComponent<MQL4PluginSettingsImpl> {

    public boolean enDocs = true;
    public boolean errorAnalysis = true;
    public int healingDelayMinutes = 5;
    public boolean autoHealEnabled = false;
    public String grokModel = "grok-2";
    public String claudeModel = "claude-sonnet-4-5-20250929";
    public boolean useClaudeCli = true;
    public String claudeCliPath = "";

    @Override
    public boolean isUseEnDocs() {
        return enDocs;
    }

    @Override
    public void setUseEnDocs(boolean v) {
        enDocs = v;
    }

    @Override
    public boolean performErrorAnalysis() {
        return errorAnalysis;
    }

    @Override
    public void setPerformErrorAnalysis(boolean v) {
        errorAnalysis = v;
    }

    @Override
    public int getHealingDelayMinutes() {
        return healingDelayMinutes;
    }

    @Override
    public void setHealingDelayMinutes(int minutes) {
        healingDelayMinutes = minutes;
    }

    @Override
    public boolean isAutoHealEnabled() {
        return autoHealEnabled;
    }

    @Override
    public void setAutoHealEnabled(boolean v) {
        autoHealEnabled = v;
    }

    @Override
    public String getGrokModel() {
        return grokModel;
    }

    @Override
    public void setGrokModel(String model) {
        grokModel = model;
    }

    @Override
    public String getClaudeModel() {
        return claudeModel;
    }

    @Override
    public void setClaudeModel(String model) {
        claudeModel = model;
    }

    @Override
    public boolean isUseClaudeCli() {
        return useClaudeCli;
    }

    @Override
    public void setUseClaudeCli(boolean v) {
        useClaudeCli = v;
    }

    @Override
    public String getClaudeCliPath() {
        return claudeCliPath;
    }

    @Override
    public void setClaudeCliPath(String p) {
        claudeCliPath = p != null ? p : "";
    }

    @Nullable
    @Override
    public MQL4PluginSettingsImpl getState() {
        return this;
    }

    @Override
    public void loadState(@NotNull MQL4PluginSettingsImpl state) {
        XmlSerializerUtil.copyBean(state, this);
    }
}
