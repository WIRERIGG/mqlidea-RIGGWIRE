/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import com.limemojito.oss.mql.healing.db.ProblemRecord;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * The analysis stage powered by the local Claude Code CLI ({@code claude -p}, headless one-shot),
 * using the user's Claude Code login for auth — no Anthropic or Grok API key required.
 *
 * <p>Reuses {@link GrokClient}'s user-prompt builder so the analysis input is identical across
 * providers, and delegates the subprocess mechanics to
 * {@link ClaudeCliClient#runClaudePrompt}. Produces the same kind of plain-text "insight" that
 * Grok would, which is stored in the healing DB and later handed to the fix-generation stage.</p>
 *
 * <p>Runs on HealingService's pooled executor thread (off-EDT); never performs read actions or
 * touches the EDT.</p>
 */
public final class ClaudeCliInsightClient implements InsightGenerator {

    /** System prompt for the analysis stage: plain-text root cause + fix approach, never a diff. */
    static final String ANALYSIS_SYSTEM_PROMPT =
            "You are an expert MQL5 (MetaQuotes Language 5) code analyst specializing in trading EA " +
                    "safety, performance, and best practices. Analyze the given code problem and reply " +
                    "with a concise plain-text explanation, in a few sentences, of the ROOT CAUSE of the " +
                    "problem and the RECOMMENDED FIX APPROACH. Focus on why the problem matters for live " +
                    "trading safety and its potential impact. Do NOT output a diff, patch, or code fences — " +
                    "reply with prose only.";

    private final String model;
    private final String configuredCliPath;

    /**
     * @param model             the Claude model id or alias passed via {@code --model}.
     * @param configuredCliPath explicit path to the {@code claude} binary from settings;
     *                          blank/null means auto-detect.
     */
    public ClaudeCliInsightClient(@NotNull String model, @Nullable String configuredCliPath) {
        this.model = model;
        this.configuredCliPath = configuredCliPath;
    }

    @Override
    @Nullable
    public String analyzeProblems(@NotNull ProblemRecord problem, @Nullable String codeContext) {
        String user = GrokClient.buildPrompt(problem, codeContext);
        String out = ClaudeCliClient.runClaudePrompt(model, configuredCliPath, ANALYSIS_SYSTEM_PROMPT, user);
        if (out == null) {
            return null;
        }
        String trimmed = out.trim();
        return trimmed.isBlank() ? null : trimmed;
    }
}
