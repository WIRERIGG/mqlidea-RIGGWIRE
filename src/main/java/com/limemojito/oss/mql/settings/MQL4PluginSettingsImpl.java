/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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
