/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.intellij.openapi.diagnostic.Logger;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.IOException;
import java.time.Duration;

public final class ClaudeClient implements ClaudeFixGenerator {

    private static final Logger LOG = Logger.getInstance(ClaudeClient.class);
    private static final String API_URL = "https://api.anthropic.com/v1/messages";
    private static final String API_VERSION = "2023-06-01";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final Gson GSON = new Gson();

    private final OkHttpClient httpClient;
    private final String model;

    public ClaudeClient(@NotNull String model) {
        this.model = model;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(Duration.ofSeconds(30))
                .readTimeout(Duration.ofSeconds(120))
                .writeTimeout(Duration.ofSeconds(30))
                .build();
    }

    /**
     * @param contextStartLine the 1-based absolute file line at which {@code codeContext} begins;
     *                         Claude is instructed to emit hunk headers with absolute line numbers.
     */
    @Override
    @Nullable
    public String generateFix(@NotNull ProblemRecord problem, @Nullable String grokInsight,
                               @NotNull String codeContext, int contextStartLine) {
        String apiKey = ApiKeyStorage.getApiKey(ApiKeyStorage.CLAUDE_KEY);
        if (apiKey == null || apiKey.isBlank()) {
            LOG.info("Claude API key not configured — skipping fix generation");
            return null;
        }

        String prompt = buildPrompt(problem, grokInsight, codeContext, contextStartLine);

        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("model", model);
        requestBody.addProperty("max_tokens", 4096);

        JsonObject systemContent = new JsonObject();
        systemContent.addProperty("type", "text");
        systemContent.addProperty("text", systemPrompt(contextStartLine));

        JsonArray systemArr = new JsonArray();
        systemArr.add(systemContent);
        requestBody.add("system", systemArr);

        JsonArray messages = new JsonArray();
        JsonObject userMsg = new JsonObject();
        userMsg.addProperty("role", "user");

        JsonArray contentArr = new JsonArray();
        JsonObject textContent = new JsonObject();
        textContent.addProperty("type", "text");
        textContent.addProperty("text", prompt);
        contentArr.add(textContent);
        userMsg.add("content", contentArr);

        messages.add(userMsg);
        requestBody.add("messages", messages);

        RequestBody body = RequestBody.create(GSON.toJson(requestBody), JSON);
        Request request = new Request.Builder()
                .url(API_URL)
                .addHeader("x-api-key", apiKey)
                .addHeader("anthropic-version", API_VERSION)
                .addHeader("content-type", "application/json")
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                int code = response.code();
                if (code == 429) {
                    LOG.info("Claude rate limited — will retry later");
                    return null;
                }
                LOG.warn("Claude API error: " + code);
                return null;
            }

            String responseBody = response.body() != null ? response.body().string() : "";
            try {
                JsonObject json = GSON.fromJson(responseBody, JsonObject.class);
                if (json == null) {
                    LOG.warn("Claude API returned an empty response body");
                    return null;
                }
                JsonArray content = json.getAsJsonArray("content");
                if (content != null && !content.isEmpty()) {
                    JsonObject first = content.get(0).getAsJsonObject();
                    JsonElement type = first.get("type");
                    JsonElement text = first.get("text");
                    if (type != null && "text".equals(type.getAsString()) && text != null) {
                        return extractDiff(text.getAsString());
                    }
                }
                LOG.warn("Claude API response missing expected content");
            } catch (RuntimeException e) {
                // Malformed JSON (JsonSyntaxException etc.) — treat as a normal failure
                LOG.warn("Failed to parse Claude API response", e);
            }
        } catch (IOException e) {
            LOG.warn("Claude API request failed", e);
        }

        return null;
    }

    /**
     * The system prompt shared by both the HTTP client and the Claude Code CLI client.
     *
     * @param contextStartLine the 1-based absolute file line at which the code snippet begins.
     */
    @NotNull
    static String systemPrompt(int contextStartLine) {
        return "You are an expert MQL5 code refactoring assistant. Generate ONLY a unified diff " +
                "that fixes the specified problem. The diff must be valid and directly applicable. " +
                "Do not include explanations outside the diff. Use the standard unified diff format:\n" +
                "--- a/filepath\n+++ b/filepath\n@@ -line,count +line,count @@\n" +
                "The code snippet you receive is an excerpt of the file; it begins at file line " +
                contextStartLine + ". Emit @@ hunk headers using ABSOLUTE file line numbers, " +
                "not positions relative to the snippet. " +
                "Make minimal, focused changes. Preserve existing code style and indentation.";
    }

    /**
     * Builds the user prompt. When {@code grokInsight} is null/blank (single combined-call mode,
     * used by the Claude Code CLI path) the prompt instructs Claude to analyze the problem AND
     * produce the fix in one shot — root-cause reasoning stays internal, output is still ONLY
     * the unified diff. When an insight is present, today's two-phase wording is kept.
     */
    @NotNull
    static String buildPrompt(@NotNull ProblemRecord problem, @Nullable String grokInsight,
                                       @NotNull String codeContext, int contextStartLine) {
        boolean hasInsight = grokInsight != null && !grokInsight.isBlank();
        return "Fix this MQL5 code problem by generating a unified diff.\n\n" +
                "**File:** " + problem.filePath() + "\n" +
                "**Line:** " + problem.line() + "\n" +
                "**Severity:** " + problem.severity() + "\n" +
                "**Inspection:** " + problem.inspectionName() + "\n" +
                "**Message:** " + problem.message() + "\n" +
                (problem.fixHint() != null ? "**Fix Hint:** " + problem.fixHint() + "\n" : "") +
                (hasInsight
                        ? "\n**AI Analysis:**\n" + grokInsight + "\n"
                        : "\nNo prior analysis is available. Analyze the problem yourself AND produce the fix: " +
                          "determine the root cause, keep that reasoning internal, and output ONLY the unified diff.\n") +
                "\n**Code Context (snippet begins at file line " + contextStartLine + "):**\n```mql5\n" +
                codeContext + "\n```\n\n" +
                "Generate a unified diff to fix this problem. Output ONLY the diff, nothing else. " +
                "Remember: @@ hunk headers must use ABSOLUTE file line numbers.";
    }

    @NotNull
    static String extractDiff(@NotNull String response) {
        // Extract the diff block if wrapped in markdown code fences
        int diffStart = response.indexOf("--- ");
        if (diffStart < 0) {
            // Try to extract from code block
            int fenceStart = response.indexOf("```diff");
            if (fenceStart >= 0) {
                int contentStart = response.indexOf('\n', fenceStart) + 1;
                int fenceEnd = response.indexOf("```", contentStart);
                if (fenceEnd > contentStart) {
                    return response.substring(contentStart, fenceEnd).trim();
                }
            }
            fenceStart = response.indexOf("```");
            if (fenceStart >= 0) {
                int contentStart = response.indexOf('\n', fenceStart) + 1;
                int fenceEnd = response.indexOf("```", contentStart);
                if (fenceEnd > contentStart) {
                    return response.substring(contentStart, fenceEnd).trim();
                }
            }
            return stripTrailingFence(response.trim());
        }
        // Slice from the first diff header. Claude frequently wraps the whole reply in a
        // ```diff … ``` fence; slicing from "--- " leaves the CLOSING ``` attached, which
        // corrupts the patch (git apply chokes on the ``` line). Drop any trailing fence.
        return stripTrailingFence(response.substring(diffStart).trim());
    }

    /**
     * Removes a trailing markdown code fence (and anything after it) from an extracted diff.
     * A valid unified diff never contains a line beginning with {@code ```}, so cutting at the
     * first such marker is safe and strips the stray closing fence Claude emits when it wraps
     * its answer in ```diff … ```.
     */
    @NotNull
    private static String stripTrailingFence(@NotNull String diff) {
        int fence = diff.indexOf("\n```");
        if (fence >= 0) {
            diff = diff.substring(0, fence);
        }
        return diff.trim();
    }
}
