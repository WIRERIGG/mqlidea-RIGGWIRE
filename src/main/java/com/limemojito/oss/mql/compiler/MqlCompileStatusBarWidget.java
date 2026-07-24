/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.openapi.fileEditor.FileEditorManager;
import com.intellij.openapi.fileEditor.FileEditorManagerEvent;
import com.intellij.openapi.fileEditor.FileEditorManagerListener;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.StatusBarWidget;
import com.intellij.util.messages.MessageBusConnection;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Shows the last {@link MqlCompilerService.CompileResult} for whichever MQL file is currently
 * active in the editor, e.g. {@code "MQL: 0 errors, 2 warnings"}, {@code "MQL: not compiled"}, or
 * {@code "MQL: compiler N/A"}. Created per-project by {@link MqlCompileStatusBarWidgetFactory}.
 */
final class MqlCompileStatusBarWidget implements StatusBarWidget, StatusBarWidget.TextPresentation {

    private final Project project;
    private StatusBar statusBar;
    private MessageBusConnection connection;

    MqlCompileStatusBarWidget(@NotNull Project project) {
        this.project = project;
    }

    @Override
    @NotNull
    public String ID() {
        return MqlCompileStatusBarWidgetFactory.WIDGET_ID;
    }

    @Override
    public void install(@NotNull StatusBar statusBar) {
        this.statusBar = statusBar;
        connection = project.getMessageBus().connect(this);
        connection.subscribe(FileEditorManagerListener.FILE_EDITOR_MANAGER, new FileEditorManagerListener() {
            @Override
            public void selectionChanged(@NotNull FileEditorManagerEvent event) {
                statusBar.updateWidget(ID());
            }
        });
    }

    @Override
    public void dispose() {
        // MessageBusConnection is registered on `this` (see install()) and disposed by the platform
        // Disposer tree when MqlCompileStatusBarWidgetFactory.disposeWidget() disposes this widget.
    }

    @Override
    @Nullable
    public WidgetPresentation getPresentation() {
        return this;
    }

    @Override
    @NotNull
    public String getText() {
        VirtualFile file = currentFile();
        if (file == null) {
            return "MQL: no file";
        }
        if (!MqlCompilerExternalAnnotator.isCompilableProgram(file.getName())) {
            return "MQL";
        }
        MqlCompilerService.CompileResult result = project.getService(MqlCompilerService.class).getLastResult(file);
        if (result == null) {
            return "MQL: not compiled";
        }
        if (!result.compilerAvailable()) {
            return "MQL: compiler N/A";
        }
        return "MQL: " + plural(result.errors(), "error") + ", " + plural(result.warnings(), "warning");
    }

    @Override
    public float getAlignment() {
        return java.awt.Component.CENTER_ALIGNMENT;
    }

    @Override
    @Nullable
    public String getTooltipText() {
        return "MQL compiler status for the active file (docs/REVAMP_PLAN.md Phase 1)";
    }

    @Nullable
    private VirtualFile currentFile() {
        VirtualFile[] selected = FileEditorManager.getInstance(project).getSelectedFiles();
        return selected.length > 0 ? selected[0] : null;
    }

    @NotNull
    private static String plural(int count, @NotNull String noun) {
        return count + " " + noun + (count == 1 ? "" : "s");
    }
}
