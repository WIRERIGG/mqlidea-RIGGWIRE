/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.ai;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public final class DiffParser {

    private static final Pattern HUNK_HEADER = Pattern.compile(
            "^@@ -(\\d+)(?:,(\\d+))? \\+(\\d+)(?:,(\\d+))? @@");

    private DiffParser() {
    }

    @Nullable
    public static DiffPatch parse(@NotNull String diffText) {
        String[] lines = diffText.split("\n");
        if (lines.length < 3) return null;

        String filePath = null;
        List<Hunk> hunks = new ArrayList<>();

        int i = 0;
        // Find file headers
        while (i < lines.length) {
            if (lines[i].startsWith("--- ")) {
                i++;
                if (i < lines.length && lines[i].startsWith("+++ ")) {
                    filePath = lines[i].substring(4).trim();
                    if (filePath.startsWith("b/")) {
                        filePath = filePath.substring(2);
                    }
                    i++;
                    break;
                }
            }
            i++;
        }

        if (filePath == null) return null;

        // Parse hunks
        while (i < lines.length) {
            if (lines[i].startsWith("@@ ")) {
                Matcher m = HUNK_HEADER.matcher(lines[i]);
                if (m.find()) {
                    int oldStart = Integer.parseInt(m.group(1));
                    int oldCount = m.group(2) != null ? Integer.parseInt(m.group(2)) : 1;
                    int newStart = Integer.parseInt(m.group(3));
                    int newCount = m.group(4) != null ? Integer.parseInt(m.group(4)) : 1;

                    List<String> hunkLines = new ArrayList<>();
                    i++;
                    while (i < lines.length && !lines[i].startsWith("@@ ")
                            && !lines[i].startsWith("--- ")) {
                        hunkLines.add(lines[i]);
                        i++;
                    }
                    hunks.add(new Hunk(oldStart, oldCount, newStart, newCount, hunkLines));
                    continue;
                }
            }
            i++;
        }

        return hunks.isEmpty() ? null : new DiffPatch(filePath, hunks);
    }

    public record DiffPatch(@NotNull String filePath, @NotNull List<Hunk> hunks) {
    }

    public record Hunk(int oldStart, int oldCount, int newStart, int newCount,
                        @NotNull List<String> lines) {

        @NotNull
        public List<String> getRemovedLines() {
            return lines.stream()
                    .filter(l -> l.startsWith("-"))
                    .map(l -> l.substring(1))
                    .toList();
        }

        @NotNull
        public List<String> getAddedLines() {
            return lines.stream()
                    .filter(l -> l.startsWith("+"))
                    .map(l -> l.substring(1))
                    .toList();
        }

        @NotNull
        public List<String> getContextLines() {
            return lines.stream()
                    .filter(l -> l.startsWith(" "))
                    .map(l -> l.substring(1))
                    .toList();
        }
    }
}
