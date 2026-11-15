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
 * Built-in names the bundled doc catalog lacks, each confirmed one by one in MetaEditor's MQL5
 * compiler. Candidates came from MetaEditor's own symbol table.
 * <ul>
 *     <li>{@code mql5-builtin-functions.json}: functions ({@code CalendarValueHistory},
 *     {@code CLContextCreate}, ...). A bare {@code Name();} compiled clean or gave "wrong
 *     parameters count", never "undeclared identifier".</li>
 *     <li>{@code mql5-builtin-names.json}: constants, enum types and predefined variables
 *     ({@code _Symbol}, {@code ENUM_TIMEFRAMES}, {@code INDICATOR_DATA}, ...). {@code Print(Name);}
 *     gave no "undeclared identifier".</li>
 *     <li>{@code mql4-only-functions.json}: catalog functions MQL5 doesn't have ({@code OrderLots},
 *     {@code TimeHour}, ...). {@code Name();} gave "undeclared identifier".</li>
 * </ul>
 */
public final class MqlBuiltinFunctions {

    private static final Set<String> FUNCTIONS = load("mql5-builtin-functions.json");
    private static final Set<String> NAMES = load("mql5-builtin-names.json");
    private static final Set<String> MQL4_ONLY = load("mql4-only-functions.json");

    private MqlBuiltinFunctions() {
    }

    public static boolean contains(@NotNull String name) {
        return FUNCTIONS.contains(name);
    }

    /** A built-in constant, enum type or predefined variable missing from the doc catalog. */
    public static boolean isBuiltinName(@NotNull String name) {
        return NAMES.contains(name) || FUNCTIONS.contains(name);
    }

    public static boolean isMql4Only(@NotNull String name) {
        return MQL4_ONLY.contains(name);
    }

    private static Set<String> load(@NotNull String resource) {
        try (InputStream in = MqlBuiltinFunctions.class.getResourceAsStream("/mql/doc/" + resource)) {
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
