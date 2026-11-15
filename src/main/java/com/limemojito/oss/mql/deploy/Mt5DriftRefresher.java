/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.deploy;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.newvfs.BulkFileListener;
import com.intellij.openapi.vfs.newvfs.events.VFileEvent;
import com.intellij.ui.EditorNotifications;
import org.jetbrains.annotations.NotNull;

import java.nio.file.Path;
import java.util.List;

/** Re-checks the MetaTrader drift banners when an MQL source is saved, created or deleted. */
public class Mt5DriftRefresher implements BulkFileListener {

    private final Project project;

    public Mt5DriftRefresher(@NotNull Project project) {
        this.project = project;
    }

    @Override
    public void after(@NotNull List<? extends VFileEvent> events) {
        for (VFileEvent event : events) {
            if (Mt5Mirror.isSource(Path.of(event.getPath()))) {
                EditorNotifications.getInstance(project).updateAllNotifications();
                return;
            }
        }
    }
}
