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
import com.intellij.openapi.actionSystem.ActionUpdateThread;
import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.application.ReadAction;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.progress.ProgressIndicator;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.progress.Task;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.WindowManager;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
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
    public @NotNull ActionUpdateThread getActionUpdateThread() {
        // update() only reads the event's VIRTUAL_FILE / project — safe on the background thread,
        // which is the required choice on the 2025.3 platform (the old EDT path is deprecated).
        return ActionUpdateThread.BGT;
    }

    @Override
    public void update(@NotNull AnActionEvent e) {
        VirtualFile file = e.getData(CommonDataKeys.VIRTUAL_FILE);
        boolean enabled = e.getProject() != null && file != null && isCheckable(file);
        e.getPresentation().setEnabledAndVisible(enabled);
    }

    @Override
    public void actionPerformed(@NotNull AnActionEvent e) {
        Project project = e.getProject();
        VirtualFile file = e.getData(CommonDataKeys.VIRTUAL_FILE);
        if (project != null && file != null) {
            runCompileCheck(project, file);
        }
    }

    /**
     * Force a fresh compile of {@code file} and refresh diagnostics/status — the shared entry point
     * for both the "Compile Check Now" action and a click on the status-bar widget. No-op when the
     * file isn't a compilable MQL program or header. A header is checked by compiling the program
     * that includes it ({@link MqlCompilerExternalAnnotator#programFor}); its own diagnostics are reported.
     */
    public static void runCompileCheck(@NotNull Project project, @NotNull VirtualFile file) {
        if (!isCheckable(file)) {
            return;
        }
        FileDocumentManager.getInstance().saveAllDocuments();
        ProgressManager.getInstance().run(new Task.Backgroundable(project, "Compiling " + file.getName(), false) {
            @Override
            public void run(@NotNull ProgressIndicator indicator) {
                MqlCompilerService service = project.getService(MqlCompilerService.class);
                VirtualFile target = file;
                if (MqlCompilerExternalAnnotator.isHeader(file.getName())) {
                    indicator.setText("Finding a program that includes " + file.getName() + "…");
                    target = ReadAction.nonBlocking(() -> {
                        PsiFile psi = PsiManager.getInstance(project).findFile(file);
                        PsiFile program = psi == null ? null : MqlCompilerExternalAnnotator.programFor(psi);
                        return program == null ? null : program.getVirtualFile();
                    }).inSmartMode(project).executeSynchronously();
                    service.rememberHeaderProgram(file, target);
                    if (target == null) {
                        ApplicationManager.getApplication().invokeLater(() -> notifyNoProgram(project, file));
                        return;
                    }
                }
                indicator.setText("Running MQL compiler on " + target.getName() + "…");
                MqlCompilerService.CompileResult result = service.recompile(target);
                VirtualFile compiled = target;
                ApplicationManager.getApplication().invokeLater(() -> onCompiled(project, file, compiled, result));
            }
        });
    }

    private static boolean isCheckable(@NotNull VirtualFile file) {
        return MqlCompilerExternalAnnotator.isCompilableProgram(file.getName())
                || MqlCompilerExternalAnnotator.isHeader(file.getName());
    }

    private static void onCompiled(@NotNull Project project, @NotNull VirtualFile file, @NotNull VirtualFile compiled,
                                    @NotNull MqlCompilerService.CompileResult result) {
        if (project.isDisposed()) {
            return;
        }
        notify(project, file, compiled, result);

        // A full restart is cheap enough for a user-triggered, one-off "Compile Check Now" (unlike
        // the per-save daemon pass). restart() and restart(PsiFile) are deprecated; the reason
        // overload exists on every supported platform version.
        DaemonCodeAnalyzer.getInstance(project).restart("MQL Compile Check Now finished");

        StatusBar bar = WindowManager.getInstance().getStatusBar(project);
        if (bar != null) {
            bar.updateWidget(MqlCompileStatusBarWidgetFactory.WIDGET_ID);
        }
    }

    private static void notify(@NotNull Project project, @NotNull VirtualFile file, @NotNull VirtualFile compiled,
                                @NotNull MqlCompilerService.CompileResult result) {
        String message;
        NotificationType type;
        if (!result.compilerAvailable()) {
            message = "MQL compiler is not available — no mt5/MetaEditor/Wine launcher could be found on this machine.";
            type = NotificationType.WARNING;
        } else if (!file.equals(compiled)) {
            int[] counts = MqlCompilerExternalAnnotator.headerCounts(result, file);
            message = file.getName() + ": " + counts[0] + " error(s), " + counts[1] + " warning(s) (compiled via "
                    + compiled.getName() + ": " + result.errors() + " error(s) in total).";
            type = counts[0] > 0 ? NotificationType.ERROR : NotificationType.INFORMATION;
        } else {
            message = file.getName() + ": " + result.errors() + " error(s), " + result.warnings() + " warning(s).";
            type = result.errors() > 0 ? NotificationType.ERROR : NotificationType.INFORMATION;
        }
        Notifications.Bus.notify(new Notification(NOTIFICATION_GROUP, "MQL Compile Check", message, type), project);
    }

    private static void notifyNoProgram(@NotNull Project project, @NotNull VirtualFile header) {
        if (project.isDisposed()) {
            return;
        }
        String message = header.getName() + " isn't #included by any .mq4/.mq5 program in this project, "
                + "so there is nothing to compile it through.";
        Notifications.Bus.notify(new Notification(NOTIFICATION_GROUP, "MQL Compile Check", message,
                NotificationType.WARNING), project);
    }
}
