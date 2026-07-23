/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.catalog;

import com.intellij.notification.Notification;
import com.intellij.notification.NotificationType;
import com.intellij.notification.Notifications;
import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.progress.ProgressIndicator;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.progress.Task;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.LocalFileSystem;
import com.limemojito.oss.mql.inspection.MqlProblemsLoggerService;
import org.jetbrains.annotations.NotNull;

import java.nio.file.Path;
import java.util.concurrent.Future;

/**
 * "Generate MQL Inspection Catalog" — on-demand action that (re-)scans the project's MQL files
 * and writes {@code docs/MQL_INSPECTION_CATALOG.md} via {@link InspectionCatalogWriter}. This is
 * the sole surviving artifact of the retired AI-healing pipeline (see
 * {@code docs/REVAMP_PLAN.md} Phase 2): a plain, AI-free triage document.
 *
 * <p>Runs the scan and file write off the EDT under a background {@link Task}, then refreshes the
 * VFS for the written file and shows a balloon notification with the result.</p>
 */
public final class GenerateInspectionCatalogAction extends AnAction {

    private static final Logger LOG = Logger.getInstance(GenerateInspectionCatalogAction.class);
    private static final String NOTIFICATION_GROUP = "MQL Inspection Catalog";

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();
        if (project == null) {
            return;
        }

        ProgressManager.getInstance().run(new Task.Backgroundable(project,
                "Generating MQL Inspection Catalog", true) {
            @Override
            public void run(@NotNull ProgressIndicator indicator) {
                MqlProblemsLoggerService loggerService = MqlProblemsLoggerService.getInstance(project);
                indicator.setText("Scanning MQL files for problems…");
                try {
                    Future<?> scan = loggerService.scanAllFiles();
                    if (scan != null) {
                        scan.get();
                    }
                } catch (InterruptedException ie) {
                    Thread.currentThread().interrupt();
                    return;
                } catch (Exception ex) {
                    LOG.warn("Inspection scan failed before catalog generation; writing catalog "
                            + "from the last available snapshot", ex);
                }

                if (project.isDisposed()) {
                    return;
                }

                indicator.setText("Writing docs/MQL_INSPECTION_CATALOG.md…");
                InspectionCatalogWriter.write(project, loggerService);

                ApplicationManager.getApplication().invokeLater(() -> notifyCatalogWritten(project));
            }
        });
    }

    private static void notifyCatalogWritten(@NotNull Project project) {
        if (project.isDisposed()) {
            return;
        }
        String basePath = project.getBasePath();
        boolean written = false;
        if (basePath != null) {
            Path target = Path.of(basePath, "docs", "MQL_INSPECTION_CATALOG.md");
            written = java.nio.file.Files.exists(target);
            LocalFileSystem.getInstance().refreshAndFindFileByNioFile(target);
        }

        String content = written
                ? "docs/MQL_INSPECTION_CATALOG.md written."
                : "Catalog not written — project has no docs/ folder to write into.";
        Notifications.Bus.notify(new Notification(NOTIFICATION_GROUP, "MQL Inspection Catalog",
                content, written ? NotificationType.INFORMATION : NotificationType.WARNING), project);
    }
}
