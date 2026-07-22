/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.vcs;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.Messages;
import com.intellij.openapi.vcs.CheckinProjectPanel;
import com.intellij.openapi.vcs.changes.CommitContext;
import com.intellij.openapi.vcs.checkin.CheckinHandler;
import com.intellij.openapi.vcs.checkin.CheckinHandlerFactory;
import com.limemojito.oss.mql.healing.HealingService;
import org.jetbrains.annotations.NotNull;

public class HealingCheckinHandlerFactory extends CheckinHandlerFactory {

    @NotNull
    @Override
    public CheckinHandler createHandler(@NotNull CheckinProjectPanel panel,
                                         @NotNull CommitContext commitContext) {
        return new HealingCheckinHandler(panel);
    }

    private static class HealingCheckinHandler extends CheckinHandler {

        private final CheckinProjectPanel panel;

        HealingCheckinHandler(@NotNull CheckinProjectPanel panel) {
            this.panel = panel;
        }

        @Override
        public ReturnResult beforeCheckin() {
            Project project = panel.getProject();
            // Read the in-memory cache — beforeCheckin runs on the EDT, no SQLite here
            int pendingCount = HealingService.getInstance(project).getPendingFixCount();

            if (pendingCount <= 0) {
                return ReturnResult.COMMIT;
            }

            int result = Messages.showYesNoCancelDialog(
                    project,
                    pendingCount + " pending AI fix" + (pendingCount > 1 ? "es" : "") +
                            " available. Apply before commit?",
                    "MQL AI Healing",
                    "Apply Fixes",
                    "Commit Anyway",
                    "Cancel",
                    Messages.getQuestionIcon()
            );

            return switch (result) {
                case Messages.YES -> ReturnResult.CANCEL; // User chose to apply fixes first
                case Messages.NO -> ReturnResult.COMMIT;  // User chose to commit anyway
                default -> ReturnResult.CANCEL;            // User cancelled
            };
        }
    }
}
