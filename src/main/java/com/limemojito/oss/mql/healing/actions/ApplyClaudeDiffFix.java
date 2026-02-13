/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.actions;

import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.healing.ai.DiffParser;
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import org.jetbrains.annotations.NotNull;

public class ApplyClaudeDiffFix implements LocalQuickFix {

    private static final Logger LOG = Logger.getInstance(ApplyClaudeDiffFix.class);

    private final long claudeTaskId;

    public ApplyClaudeDiffFix(long claudeTaskId) {
        this.claudeTaskId = claudeTaskId;
    }

    @NotNull
    @Override
    public String getFamilyName() {
        return "Apply AI-generated fix";
    }

    @NotNull
    @Override
    public String getName() {
        return "Apply AI fix (Claude diff)";
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        HealingDatabase db = HealingDatabase.getInstance(project);

        // Find the Claude task
        var tasks = db.getPendingClaudeTasks();
        ClaudeTask task = null;
        for (ClaudeTask t : tasks) {
            if (t.id() == claudeTaskId) {
                task = t;
                break;
            }
        }

        if (task == null || task.diff() == null) {
            LOG.warn("Claude task not found or has no diff: " + claudeTaskId);
            return;
        }

        DiffParser.DiffPatch patch = DiffParser.parse(task.diff());
        if (patch == null) {
            LOG.warn("Failed to parse diff for Claude task: " + claudeTaskId);
            db.updateClaudeTaskStatus(claudeTaskId, ClaudeTask.STATUS_FAILED);
            return;
        }

        boolean success = DiffApplier.apply(project, patch);
        if (success) {
            db.markClaudeTaskApplied(claudeTaskId);
            LOG.info("Applied AI fix for task: " + claudeTaskId);
        } else {
            db.updateClaudeTaskStatus(claudeTaskId, ClaudeTask.STATUS_FAILED);
            LOG.warn("Failed to apply AI fix for task: " + claudeTaskId);
        }
    }
}
