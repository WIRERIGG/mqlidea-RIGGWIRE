/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.newvfs.BulkFileListener;
import com.intellij.openapi.vfs.newvfs.events.VFileEvent;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public class MqlProblemsLoggerFileListener implements BulkFileListener {

    private static final Set<String> MQL_EXTENSIONS = Set.of("mq4", "mq5", "mqh", "mql4", "mql5");

    private final Project project;

    public MqlProblemsLoggerFileListener(@NotNull Project project) {
        this.project = project;
    }

    @Override
    public void after(@NotNull List<? extends VFileEvent> events) {
        if (project.isDisposed()) return;

        List<String> changedUrls = new ArrayList<>();
        for (VFileEvent event : events) {
            VirtualFile file = event.getFile();
            if (file != null) {
                String ext = file.getExtension();
                if (ext != null && MQL_EXTENSIONS.contains(ext.toLowerCase())) {
                    changedUrls.add(file.getUrl());
                }
            }
        }

        if (!changedUrls.isEmpty()) {
            MqlProblemsLoggerService service = MqlProblemsLoggerService.getInstance(project);
            service.markDirty(changedUrls);
            service.scheduleScan();
        }
    }
}
