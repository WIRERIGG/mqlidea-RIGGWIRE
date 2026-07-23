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

public final class GrokClient implements InsightGenerator {

    private static final Logger LOG = Logger.getInstance(GrokClient.class);
    private static final String API_URL = "https://api.x.ai/v1/chat/completions";
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    private static final Gson GSON = new Gson();

    private final OkHttpClient httpClient;
    private final String model;

    public GrokClient(@NotNull String model) {
        this.model = model;
        this.httpClient = new OkHttpClient.Builder()
                .connectTimeout(Duration.ofSeconds(30))
                .readTimeout(Duration.ofSeconds(60))
                .writeTimeout(Duration.ofSeconds(30))
                .build();
    }

    @Override
    @Nullable
    public String analyzeProblems(@NotNull ProblemRecord problem, @Nullable String codeContext) {
        String apiKey = ApiKeyStorage.getApiKey(ApiKeyStorage.GROK_KEY);
        if (apiKey == null || apiKey.isBlank()) {
            LOG.info("Grok API key not configured — skipping analysis");
            return null;
        }

        String prompt = buildPrompt(problem, codeContext);

        JsonObject requestBody = new JsonObject();
        requestBody.addProperty("model", model);
        requestBody.addProperty("temperature", 0.3);
        requestBody.addProperty("max_tokens", 1024);

        JsonArray messages = new JsonArray();
        JsonObject systemMsg = new JsonObject();
        systemMsg.addProperty("role", "system");
        systemMsg.addProperty("content",
                "You are an expert MQL5 (MetaQuotes Language 5) code analyst specializing in " +
                        "trading EA safety, performance, and best practices. Provide concise, actionable " +
                        "insights about code problems. Focus on WHY the problem matters for trading safety " +
                        "and what specific impact it could have in live trading.");
        messages.add(systemMsg);

        JsonObject userMsg = new JsonObject();
        userMsg.addProperty("role", "user");
        userMsg.addProperty("content", prompt);
        messages.add(userMsg);

        requestBody.add("messages", messages);

        RequestBody body = RequestBody.create(GSON.toJson(requestBody), JSON);
        Request request = new Request.Builder()
                .url(API_URL)
                .addHeader("Authorization", "Bearer " + apiKey)
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build();

        try (Response response = httpClient.newCall(request).execute()) {
            if (!response.isSuccessful()) {
                int code = response.code();
                if (code == 429) {
                    LOG.info("Grok rate limited — will retry later");
                    return null;
                }
                LOG.warn("Grok API error: " + code);
                return null;
            }

            String responseBody = response.body() != null ? response.body().string() : "";
            try {
                JsonObject json = GSON.fromJson(responseBody, JsonObject.class);
                if (json == null) {
                    LOG.warn("Grok API returned an empty response body");
                    return null;
                }
                JsonArray choices = json.getAsJsonArray("choices");
                if (choices != null && !choices.isEmpty()) {
                    JsonObject message = choices.get(0).getAsJsonObject().getAsJsonObject("message");
                    JsonElement content = message != null ? message.get("content") : null;
                    if (content != null && !content.isJsonNull()) {
                        return content.getAsString();
                    }
                }
                LOG.warn("Grok API response missing expected content");
            } catch (RuntimeException e) {
                // Malformed JSON (JsonSyntaxException etc.) — treat as a normal failure
                LOG.warn("Failed to parse Grok API response", e);
            }
        } catch (IOException e) {
            LOG.warn("Grok API request failed", e);
        }

        return null;
    }

    @NotNull
    static String buildPrompt(@NotNull ProblemRecord problem, @Nullable String codeContext) {
        StringBuilder sb = new StringBuilder();
        sb.append("Analyze this MQL5 code problem:\n\n");
        sb.append("**File:** ").append(problem.filePath()).append("\n");
        sb.append("**Line:** ").append(problem.line()).append("\n");
        sb.append("**Severity:** ").append(problem.severity()).append("\n");
        sb.append("**Inspection:** ").append(problem.inspectionName()).append("\n");
        sb.append("**Message:** ").append(problem.message()).append("\n");
        if (problem.fixHint() != null) {
            sb.append("**Suggested Fix:** ").append(problem.fixHint()).append("\n");
        }
        if (codeContext != null && !codeContext.isBlank()) {
            sb.append("\n**Code Context (surrounding lines):**\n```mql5\n");
            sb.append(codeContext);
            sb.append("\n```\n");
        }
        sb.append("\nProvide:\n");
        sb.append("1. A brief explanation of why this problem is dangerous in live trading\n");
        sb.append("2. The specific risk (e.g., financial loss, data corruption, crash)\n");
        sb.append("3. A recommended fix approach\n");
        return sb.toString();
    }
}
