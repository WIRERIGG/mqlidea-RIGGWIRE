/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.action;

import com.intellij.ide.actions.CreateFileFromTemplateAction;
import com.intellij.ide.actions.CreateFileFromTemplateDialog;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDirectory;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.MQL4PluginResources;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * The "New MQL5 File" action (Phase 2e, REVAMP_PLAN.md). Offers the bundled "MQL5 Expert
 * Advisor" / "MQL5 Indicator" / "MQL5 Script" internal file templates (see {@code
 * resources/fileTemplates/internal/}) instead of creating an empty file.
 */
public class CreateMQL5FileAction extends CreateFileFromTemplateAction {

    public static final String EXPERT_ADVISOR_TEMPLATE = "MQL5 Expert Advisor";
    public static final String INDICATOR_TEMPLATE = "MQL5 Indicator";
    public static final String SCRIPT_TEMPLATE = "MQL5 Script";

    public CreateMQL5FileAction() {
        super(() -> MQL4PluginResources.message("action.New-MQL5-File.text"),
                () -> MQL4PluginResources.message("action.New-MQL5-File.description"),
                MQL4Icons.File);
    }

    @Override
    protected void buildDialog(@NotNull Project project, @NotNull PsiDirectory directory,
                                @NotNull CreateFileFromTemplateDialog.Builder builder) {
        builder.setTitle(MQL4PluginResources.message("action.New-MQL5-File.text"))
                .addKind("Expert Advisor", MQL4Icons.File, EXPERT_ADVISOR_TEMPLATE)
                .addKind("Indicator", MQL4Icons.File, INDICATOR_TEMPLATE)
                .addKind("Script", MQL4Icons.File, SCRIPT_TEMPLATE);
    }

    @Override
    protected String getActionName(PsiDirectory directory, @NotNull String newName, String templateName) {
        return MQL4PluginResources.message("action.New-MQL5-File.text") + " " + newName;
    }

    @Nullable
    @Override
    protected String getDefaultTemplateProperty() {
        return "MQL5FileTemplate";
    }
}
