/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.startup.ProjectActivity;
import kotlin.Unit;
import kotlin.coroutines.Continuation;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Triggers the initial MQL problems scan on project open, so an idle project that never receives a
 * VFS event still gets its {@code mql-problems.log}/{@code mql-tasks.md} written and its problem
 * icons computed. Previously the one-time scan was piggybacked only onto the FIRST VFS event
 * ({@link MqlProblemsLoggerFileListener}), so a freshly-opened, untouched project never scanned and
 * its problem badges never appeared. This complements (does not replace) that listener trigger —
 * both funnel through the same {@link MqlProblemsLoggerService#scanAllFiles()} (off-EDT, deferred
 * while dumb) and are idempotent, so running both is harmless.
 *
 * <p>Registered as {@code <postStartupActivity>}; implements the modern {@link ProjectActivity}
 * (a Kotlin {@code suspend fun execute(Project)}) from Java as
 * {@code execute(Project, Continuation)} returning {@link Unit#INSTANCE}.</p>
 */
public final class MqlProblemsLoggerStartupActivity implements ProjectActivity {

    @Nullable
    @Override
    public Object execute(@NotNull Project project, @NotNull Continuation<? super Unit> continuation) {
        if (!project.isDisposed()) {
            // getService (not getServiceIfCreated) so the service exists from open — the icon
            // provider's hasProblems() lookup then succeeds once this scan populates the cache.
            MqlProblemsLoggerService.getInstance(project).scanAllFiles();
        }
        return Unit.INSTANCE;
    }
}
