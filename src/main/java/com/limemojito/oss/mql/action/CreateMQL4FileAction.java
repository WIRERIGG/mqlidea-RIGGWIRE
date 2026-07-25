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
 * The "New MQL4 File" action (Phase 2e, REVAMP_PLAN.md). Offers the bundled "MQL4 Expert"
 * internal file template (see {@code resources/fileTemplates/internal/}) instead of creating an
 * empty file.
 */
public class CreateMQL4FileAction extends CreateFileFromTemplateAction {

    public static final String EXPERT_TEMPLATE = "MQL4 Expert";

    public CreateMQL4FileAction() {
        super(() -> MQL4PluginResources.message("action.New-MQL-File.text"),
                () -> MQL4PluginResources.message("action.New-MQL-File.description"),
                MQL4Icons.File);
    }

    @Override
    protected void buildDialog(@NotNull Project project, @NotNull PsiDirectory directory,
                                @NotNull CreateFileFromTemplateDialog.Builder builder) {
        builder.setTitle(MQL4PluginResources.message("action.New-MQL-File.text"))
                .addKind("Expert", MQL4Icons.File, EXPERT_TEMPLATE);
    }

    @Override
    protected String getActionName(PsiDirectory directory, @NotNull String newName, String templateName) {
        return MQL4PluginResources.message("action.New-MQL-File.text") + " " + newName;
    }

    @Nullable
    @Override
    protected String getDefaultTemplateProperty() {
        return "MQL4FileTemplate";
    }
}
