/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.startup.StartupActivity;
import com.intellij.openapi.vfs.VirtualFileManager;
import org.jetbrains.annotations.NotNull;

// TODO: migrate to ProjectActivity (StartupActivity is deprecated but still works on 2025.3)
@SuppressWarnings("deprecation")
public class MqlProblemsLoggerStartupActivity implements StartupActivity.DumbAware {

    @Override
    public void runActivity(@NotNull Project project) {
        MqlProblemsLoggerService service = MqlProblemsLoggerService.getInstance(project);

        // Register file change listener for ongoing monitoring, scoped to the service's
        // lifetime so the connection is disposed with it
        project.getMessageBus().connect(service)
                .subscribe(VirtualFileManager.VFS_CHANGES, new MqlProblemsLoggerFileListener(project));

        // Trigger initial full scan (defers automatically if still indexing)
        service.scanAllFiles();
    }
}
