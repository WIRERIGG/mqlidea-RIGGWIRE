/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.actions;

import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.notification.Notification;
import com.intellij.notification.NotificationType;
import com.intellij.notification.Notifications;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.healing.HealingService;
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
    public boolean startInWriteAction() {
        return false; // DB lookups run on a pooled thread; DiffApplier runs its own write command
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        // Never run SQLite queries on the EDT — look up the task on a pooled thread
        ApplicationManager.getApplication().executeOnPooledThread(() -> {
            if (project.isDisposed()) return;
            HealingDatabase db = HealingDatabase.getInstance(project);

            // Find the Claude task
            ClaudeTask task = null;
            for (ClaudeTask t : db.getPendingClaudeTasks()) {
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
                HealingService.getInstance(project).refreshPendingFixCacheAsync();
                notifyNotApplied(project);
                return;
            }

            ApplicationManager.getApplication().invokeLater(() -> {
                if (project.isDisposed()) return;
                boolean success = DiffApplier.apply(project, patch);
                ApplicationManager.getApplication().executeOnPooledThread(() -> {
                    if (project.isDisposed()) return;
                    if (success) {
                        db.markClaudeTaskApplied(claudeTaskId);
                        LOG.info("Applied AI fix for task: " + claudeTaskId);
                    } else {
                        // Leave the task un-applied so it can be retried once the file settles
                        LOG.warn("Failed to apply AI fix for task: " + claudeTaskId);
                        notifyNotApplied(project);
                    }
                    HealingService.getInstance(project).refreshPendingFixCacheAsync();
                });
            });
        });
    }

    private static void notifyNotApplied(@NotNull Project project) {
        Notifications.Bus.notify(new Notification(
                "MQL AI Healing",
                "AI fix not applied",
                "The AI-generated diff could not be applied cleanly. " +
                        "The file may have changed since the fix was generated.",
                NotificationType.WARNING), project);
    }
}
