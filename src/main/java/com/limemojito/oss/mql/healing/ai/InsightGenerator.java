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
 * The analysis stage of the healing pipeline: turns an inspection problem (plus surrounding code)
 * into a concise plain-text insight (root cause + recommended fix approach). Implemented by
 * {@link GrokClient} (xAI Grok over HTTP) and {@link ClaudeCliInsightClient} (headless Claude Code
 * via {@code claude -p}). The returned insight is stored in the healing DB and later handed to the
 * fix-generation stage.
 */
public interface InsightGenerator {

    /**
     * @param codeContext the surrounding source lines, or {@code null} if unavailable.
     * @return a concise plain-text analysis, or {@code null} if none could be produced.
     */
    @Nullable
    String analyzeProblems(@NotNull ProblemRecord problem, @Nullable String codeContext);
}
