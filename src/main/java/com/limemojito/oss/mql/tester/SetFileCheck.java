/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * A {@code .set} file against the EA it's for. MetaTrader skips a name the EA doesn't declare
 * without a word and runs that input at its default, so a typo silently tests something else.
 */
public final class SetFileCheck {

    /** MetaTrader's header line: {@code ; this file contains input parameters for testing/optimizing X expert advisor}. */
    private static final Pattern HEADER_EA = Pattern.compile(
            "(?im)^\\s*;.*\\bfor\\s+(?:testing/optimizing|testing|optimizing)\\s+(\\S+?)(?:\\.ex5)?\\s+expert\\s+advisor");

    public record Result(@NotNull List<String> unknown, @NotNull List<String> badValues) {
        public boolean isEmpty() {
            return unknown.isEmpty() && badValues.isEmpty();
        }
    }

    private SetFileCheck() {
    }

    /**
     * The EA a {@code .set} belongs to, as an {@code .mq5} base name among {@code eaNames}: the one its
     * MetaTrader header names, else the longest EA name its file name starts with; null when unsure.
     */
    @Nullable
    public static String eaFor(@NotNull String setFileName, @NotNull String text, @NotNull Collection<String> eaNames) {
        Matcher header = HEADER_EA.matcher(text);
        if (header.find()) {
            String named = header.group(1);
            for (String ea : eaNames) {
                if (ea.equalsIgnoreCase(named)) {
                    return ea;
                }
            }
            return null; // it names an EA this project doesn't have
        }
        String base = setFileName.replaceFirst("(?i)\\.set$", "").toLowerCase(Locale.ROOT);
        String best = null;
        boolean tie = false;
        for (String ea : eaNames) {
            String e = ea.toLowerCase(Locale.ROOT);
            boolean fits = base.equals(e) || base.startsWith(e) && !Character.isLetterOrDigit(base.charAt(e.length()));
            if (!fits) {
                continue;
            }
            if (best == null || ea.length() > best.length()) {
                best = ea;
                tie = false;
            } else if (ea.length() == best.length()) {
                tie = true;
            }
        }
        return tie ? null : best;
    }

    @NotNull
    public static Result check(@NotNull String text, @NotNull Map<String, String> inputs) {
        List<String> unknown = new ArrayList<>();
        List<String> bad = new ArrayList<>();
        for (TesterInputs.Entry e : TesterInputs.entries(text)) {
            String type = inputs.get(e.name());
            if (type == null) {
                unknown.add(e.name());
                continue;
            }
            String why = EaInputs.badValue(type, e.value());
            if (why != null) {
                bad.add(e.name() + "=" + e.value() + " (" + type + ": " + why + ")");
            }
        }
        return new Result(unknown, bad);
    }
}
