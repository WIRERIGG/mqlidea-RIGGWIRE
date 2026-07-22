/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing;

import com.intellij.openapi.Disposable;
import com.intellij.openapi.application.ReadAction;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.VirtualFileManager;
import com.limemojito.oss.mql.healing.ai.ClaudeClient;
import com.limemojito.oss.mql.healing.ai.GrokClient;
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.GrokInsight;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import com.limemojito.oss.mql.settings.MQL4PluginSettings;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;

public final class HealingService implements Disposable {

    private static final Logger LOG = Logger.getInstance(HealingService.class);
    private static final int MAX_PROBLEMS_PER_CYCLE = 10;
    private static final int CONTEXT_LINES = 25;

    private final Project project;
    private final ScheduledExecutorService executor;
    private volatile ScheduledFuture<?> scheduledTask;
    private volatile GrokClient grokClient;
    private volatile ClaudeClient claudeClient;

    // In-memory snapshot of claude_tasks state so EDT consumers (line markers, quick fixes,
    // checkin handler) never run SQLite queries on the EDT. Refreshed after task mutations.
    private volatile Map<String, Integer> readyFixCountsByFile = Map.of();
    private volatile int pendingFixCount;

    public HealingService(@NotNull Project project) {
        this.project = project;
        this.executor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "MQL-Healing-Service");
            t.setDaemon(true);
            t.setPriority(Thread.MIN_PRIORITY);
            return t;
        });
    }

    public static HealingService getInstance(@NotNull Project project) {
        return project.getService(HealingService.class);
    }

    public void start() {
        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        int delayMinutes = settings.getHealingDelayMinutes();
        if (delayMinutes <= 0) delayMinutes = 5;

        stop();
        scheduledTask = executor.scheduleWithFixedDelay(
                this::runHealingCycle,
                delayMinutes,
                delayMinutes,
                TimeUnit.MINUTES
        );
        LOG.info("Healing service started with " + delayMinutes + " minute intervals");
    }

    public void stop() {
        ScheduledFuture<?> task = scheduledTask;
        if (task != null) {
            task.cancel(false);
            scheduledTask = null;
        }
    }

    public void triggerNow() {
        executor.submit(this::runHealingCycle);
    }

    public void setGrokModel(@NotNull String model) {
        this.grokClient = new GrokClient(model);
    }

    public void setClaudeModel(@NotNull String model) {
        this.claudeClient = new ClaudeClient(model);
    }

    /** EDT-safe: number of Claude fixes that are pending or ready to apply (cached). */
    public int getPendingFixCount() {
        return pendingFixCount;
    }

    /** EDT-safe: number of completed Claude fixes with diffs for the given file (cached). */
    public int getReadyFixCountForFile(@NotNull String fileUrl) {
        return readyFixCountsByFile.getOrDefault(fileUrl, 0);
    }

    /** Refreshes the pending-fix cache on the service's background thread. */
    public void refreshPendingFixCacheAsync() {
        if (project.isDisposed()) return;
        try {
            executor.submit(this::refreshPendingFixCache);
        } catch (RejectedExecutionException ignored) {
            // Service disposed — nothing to refresh
        }
    }

    private void refreshPendingFixCache() {
        if (project.isDisposed()) return;
        try {
            HealingDatabase db = HealingDatabase.getInstance(project);
            pendingFixCount = db.getPendingClaudeTaskCount();
            readyFixCountsByFile = Map.copyOf(db.getReadyClaudeTaskCountsByFile());
        } catch (Exception e) {
            LOG.warn("Failed to refresh pending fix cache", e);
        }
    }

    private void runHealingCycle() {
        if (project.isDisposed()) return;

        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        if (!settings.isAutoHealEnabled()) return;

        try {
            HealingDatabase db = HealingDatabase.getInstance(project);

            // Phase 1: Grok analysis for problems without insights
            runGrokAnalysis(db);

            // Phase 2: Claude refactoring for problems with insights but no tasks
            runClaudeRefactoring(db);

            refreshPendingFixCache();

        } catch (Exception e) {
            LOG.warn("Healing cycle failed", e);
        }
    }

    private void runGrokAnalysis(@NotNull HealingDatabase db) {
        GrokClient grok = this.grokClient;
        if (grok == null) {
            grok = new GrokClient("grok-2");
            this.grokClient = grok;
        }

        List<ProblemRecord> problems = db.getProblemsWithoutGrokInsight();
        int processed = 0;

        for (ProblemRecord problem : problems) {
            if (project.isDisposed() || processed >= MAX_PROBLEMS_PER_CYCLE) break;

            try {
                FileContext context = readFileContext(problem.fileUrl(), problem.line());
                String insight = grok.analyzeProblems(problem, context != null ? context.text() : null);

                if (insight != null) {
                    db.insertGrokInsight(problem.id(), insight);
                    processed++;
                    LOG.info("Grok analyzed: " + problem.filePath() + ":" + problem.line()
                            + " [" + problem.inspectionName() + "]");
                }
            } catch (Exception e) {
                // One bad problem must never abort the whole cycle
                LOG.warn("Grok analysis failed for " + problem.filePath() + ":" + problem.line(), e);
            }

            // Rate limit: pause between API calls
            try {
                Thread.sleep(2000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }

    private void runClaudeRefactoring(@NotNull HealingDatabase db) {
        ClaudeClient claude = this.claudeClient;
        if (claude == null) {
            claude = new ClaudeClient("claude-sonnet-4-5-20250929");
            this.claudeClient = claude;
        }

        List<ProblemRecord> problems = db.getProblemsWithInsightButNoClaudeTask();
        int processed = 0;

        for (ProblemRecord problem : problems) {
            if (project.isDisposed() || processed >= MAX_PROBLEMS_PER_CYCLE) break;

            try {
                GrokInsight insight = db.getGrokInsightForProblem(problem.id());
                if (insight == null) continue;

                FileContext context = readFileContext(problem.fileUrl(), problem.line());
                if (context == null) continue;

                String diff = claude.generateFix(problem, insight.insight(),
                                                 context.text(), context.startLine());

                if (diff != null) {
                    // Single task row per generated fix: COMPLETED means "generated, pending
                    // application". APPLIED is only set by DiffApplier after a successful apply.
                    db.insertClaudeTask(problem.id(), diff, ClaudeTask.STATUS_COMPLETED);
                    processed++;
                    LOG.info("Claude generated fix for: " + problem.filePath() + ":" + problem.line());
                }
            } catch (Exception e) {
                // One bad problem must never abort the whole cycle
                LOG.warn("Claude refactoring failed for " + problem.filePath() + ":" + problem.line(), e);
            }

            try {
                Thread.sleep(3000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                return;
            }
        }
    }

    @Nullable
    private FileContext readFileContext(@NotNull String fileUrl, int problemLine) {
        return ReadAction.compute(() -> {
            VirtualFile vf = VirtualFileManager.getInstance().findFileByUrl(fileUrl);
            if (vf == null || !vf.isValid()) return null;

            Document doc = FileDocumentManager.getInstance().getDocument(vf);
            if (doc == null) return null;

            int lineCount = doc.getLineCount();
            int line = problemLine - 1;
            if (line >= lineCount) {
                // Stale problem line beyond the current end of file — skip this problem
                LOG.info("Problem line " + problemLine + " is beyond end of " + fileUrl + " — skipping");
                return null;
            }
            if (line < 0) line = 0;

            int startLine = Math.max(0, line - CONTEXT_LINES);
            int endLine = Math.min(lineCount - 1, line + CONTEXT_LINES);

            int startOffset = doc.getLineStartOffset(startLine);
            int endOffset = doc.getLineEndOffset(endLine);

            return new FileContext(doc.getText().substring(startOffset, endOffset), startLine + 1);
        });
    }

    /** A snippet of file text plus the 1-based file line at which the snippet begins. */
    private record FileContext(@NotNull String text, int startLine) {
    }

    @Override
    public void dispose() {
        stop();
        executor.shutdownNow();
    }
}
