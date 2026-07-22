/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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

public final class ClaudeClient {

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
    @Nullable
    public String generateFix(@NotNull ProblemRecord problem, @NotNull String grokInsight,
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
        systemContent.addProperty("text",
                "You are an expert MQL5 code refactoring assistant. Generate ONLY a unified diff " +
                        "that fixes the specified problem. The diff must be valid and directly applicable. " +
                        "Do not include explanations outside the diff. Use the standard unified diff format:\n" +
                        "--- a/filepath\n+++ b/filepath\n@@ -line,count +line,count @@\n" +
                        "The code snippet you receive is an excerpt of the file; it begins at file line " +
                        contextStartLine + ". Emit @@ hunk headers using ABSOLUTE file line numbers, " +
                        "not positions relative to the snippet. " +
                        "Make minimal, focused changes. Preserve existing code style and indentation.");

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

    @NotNull
    private static String buildPrompt(@NotNull ProblemRecord problem, @NotNull String grokInsight,
                                       @NotNull String codeContext, int contextStartLine) {
        return "Fix this MQL5 code problem by generating a unified diff.\n\n" +
                "**File:** " + problem.filePath() + "\n" +
                "**Line:** " + problem.line() + "\n" +
                "**Severity:** " + problem.severity() + "\n" +
                "**Inspection:** " + problem.inspectionName() + "\n" +
                "**Message:** " + problem.message() + "\n" +
                (problem.fixHint() != null ? "**Fix Hint:** " + problem.fixHint() + "\n" : "") +
                "\n**AI Analysis:**\n" + grokInsight + "\n" +
                "\n**Code Context (snippet begins at file line " + contextStartLine + "):**\n```mql5\n" +
                codeContext + "\n```\n\n" +
                "Generate a unified diff to fix this problem. Output ONLY the diff, nothing else. " +
                "Remember: @@ hunk headers must use ABSOLUTE file line numbers.";
    }

    @NotNull
    private static String extractDiff(@NotNull String response) {
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
            return response.trim();
        }
        return response.substring(diffStart).trim();
    }
}
