/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ui;

import com.intellij.codeInsight.intention.IntentionAction;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.codeInspection.util.IntentionFamilyName;
import com.intellij.codeInspection.util.IntentionName;
import com.intellij.lang.annotation.AnnotationHolder;
import com.intellij.lang.annotation.Annotator;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.IncorrectOperationException;
import com.limemojito.oss.mql.healing.ai.DiffParser;
import com.limemojito.oss.mql.healing.actions.DiffApplier;
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class HealingAnnotator implements Annotator {

    @Override
    public void annotate(@NotNull PsiElement element, @NotNull AnnotationHolder holder) {
        PsiFile file = element.getContainingFile();
        if (file == null) return;

        // Only process the first child to avoid duplicate annotations
        if (element != file.getFirstChild()) return;

        VirtualFile vf = file.getVirtualFile();
        if (vf == null) return;

        Project project = element.getProject();
        HealingDatabase db = HealingDatabase.getInstance(project);
        List<ClaudeTask> tasks = db.getClaudeTasksForFile(vf.getUrl());

        for (ClaudeTask task : tasks) {
            if (!ClaudeTask.STATUS_COMPLETED.equals(task.status()) || task.diff() == null) continue;

            ProblemRecord problem = db.getProblemById(task.problemId());
            if (problem == null) continue;

            holder.newAnnotation(
                            HighlightSeverity.INFORMATION,
                            "AI fix available: " + problem.inspectionName()
                    )
                    .range(element.getTextRange())
                    .highlightType(ProblemHighlightType.INFORMATION)
                    .withFix(new ApplyAiFixIntention(task.id(), task.diff(), problem.inspectionName()))
                    .create();
        }
    }

    private static class ApplyAiFixIntention implements IntentionAction {

        private final long taskId;
        private final String diff;
        private final String inspectionName;

        ApplyAiFixIntention(long taskId, @NotNull String diff, @NotNull String inspectionName) {
            this.taskId = taskId;
            this.diff = diff;
            this.inspectionName = inspectionName;
        }

        @Override
        public @IntentionName @NotNull String getText() {
            return "Apply AI fix: " + inspectionName;
        }

        @Override
        public @IntentionFamilyName @NotNull String getFamilyName() {
            return "MQL AI Healing";
        }

        @Override
        public boolean isAvailable(@NotNull Project project, Editor editor, PsiFile file) {
            return true;
        }

        @Override
        public void invoke(@NotNull Project project, Editor editor, PsiFile file) throws IncorrectOperationException {
            DiffParser.DiffPatch patch = DiffParser.parse(diff);
            if (patch == null) return;

            boolean success = DiffApplier.apply(project, patch);
            if (success) {
                HealingDatabase.getInstance(project).markClaudeTaskApplied(taskId);
            }
        }

        @Override
        public boolean startInWriteAction() {
            return false;
        }
    }
}
