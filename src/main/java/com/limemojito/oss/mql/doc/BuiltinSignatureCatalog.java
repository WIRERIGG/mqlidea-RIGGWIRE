/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.intellij.openapi.diagnostic.Logger;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

/**
 * Loads {@code mql/doc/mql4-signatures.json} (committed by the one-off
 * {@code tools.GenerateBuiltinSignatures} generator, REVAMP_PLAN.md Phase 6 deliverable 1) and
 * exposes it by function name for completion tail-text, param-info, and quick-doc.
 */
public final class BuiltinSignatureCatalog {

    private static final Logger log = Logger.getInstance(BuiltinSignatureCatalog.class);
    private static final String RESOURCE = "mql/doc/mql4-signatures.json";

    private static volatile Map<String, BuiltinSignature> byName;

    private BuiltinSignatureCatalog() {
    }

    @NotNull
    private static Map<String, BuiltinSignature> ensureLoaded() {
        Map<String, BuiltinSignature> loaded = byName;
        if (loaded != null) {
            return loaded;
        }
        synchronized (BuiltinSignatureCatalog.class) {
            if (byName != null) {
                return byName;
            }
            Map<String, BuiltinSignature> map = new HashMap<>();
            ClassLoader loader = BuiltinSignatureCatalog.class.getClassLoader();
            try (Reader reader = new InputStreamReader(
                    Objects.requireNonNull(loader.getResourceAsStream(RESOURCE)), StandardCharsets.UTF_8)) {
                Gson gson = new Gson();
                List<BuiltinSignature> entries = gson.fromJson(reader, new TypeToken<List<BuiltinSignature>>() {
                }.getType());
                for (BuiltinSignature entry : entries) {
                    map.put(entry.name, entry);
                }
            } catch (Exception e) {
                log.warn("Error loading built-in signature catalog: " + RESOURCE, e);
            }
            byName = map;
            return map;
        }
    }

    @Nullable
    public static BuiltinSignature get(@NotNull String functionName) {
        return ensureLoaded().get(functionName);
    }

    @NotNull
    public static Map<String, BuiltinSignature> all() {
        return Collections.unmodifiableMap(ensureLoaded());
    }
}
