/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.intellij.openapi.diagnostic.Logger;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Fields and methods of MQL5's built-in structures ({@code MqlDateTime}, {@code MqlTradeRequest},
 * ...), from {@code mql/doc/mql5-structs.json}: names only, verified against MetaEditor.
 */
public final class StructCatalog {

    private static final Logger log = Logger.getInstance(StructCatalog.class);
    private static final String RESOURCE = "mql/doc/mql5-structs.json";

    /** The members of one built-in structure. */
    public record Members(@NotNull List<String> fields, @NotNull List<String> methods) {
        public boolean has(@NotNull String name) {
            return fields.contains(name) || methods.contains(name);
        }
    }

    private StructCatalog() {
    }

    /** The members of built-in structure {@code typeName}, or {@code null} if it isn't one. */
    @Nullable
    public static Members of(@Nullable String typeName) {
        return typeName == null ? null : Holder.STRUCTS.get(typeName);
    }

    private static final class Holder {
        static final Map<String, Members> STRUCTS = load();

        private static Map<String, Members> load() {
            Map<String, Members> out = new HashMap<>();
            try (Reader reader = new InputStreamReader(Objects.requireNonNull(
                    StructCatalog.class.getClassLoader().getResourceAsStream(RESOURCE)), StandardCharsets.UTF_8)) {
                JsonObject root = JsonParser.parseReader(reader).getAsJsonObject();
                for (Map.Entry<String, JsonElement> e : root.entrySet()) {
                    if (e.getValue().isJsonObject()) {
                        JsonObject entry = e.getValue().getAsJsonObject();
                        out.put(e.getKey(), new Members(names(entry, "fields"), names(entry, "methods")));
                    }
                }
            } catch (Exception e) {
                log.warn("Error loading built-in structure catalog: " + RESOURCE, e);
            }
            return Map.copyOf(out);
        }

        private static List<String> names(@NotNull JsonObject entry, @NotNull String key) {
            return entry.has(key) ? entry.getAsJsonArray(key).asList().stream().map(JsonElement::getAsString).toList() : List.of();
        }
    }
}
