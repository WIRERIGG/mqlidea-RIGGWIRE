/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
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
import com.limemojito.oss.mql.healing.ai.ClaudeCliClient;
import com.limemojito.oss.mql.healing.ai.ClaudeCliInsightClient;
import com.limemojito.oss.mql.healing.ai.ClaudeFixGenerator;
import com.limemojito.oss.mql.healing.ai.GrokClient;
import com.limemojito.oss.mql.healing.ai.InsightGenerator;
import com.limemojito.oss.mql.healing.db.ClaudeTask;
import com.limemojito.oss.mql.healing.db.GrokInsight;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import com.limemojito.oss.mql.settings.MQL4PluginSettings;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

public final class HealingService implements Disposable {

    private static final Logger LOG = Logger.getInstance(HealingService.class);
    private static final int MAX_PROBLEMS_PER_CYCLE = 10;
    private static final int CONTEXT_LINES = 25;
    /** Consecutive null fixes after which the CLI pass assumes rate limiting and stops early. */
    private static final int MAX_CONSECUTIVE_NULL_FIXES = 5;
    /** Minimum interval between pending-fix cache refreshes while fixes land mid-pass. */
    private static final long CACHE_REFRESH_THROTTLE_MS = 2_000;

    private final Project project;
    private final ScheduledExecutorService executor;
    private volatile ScheduledFuture<?> scheduledTask;
    private volatile InsightGenerator grokClient;
    private volatile ClaudeFixGenerator claudeClient;

    // Live state of the currently running CLI worker pass, so stop()/dispose() can
    // stop submissions and interrupt in-flight claude -p workers.
    private volatile ExecutorService activeWorkerPool;
    private volatile AtomicBoolean activePassAbort;

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
        // First cycle runs promptly after start; subsequent cycles keep the configured period.
        scheduledTask = executor.scheduleWithFixedDelay(
                () -> runHealingCycle(false),
                15,
                (long) delayMinutes * 60,
                TimeUnit.SECONDS
        );
        LOG.info("Healing service started with " + delayMinutes + " minute intervals");
    }

    public void stop() {
        ScheduledFuture<?> task = scheduledTask;
        if (task != null) {
            task.cancel(false);
            scheduledTask = null;
        }
        cancelActivePass();
    }

    /** Stops a running CLI worker pass: no new submissions, in-flight workers interrupted. */
    private void cancelActivePass() {
        AtomicBoolean abort = activePassAbort;
        if (abort != null) {
            abort.set(true);
        }
        ExecutorService pool = activeWorkerPool;
        if (pool != null) {
            pool.shutdownNow();
        }
    }

    /**
     * Runs a healing cycle immediately on the service executor, bypassing the auto-heal
     * setting. Safe to call from the EDT — the cycle itself runs on the background thread.
     */
    public void healNow() {
        if (project.isDisposed()) return;
        try {
            executor.submit(() -> runHealingCycle(true));
        } catch (RejectedExecutionException ignored) {
            // Service disposed — nothing to run
        }
    }

    public void setGrokModel(@NotNull String model) {
        this.grokClient = createInsightGenerator(model);
    }

    public void setClaudeModel(@NotNull String model) {
        this.claudeClient = createClaudeFixGenerator(model);
    }

    /**
     * Picks the analysis provider from settings: the local Claude Code CLI ({@code claude -p},
     * using the user's Claude Code login) when enabled, otherwise the xAI Grok HTTP API.
     * When the CLI is enabled the Claude model is used (analysis now runs on Claude), so the
     * supplied Grok model is only used for the Grok fallback.
     */
    @NotNull
    private static InsightGenerator createInsightGenerator(@NotNull String grokModel) {
        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        if (settings.isUseClaudeCli()) {
            return new ClaudeCliInsightClient(settings.getClaudeModel(), settings.getClaudeCliPath());
        }
        return new GrokClient(grokModel);
    }

    /**
     * Picks the fix provider from settings: the local Claude Code CLI ({@code claude -p},
     * using the user's Claude Code login) when enabled, otherwise the Anthropic HTTP API.
     */
    @NotNull
    private static ClaudeFixGenerator createClaudeFixGenerator(@NotNull String model) {
        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        if (settings.isUseClaudeCli()) {
            return new ClaudeCliClient(model, settings.getClaudeCliPath());
        }
        return new ClaudeClient(model);
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

    private void runHealingCycle(boolean force) {
        if (project.isDisposed()) return;

        if (force) {
            LOG.info("Manual heal-now triggered");
        }

        MQL4PluginSettings settings = MQL4PluginSettings.getInstance();
        if (!force && !settings.isAutoHealEnabled()) return;

        try {
            HealingDatabase db = HealingDatabase.getInstance(project);

            if (settings.isUseClaudeCli()) {
                // Single combined analyze+fix call per problem, whole queue, bounded concurrency.
                runClaudeCliPass(db);
            } else {
                // API-key (Grok + Anthropic HTTP) path: unchanged two-phase cycle.
                // Phase 1: Grok analysis for problems without insights
                runGrokAnalysis(db);

                // Phase 2: Claude refactoring for problems with insights but no tasks
                runClaudeRefactoring(db);
            }

            refreshPendingFixCache();

        } catch (Exception e) {
            LOG.warn("Healing cycle failed", e);
        }
    }

    /**
     * CLI-mode healing pass: processes the ENTIRE queue of unresolved problems that have no
     * non-failed claude_task, one combined analyze+fix {@code claude -p} call per problem,
     * on a bounded worker pool ({@code healingConcurrency} threads, 1-8). Fixes are written to
     * the DB as they land and the pending-fix cache is refreshed (throttled to ~2s) so the tool
     * window and gutter update progressively. After {@value #MAX_CONSECUTIVE_NULL_FIXES}
     * consecutive null fixes the pass assumes {@code claude -p} is rate-limited/unavailable and
     * stops early; failed tasks stay retryable, so the next scheduled cycle resumes the queue.
     */
    private void runClaudeCliPass(@NotNull HealingDatabase db) {
        ClaudeFixGenerator claude = this.claudeClient;
        if (claude == null) {
            claude = createClaudeFixGenerator(MQL4PluginSettings.getInstance().getClaudeModel());
            this.claudeClient = claude;
        }
        final ClaudeFixGenerator fixer = claude;

        List<ProblemRecord> problems = db.getProblemsNeedingFix();
        if (problems.isEmpty()) {
            return;
        }

        int concurrency = Math.max(1, Math.min(8, MQL4PluginSettings.getInstance().getHealingConcurrency()));
        LOG.info("Claude CLI healing pass: " + problems.size() + " problem(s) with "
                + concurrency + " parallel session(s)");

        AtomicInteger threadIndex = new AtomicInteger();
        ExecutorService pool = Executors.newFixedThreadPool(concurrency, r -> {
            Thread t = new Thread(r, "MQL-Healing-Worker-" + threadIndex.incrementAndGet());
            t.setDaemon(true);
            t.setPriority(Thread.MIN_PRIORITY);
            return t;
        });
        AtomicBoolean abort = new AtomicBoolean(false);
        AtomicInteger consecutiveNulls = new AtomicInteger();
        AtomicLong lastCacheRefresh = new AtomicLong();

        activeWorkerPool = pool;
        activePassAbort = abort;
        int generated = 0;
        try {
            List<Future<Boolean>> futures = new ArrayList<>(problems.size());
            for (ProblemRecord problem : problems) {
                try {
                    futures.add(pool.submit(
                            () -> healOneProblem(db, fixer, problem, abort, consecutiveNulls, lastCacheRefresh)));
                } catch (RejectedExecutionException e) {
                    break; // Pool shut down by stop()/dispose() — stop submitting.
                }
            }
            for (Future<Boolean> future : futures) {
                try {
                    if (Boolean.TRUE.equals(future.get())) {
                        generated++;
                    }
                } catch (ExecutionException e) {
                    // healOneProblem already catches per-problem failures; this is belt-and-braces.
                    LOG.warn("Healing worker failed", e.getCause());
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    abort.set(true);
                    break;
                } catch (java.util.concurrent.CancellationException ignored) {
                    // Worker cancelled by stop()/dispose()
                }
            }
        } finally {
            activeWorkerPool = null;
            activePassAbort = null;
            pool.shutdownNow();
        }
        LOG.info("Claude CLI healing pass finished: " + generated + " fix(es) generated");
    }

    /**
     * Worker body for one problem in the CLI pass: read context, one combined
     * {@code claude -p} call ({@code grokInsight = null}), store the diff (or a failed task).
     * Never throws — one bad problem must not abort the batch.
     *
     * @return true when a fix diff was generated and stored.
     */
    private boolean healOneProblem(@NotNull HealingDatabase db,
                                   @NotNull ClaudeFixGenerator claude,
                                   @NotNull ProblemRecord problem,
                                   @NotNull AtomicBoolean abort,
                                   @NotNull AtomicInteger consecutiveNulls,
                                   @NotNull AtomicLong lastCacheRefresh) {
        if (abort.get() || project.isDisposed()) {
            return false;
        }
        try {
            FileContext context = readFileContext(problem.fileUrl(), problem.line());
            if (context == null) {
                // Stale line / unreadable file — skip without a failed task (matches Grok path).
                return false;
            }

            String diff = claude.generateFix(problem, null, context.text(), context.startLine());

            if (Thread.currentThread().isInterrupted()) {
                // Pass cancelled mid-call — don't record a bogus failure.
                return false;
            }

            if (diff != null && !diff.isBlank()) {
                consecutiveNulls.set(0);
                // COMPLETED means "generated, pending application" — the tool window/gutter
                // show it as a ready fix. APPLIED is only set by DiffApplier.
                db.insertClaudeTask(problem.id(), diff, ClaudeTask.STATUS_COMPLETED);
                LOG.info("Claude generated fix for: " + problem.filePath() + ":" + problem.line());
                maybeRefreshCacheThrottled(lastCacheRefresh);
                return true;
            }

            // Null/blank diff: mark failed so this problem isn't retried forever within the
            // pass; getProblemsNeedingFix ignores failed tasks, so a later cycle retries it.
            db.insertClaudeTask(problem.id(), "", ClaudeTask.STATUS_FAILED);
            if (consecutiveNulls.incrementAndGet() >= MAX_CONSECUTIVE_NULL_FIXES
                    && abort.compareAndSet(false, true)) {
                LOG.warn("claude -p appears rate-limited/unavailable — will resume next cycle");
            }
        } catch (Exception e) {
            LOG.warn("Claude CLI healing failed for " + problem.filePath() + ":" + problem.line(), e);
            try {
                db.insertClaudeTask(problem.id(), "", ClaudeTask.STATUS_FAILED);
            } catch (Exception ignored) {
                // DB write failed too — nothing more to do for this problem.
            }
        }
        return false;
    }

    /** Refreshes the pending-fix cache at most once every {@value #CACHE_REFRESH_THROTTLE_MS} ms. */
    private void maybeRefreshCacheThrottled(@NotNull AtomicLong lastCacheRefresh) {
        long now = System.currentTimeMillis();
        long last = lastCacheRefresh.get();
        if (now - last >= CACHE_REFRESH_THROTTLE_MS && lastCacheRefresh.compareAndSet(last, now)) {
            refreshPendingFixCache();
        }
    }

    private void runGrokAnalysis(@NotNull HealingDatabase db) {
        InsightGenerator grok = this.grokClient;
        if (grok == null) {
            grok = createInsightGenerator("grok-2");
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
        ClaudeFixGenerator claude = this.claudeClient;
        if (claude == null) {
            claude = createClaudeFixGenerator("claude-sonnet-4-5-20250929");
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
