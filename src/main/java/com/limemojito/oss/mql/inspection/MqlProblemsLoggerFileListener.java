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
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Registered declaratively via {@code <projectListeners>} in plugin.xml (topic
 * {@link BulkFileListener}), one instance constructed per project. This replaces the deprecated
 * {@code StartupActivity}-based wiring (formerly {@code MqlProblemsLoggerStartupActivity}, which
 * manually connected this listener to the project message bus and kicked off the initial full
 * scan) -- the platform now handles both the subscription and the listener's lifecycle. The
 * one-time initial scan is also piggybacked onto the first VFS event this listener receives (see
 * {@link #initialized}) as a backstop; the primary open-time trigger is now
 * {@link MqlProblemsLoggerStartupActivity}. Both are idempotent (the {@link #initialized} guard
 * here, and the modstamp cache in {@link MqlProblemsLoggerService}), so running both is harmless.
 */
public class MqlProblemsLoggerFileListener implements BulkFileListener {

    private static final Set<String> MQL_EXTENSIONS = Set.of("mq4", "mq5", "mqh", "mql4", "mql5");

    private final Project project;
    private final AtomicBoolean initialized = new AtomicBoolean(false);

    public MqlProblemsLoggerFileListener(@NotNull Project project) {
        this.project = project;
    }

    @Override
    public void after(@NotNull List<? extends VFileEvent> events) {
        if (project.isDisposed()) return;

        // First event delivered to this project after open: do the one-time full scan the old
        // postStartupActivity used to trigger explicitly, so mql-problems.log / mql-tasks.md get
        // written even if the very first event isn't itself an MQL file change.
        if (initialized.compareAndSet(false, true)) {
            MqlProblemsLoggerService.getInstance(project).scanAllFiles();
        }

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
