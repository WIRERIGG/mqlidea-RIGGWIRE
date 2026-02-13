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
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

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
        HealingDatabase db = HealingDatabase.getInstance(project);
        List<ClaudeTask> tasks = db.getClaudeTasksForFile(vf.getUrl());

        if (tasks.isEmpty()) return null;

        // Count completed tasks with diffs ready to apply
        long readyCount = tasks.stream()
                .filter(t -> ClaudeTask.STATUS_COMPLETED.equals(t.status()) && t.diff() != null)
                .count();

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
