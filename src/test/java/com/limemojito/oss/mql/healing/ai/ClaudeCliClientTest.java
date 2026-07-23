/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Unit tests for the CLI provider's binary resolution and the prompt pieces it reuses
 * from {@link ClaudeClient}. Never launches the real {@code claude} binary.
 */
class ClaudeCliClientTest {

    @Test
    void configuredExecutablePathWins(@TempDir Path tempDir) throws IOException {
        Path fakeClaude = tempDir.resolve("claude");
        Files.writeString(fakeClaude, "#!/bin/sh\nexit 0\n");
        assertThat(fakeClaude.toFile().setExecutable(true)).isTrue();

        assertThat(ClaudeCliClient.resolveClaudePath(fakeClaude.toString()))
                .isEqualTo(fakeClaude.toAbsolutePath().toString());
    }

    @Test
    void nonExecutableConfiguredPathIsNotUsed(@TempDir Path tempDir) throws IOException {
        Path notExecutable = tempDir.resolve("claude");
        Files.writeString(notExecutable, "not a binary");
        assertThat(notExecutable.toFile().setExecutable(false)).isTrue();

        // Falls through to auto-detect; whatever it finds, it must not be the configured path.
        assertThat(ClaudeCliClient.resolveClaudePath(notExecutable.toString()))
                .isNotEqualTo(notExecutable.toAbsolutePath().toString());
    }

    @Test
    void missingConfiguredPathIsNotUsed(@TempDir Path tempDir) {
        String missing = tempDir.resolve("does-not-exist").toString();
        assertThat(ClaudeCliClient.resolveClaudePath(missing)).isNotEqualTo(missing);
    }

    @Test
    void systemPromptCarriesAbsoluteLineInstruction() {
        String prompt = ClaudeClient.systemPrompt(42);
        assertThat(prompt)
                .contains("expert MQL5 code refactoring assistant")
                .contains("begins at file line 42")
                .contains("ABSOLUTE file line numbers")
                .contains("unified diff");
    }

    @Test
    void extractDiffHandlesBareDiff() {
        String response = "--- a/Expert.mq5\n+++ b/Expert.mq5\n@@ -1,1 +1,1 @@\n-old\n+new";
        assertThat(ClaudeClient.extractDiff(response)).isEqualTo(response);
    }

    @Test
    void extractDiffUnwrapsFencedDiff() {
        String diff = "@@ -3,1 +3,1 @@\n-foo\n+bar";
        String response = "Here you go:\n```diff\n" + diff + "\n```\nDone.";
        assertThat(ClaudeClient.extractDiff(response)).isEqualTo(diff);
    }

    @Test
    void analysisSystemPromptAsksForProseNotDiff() {
        assertThat(ClaudeCliInsightClient.ANALYSIS_SYSTEM_PROMPT)
                .contains("expert MQL5")
                .contains("ROOT CAUSE")
                .contains("RECOMMENDED FIX APPROACH")
                .contains("Do NOT output a diff");
    }
}
