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
 * A provider that turns an inspection problem (plus Grok's analysis and the surrounding code)
 * into a unified diff. Implemented by {@link ClaudeClient} (Anthropic API over HTTP) and
 * {@link ClaudeCliClient} (headless Claude Code via {@code claude -p}).
 */
public interface ClaudeFixGenerator {

    /**
     * @param contextStartLine the 1-based absolute file line at which {@code codeContext} begins;
     *                         the model is instructed to emit hunk headers with absolute line numbers.
     * @return a unified diff that fixes the problem, or {@code null} if no fix could be generated.
     */
    @Nullable
    String generateFix(@NotNull ProblemRecord problem, @NotNull String grokInsight,
                       @NotNull String codeContext, int contextStartLine);
}
