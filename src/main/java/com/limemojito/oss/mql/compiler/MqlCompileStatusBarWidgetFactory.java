/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.openapi.Disposable;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.Disposer;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.StatusBarWidget;
import com.intellij.openapi.wm.StatusBarWidgetFactory;
import org.jetbrains.annotations.NotNull;

/**
 * Registers the "MQL compile status" status-bar widget (docs/REVAMP_PLAN.md Phase 1). The widget
 * shows the last {@link MqlCompilerService} result for whichever MQL file is currently active, and
 * is refreshed by {@link MqlCompilerExternalAnnotator} after every background compile and by
 * {@link CompileCheckNowAction} after a manual "Compile Check Now".
 */
public final class MqlCompileStatusBarWidgetFactory implements StatusBarWidgetFactory {

    public static final String WIDGET_ID = "com.limemojito.oss.mql.compiler.status";

    @Override
    @NotNull
    public String getId() {
        return WIDGET_ID;
    }

    @Override
    @NotNull
    public String getDisplayName() {
        return "MQL Compile Status";
    }

    @Override
    public boolean isAvailable(@NotNull Project project) {
        return true;
    }

    @Override
    @NotNull
    public StatusBarWidget createWidget(@NotNull Project project) {
        return new MqlCompileStatusBarWidget(project);
    }

    @Override
    public void disposeWidget(@NotNull StatusBarWidget widget) {
        if (widget instanceof Disposable disposable) {
            Disposer.dispose(disposable);
        }
    }

    @Override
    public boolean canBeEnabledOn(@NotNull StatusBar statusBar) {
        return true;
    }
}
