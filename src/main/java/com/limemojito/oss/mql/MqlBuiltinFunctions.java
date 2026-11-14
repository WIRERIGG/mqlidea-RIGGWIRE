/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.google.gson.Gson;
import org.jetbrains.annotations.NotNull;

import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.Set;

/**
 * MQL5 built-in functions missing from the bundled doc catalog ({@code CalendarValueHistory},
 * {@code CLContextCreate}, ...). Each name in {@code mql/doc/mql5-builtin-functions.json} was
 * confirmed one by one in MetaEditor: a bare {@code Name();} compiled clean or gave
 * "wrong parameters count", never "undeclared identifier".
 */
public final class MqlBuiltinFunctions {

    private static final Set<String> NAMES = load();

    private MqlBuiltinFunctions() {
    }

    public static boolean contains(@NotNull String name) {
        return NAMES.contains(name);
    }

    private static Set<String> load() {
        try (InputStream in = MqlBuiltinFunctions.class.getResourceAsStream("/mql/doc/mql5-builtin-functions.json")) {
            if (in == null) {
                return Set.of();
            }
            String[] names = new Gson().fromJson(new InputStreamReader(in, StandardCharsets.UTF_8), String[].class);
            return Set.of(names);
        } catch (java.io.IOException e) {
            return Set.of();
        }
    }
}
