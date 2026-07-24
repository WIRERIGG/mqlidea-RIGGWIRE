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
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * Loads {@code mql/doc/mql5-stdlib.json} (committed by the one-off {@code tools.GenerateStdlibCatalog}
 * generator, REVAMP_PLAN.md Phase 6 deliverable 2) and exposes the MQL5 Standard Library class/method
 * catalog -- the CTrade, CArray family, CPositionInfo (etc.) gap the Phase 4/5 reviews flagged as missing.
 */
public final class StdLibCatalog {

    private static final Logger log = Logger.getInstance(StdLibCatalog.class);
    private static final String RESOURCE = "mql/doc/mql5-stdlib.json";

    private static volatile Map<String, StdLibClass> byName;

    private StdLibCatalog() {
    }

    @NotNull
    private static Map<String, StdLibClass> ensureLoaded() {
        Map<String, StdLibClass> loaded = byName;
        if (loaded != null) {
            return loaded;
        }
        synchronized (StdLibCatalog.class) {
            if (byName != null) {
                return byName;
            }
            Map<String, StdLibClass> map = new HashMap<>();
            ClassLoader loader = StdLibCatalog.class.getClassLoader();
            try (Reader reader = new InputStreamReader(
                    Objects.requireNonNull(loader.getResourceAsStream(RESOURCE)), StandardCharsets.UTF_8)) {
                Gson gson = new Gson();
                List<StdLibClass> entries = gson.fromJson(reader, new TypeToken<List<StdLibClass>>() {
                }.getType());
                for (StdLibClass entry : entries) {
                    map.put(entry.name, entry);
                }
            } catch (Exception e) {
                log.warn("Error loading Standard Library catalog: " + RESOURCE, e);
            }
            byName = map;
            return map;
        }
    }

    @Nullable
    public static StdLibClass get(@NotNull String className) {
        return ensureLoaded().get(className);
    }

    @NotNull
    public static Map<String, StdLibClass> all() {
        return Collections.unmodifiableMap(ensureLoaded());
    }

    /**
     * All methods visible on {@code className}, including those inherited from public base
     * classes (walking {@link StdLibClass#parent} up to the root), own methods first, most
     * specific declaration winning on a name clash.
     */
    @NotNull
    public static List<StdLibMethod> methodsIncludingInherited(@NotNull String className) {
        List<StdLibMethod> result = new ArrayList<>();
        Set<String> seenNames = new LinkedHashSet<>();
        Set<String> visitedClasses = new LinkedHashSet<>();
        String current = className;
        while (current != null && visitedClasses.add(current)) {
            StdLibClass cls = get(current);
            if (cls == null || cls.methods == null) {
                break;
            }
            for (StdLibMethod m : cls.methods) {
                if (m.isConstructor) {
                    continue; // a base class's constructor is never inherited
                }
                if (seenNames.add(m.name)) {
                    result.add(m);
                }
            }
            current = cls.parent;
        }
        return result;
    }
}
