
/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.actions.ConfigurationContext;
import com.intellij.execution.actions.RunConfigurationProducer;
import com.intellij.openapi.util.Ref;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;

public class MQL4RunCompilerConfigurationProducer extends RunConfigurationProducer<MQL4RunCompilerConfiguration> {

    protected MQL4RunCompilerConfigurationProducer() {
        super(MQL4RunCompilerConfigurationType.getInstance());
    }

    @Override
    protected boolean setupConfigurationFromContext(@NotNull MQL4RunCompilerConfiguration configuration, @NotNull ConfigurationContext context, @NotNull Ref<PsiElement> sourceElement) {
        return false;
    }

    @Override
    public boolean isConfigurationFromContext(@NotNull MQL4RunCompilerConfiguration configuration, @NotNull ConfigurationContext context) {
        return false;
    }
}
