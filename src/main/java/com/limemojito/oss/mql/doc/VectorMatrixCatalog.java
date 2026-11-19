/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.intellij.openapi.diagnostic.Logger;
import org.jetbrains.annotations.NotNull;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Objects;

/**
 * Member names of MQL5's built-in {@code vector}, {@code matrix} and {@code complex} types, from
 * {@code mql/doc/mql5-vector-matrix.json}. They have no {@code Include} header to scrape like the
 * Standard Library, so the list was checked name by name against MetaEditor.
 */
public final class VectorMatrixCatalog {

    private static final Logger log = Logger.getInstance(VectorMatrixCatalog.class);
    private static final String RESOURCE = "mql/doc/mql5-vector-matrix.json";

    /** Instance methods, static constructors and fields of one type family. */
    public record Members(@NotNull List<String> methods, @NotNull List<String> statics, @NotNull List<String> fields) {
        static final Members NONE = new Members(List.of(), List.of(), List.of());

        /** True when {@code name} is listed in any form: method, static constructor or field. */
        public boolean has(@NotNull String name) {
            return methods.contains(name) || statics.contains(name) || fields.contains(name);
        }

        public boolean isEmpty() {
            return methods.isEmpty() && statics.isEmpty() && fields.isEmpty();
        }
    }

    private VectorMatrixCatalog() {
    }

    /** The members of {@code typeName} ({@code vectorf} as {@code vector}, ...), or none for another type. */
    @NotNull
    public static Members of(@NotNull String typeName) {
        return switch (typeName) {
            case "vector", "vectorf", "vectorc" -> Holder.VECTOR;
            case "matrix", "matrixf", "matrixc" -> Holder.MATRIX;
            case "complex" -> Holder.COMPLEX;
            default -> Members.NONE;
        };
    }

    private static final class Holder {
        static final JsonObject ROOT = load();
        static final Members VECTOR = members("vector");
        static final Members MATRIX = members("matrix");
        static final Members COMPLEX = members("complex");

        private static JsonObject load() {
            try (Reader reader = new InputStreamReader(Objects.requireNonNull(
                    VectorMatrixCatalog.class.getClassLoader().getResourceAsStream(RESOURCE)), StandardCharsets.UTF_8)) {
                return JsonParser.parseReader(reader).getAsJsonObject();
            } catch (Exception e) {
                log.warn("Error loading vector/matrix catalog: " + RESOURCE, e);
                return new JsonObject();
            }
        }

        private static Members members(@NotNull String type) {
            JsonObject entry = ROOT.getAsJsonObject(type);
            return entry == null ? Members.NONE : new Members(names(entry, "methods"), names(entry, "static"), names(entry, "fields"));
        }

        private static List<String> names(@NotNull JsonObject entry, @NotNull String key) {
            return entry.has(key) ? entry.getAsJsonArray(key).asList().stream().map(e -> e.getAsString()).toList() : List.of();
        }
    }
}
