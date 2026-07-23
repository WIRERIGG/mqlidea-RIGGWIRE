/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import com.intellij.openapi.diagnostic.Logger;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.concurrent.TimeUnit;

/**
 * Generates unified-diff fixes by shelling out to the local Claude Code CLI
 * ({@code claude -p}, headless one-shot mode). Uses the user's existing Claude Code
 * login for auth — no Anthropic API key is required.
 *
 * <p>Reuses {@link ClaudeClient}'s system prompt, user prompt, and diff extraction so
 * both providers behave identically apart from transport.</p>
 *
 * <p>Runs on HealingService's pooled executor thread (off-EDT); never performs
 * read actions or touches the EDT.</p>
 */
public final class ClaudeCliClient implements ClaudeFixGenerator {

    private static final Logger LOG = Logger.getInstance(ClaudeCliClient.class);
    private static final long TIMEOUT_SECONDS = 180;
    private static final long SHELL_LOOKUP_TIMEOUT_SECONDS = 15;
    private static final int STDERR_SNIPPET_LENGTH = 500;

    private final String model;
    private final String configuredCliPath;

    /**
     * @param model             the Claude model id or alias passed via {@code --model}.
     * @param configuredCliPath explicit path to the {@code claude} binary from settings;
     *                          blank/null means auto-detect.
     */
    public ClaudeCliClient(@NotNull String model, @Nullable String configuredCliPath) {
        this.model = model;
        this.configuredCliPath = configuredCliPath;
    }

    @Override
    @Nullable
    public String generateFix(@NotNull ProblemRecord problem, @Nullable String grokInsight,
                              @NotNull String codeContext, int contextStartLine) {
        String system = ClaudeClient.systemPrompt(contextStartLine);
        String user = ClaudeClient.buildPrompt(problem, grokInsight, codeContext, contextStartLine);
        String out = runClaudePrompt(model, configuredCliPath, system, user);
        return out == null ? null : ClaudeClient.extractDiff(out);
    }

    /**
     * Runs {@code claude -p} one-shot: resolves the binary, builds the command, writes
     * {@code userPrompt} to stdin, drains stdout/stderr concurrently, waits with a timeout,
     * and returns trimmed stdout.
     *
     * <p>Shared by both healing stages (analysis and fix generation). Runs on a pooled
     * background thread; never performs read actions or touches the EDT.</p>
     *
     * @return trimmed stdout on success, or {@code null} on any failure, timeout,
     *         non-zero exit, or blank output.
     */
    @Nullable
    static String runClaudePrompt(@NotNull String model, @Nullable String configuredCliPath,
                                  @NotNull String systemPrompt, @NotNull String userPrompt) {
        String claudePath = resolveClaudePath(configuredCliPath);
        if (claudePath == null) {
            LOG.warn("Claude Code CLI not found (checked configured path, standard locations and login shell) "
                    + "— skipping this cycle");
            return null;
        }

        List<String> command = List.of(
                claudePath,
                "-p",
                "--output-format", "text",
                "--model", model,
                "--append-system-prompt", systemPrompt);

        ProcessBuilder builder = new ProcessBuilder(command);
        builder.redirectErrorStream(false);
        hardenEnvironment(builder);
        // Neutral working directory — avoid picking up a stray project CLAUDE.md.
        File home = new File(System.getProperty("user.home", System.getProperty("java.io.tmpdir", "/")));
        if (home.isDirectory()) {
            builder.directory(home);
        }

        try {
            Process process = builder.start();

            // Drain stdout and stderr concurrently to avoid pipe-buffer deadlock.
            StreamDrainer stdout = new StreamDrainer(process.getInputStream(), "MQL-Healing-claude-stdout");
            StreamDrainer stderr = new StreamDrainer(process.getErrorStream(), "MQL-Healing-claude-stderr");
            stdout.start();
            stderr.start();

            // Write the user prompt to stdin, then close it so the CLI runs one-shot.
            try (OutputStream stdin = process.getOutputStream()) {
                stdin.write(userPrompt.getBytes(StandardCharsets.UTF_8));
            }

            if (!process.waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                stdout.join(2000);
                stderr.join(2000);
                LOG.warn("claude -p timed out after " + TIMEOUT_SECONDS + "s — skipping this cycle");
                return null;
            }

            stdout.join(5000);
            stderr.join(5000);

            int exitCode = process.exitValue();
            if (exitCode != 0) {
                LOG.warn("claude -p exited with code " + exitCode + snippet(stderr.text()));
                return null;
            }

            String responseText = stdout.text().trim();
            if (responseText.isBlank()) {
                LOG.warn("claude -p produced no output" + snippet(stderr.text()));
                return null;
            }

            return responseText;
        } catch (IOException e) {
            LOG.warn("Failed to run claude -p", e);
            return null;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        }
    }

    /**
     * Resolves the {@code claude} binary: the configured path if it exists and is executable,
     * then well-known install locations, then a login-shell {@code command -v claude} lookup.
     *
     * @return absolute path to the binary, or {@code null} if not found.
     */
    @Nullable
    static String resolveClaudePath(@Nullable String configuredCliPath) {
        if (configuredCliPath != null && !configuredCliPath.isBlank()) {
            File configured = new File(configuredCliPath.trim());
            if (configured.isFile() && configured.canExecute()) {
                return configured.getAbsolutePath();
            }
        }

        String home = System.getProperty("user.home", "");
        String[] candidates = {
                home + "/.local/bin/claude",
                "/opt/homebrew/bin/claude",
                "/usr/local/bin/claude",
                "/usr/bin/claude",
                home + "/.claude/local/claude",
        };
        for (String candidate : candidates) {
            File file = new File(candidate);
            if (file.isFile() && file.canExecute()) {
                return file.getAbsolutePath();
            }
        }

        return loginShellLookup();
    }

    /**
     * Ensures the child process environment carries the identity variables macOS needs to
     * reach the Keychain-stored Claude Code login ({@code HOME}, {@code USER}, {@code LOGNAME}).
     * IDE-spawned processes can inherit a stripped environment missing these, which makes
     * {@code claude -p} fail with "Not logged in". Uses {@code putIfAbsent} so any real
     * values already present in the IDE's environment win.
     */
    private static void hardenEnvironment(@NotNull ProcessBuilder builder) {
        java.util.Map<String, String> env = builder.environment();
        String home = System.getProperty("user.home");
        String user = System.getProperty("user.name");
        if (home != null && !home.isBlank()) {
            env.putIfAbsent("HOME", home);
        }
        if (user != null && !user.isBlank()) {
            env.putIfAbsent("USER", user);
            env.putIfAbsent("LOGNAME", user);
        }
    }

    @Nullable
    private static String loginShellLookup() {
        try {
            ProcessBuilder builder = new ProcessBuilder("/bin/zsh", "-lc", "command -v claude");
            builder.redirectErrorStream(false);
            hardenEnvironment(builder);
            Process process = builder.start();
            StreamDrainer stdout = new StreamDrainer(process.getInputStream(), "MQL-Healing-claude-which-stdout");
            StreamDrainer stderr = new StreamDrainer(process.getErrorStream(), "MQL-Healing-claude-which-stderr");
            stdout.start();
            stderr.start();
            process.getOutputStream().close();

            if (!process.waitFor(SHELL_LOOKUP_TIMEOUT_SECONDS, TimeUnit.SECONDS)) {
                process.destroyForcibly();
                return null;
            }
            stdout.join(2000);
            stderr.join(2000);
            if (process.exitValue() != 0) {
                return null;
            }
            String path = stdout.text().trim();
            if (path.isEmpty()) {
                return null;
            }
            File file = new File(path);
            return (file.isFile() && file.canExecute()) ? file.getAbsolutePath() : null;
        } catch (IOException e) {
            LOG.info("Login-shell lookup for claude failed: " + e.getMessage());
            return null;
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            return null;
        }
    }

    @NotNull
    private static String snippet(@NotNull String stderr) {
        String trimmed = stderr.trim();
        if (trimmed.isEmpty()) {
            return "";
        }
        if (trimmed.length() > STDERR_SNIPPET_LENGTH) {
            trimmed = trimmed.substring(0, STDERR_SNIPPET_LENGTH) + "…";
        }
        return ": " + trimmed;
    }

    /** Background reader that fully drains a process stream into a buffer. */
    private static final class StreamDrainer extends Thread {

        private final InputStream in;
        private final ByteArrayOutputStream buffer = new ByteArrayOutputStream();

        StreamDrainer(@NotNull InputStream in, @NotNull String name) {
            super(name);
            this.in = in;
            setDaemon(true);
        }

        @Override
        public void run() {
            try (InputStream stream = in) {
                stream.transferTo(buffer);
            } catch (IOException ignored) {
                // Process was killed or stream closed — keep whatever was read.
            }
        }

        @NotNull
        String text() {
            // ByteArrayOutputStream.toString is synchronized; join() before calling for full output.
            return buffer.toString(StandardCharsets.UTF_8);
        }
    }
}
