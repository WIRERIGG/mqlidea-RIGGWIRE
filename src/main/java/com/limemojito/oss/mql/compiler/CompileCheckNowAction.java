/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer;
import com.intellij.notification.Notification;
import com.intellij.notification.NotificationType;
import com.intellij.notification.Notifications;
import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.progress.ProgressIndicator;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.progress.Task;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.WindowManager;
import org.jetbrains.annotations.NotNull;

/**
 * "Compile Check Now" &mdash; force-recompiles the current MQL program through
 * {@link MqlCompilerService#recompile(VirtualFile)} (bypassing the modification-stamp cache) and
 * restarts the daemon so squiggles from {@link MqlCompilerExternalAnnotator} refresh immediately,
 * instead of waiting for the next save-triggered background pass. See docs/REVAMP_PLAN.md Phase 1.
 *
 * <p>A clear balloon notification reports the outcome, including the honest "compiler not
 * available" case (no {@code mt5}/MetaEditor/Wine launcher could be found) rather than doing
 * nothing silently.</p>
 */
public final class CompileCheckNowAction extends AnAction {

    private static final String NOTIFICATION_GROUP = "MQL Compiler";

    @Override
    public void update(@NotNull AnActionEvent e) {
        VirtualFile file = e.getData(CommonDataKeys.VIRTUAL_FILE);
        boolean enabled = e.getProject() != null && file != null
                && MqlCompilerExternalAnnotator.isCompilableProgram(file.getName());
        e.getPresentation().setEnabledAndVisible(enabled);
    }

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();
        VirtualFile file = e.getData(CommonDataKeys.VIRTUAL_FILE);
        if (project == null || file == null || !MqlCompilerExternalAnnotator.isCompilableProgram(file.getName())) {
            return;
        }

        FileDocumentManager.getInstance().saveAllDocuments();

        ProgressManager.getInstance().run(new Task.Backgroundable(project, "Compiling " + file.getName(), false) {
            @Override
            public void run(@NotNull ProgressIndicator indicator) {
                indicator.setText("Running MQL compiler on " + file.getName() + "…");
                MqlCompilerService service = project.getService(MqlCompilerService.class);
                MqlCompilerService.CompileResult result = service.recompile(file);
                ApplicationManager.getApplication().invokeLater(() -> onCompiled(project, file, result));
            }
        });
    }

    private static void onCompiled(@NotNull Project project, @NotNull VirtualFile file,
                                    @NotNull MqlCompilerService.CompileResult result) {
        if (project.isDisposed()) {
            return;
        }
        notify(project, file, result);

        // restart(PsiFile) is deprecated on this platform version; a full restart is cheap enough
        // for a user-triggered, one-off "Compile Check Now" (unlike the per-save daemon pass).
        DaemonCodeAnalyzer.getInstance(project).restart();

        StatusBar bar = WindowManager.getInstance().getStatusBar(project);
        if (bar != null) {
            bar.updateWidget(MqlCompileStatusBarWidgetFactory.WIDGET_ID);
        }
    }

    private static void notify(@NotNull Project project, @NotNull VirtualFile file,
                                @NotNull MqlCompilerService.CompileResult result) {
        String message;
        NotificationType type;
        if (!result.compilerAvailable()) {
            message = "MQL compiler is not available — no mt5/MetaEditor/Wine launcher could be found on this machine.";
            type = NotificationType.WARNING;
        } else {
            message = file.getName() + ": " + result.errors() + " error(s), " + result.warnings() + " warning(s).";
            type = result.errors() > 0 ? NotificationType.ERROR : NotificationType.INFORMATION;
        }
        Notifications.Bus.notify(new Notification(NOTIFICATION_GROUP, "MQL Compile Check", message, type), project);
    }
}
