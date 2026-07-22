/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ui;

import com.intellij.codeInsight.daemon.LineMarkerInfo;
import com.intellij.codeInsight.daemon.LineMarkerProvider;
import com.intellij.openapi.editor.markup.GutterIconRenderer;
import com.limemojito.oss.mql.MQL4Icons;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.limemojito.oss.mql.healing.HealingService;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public class HealingLineMarkerProvider implements LineMarkerProvider {

    @Nullable
    @Override
    public LineMarkerInfo<?> getLineMarkerInfo(@NotNull PsiElement element) {
        // Only mark the first leaf element of a file to check for healing tasks
        PsiFile file = element.getContainingFile();
        if (file == null) return null;

        // Only process the first element of the file
        if (element != file.getFirstChild()) return null;

        VirtualFile vf = file.getVirtualFile();
        if (vf == null) return null;

        Project project = element.getProject();
        // Read the in-memory cache — never query SQLite from line marker computation
        int readyCount = HealingService.getInstance(project).getReadyFixCountForFile(vf.getUrl());

        if (readyCount == 0) return null;

        return new LineMarkerInfo<>(
                element,
                element.getTextRange(),
                MQL4Icons.Healing16,
                e -> readyCount + " AI fix" + (readyCount > 1 ? "es" : "") + " available",
                null,
                GutterIconRenderer.Alignment.RIGHT,
                () -> readyCount + " AI fix" + (readyCount > 1 ? "es" : "") + " available"
        );
    }
}
