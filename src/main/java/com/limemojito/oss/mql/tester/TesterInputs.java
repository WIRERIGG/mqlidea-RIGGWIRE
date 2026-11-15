/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import org.jetbrains.annotations.NotNull;

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * An EA input file: a MetaTrader {@code .set} file ({@code Name=value||start||step||stop||Y}, often
 * UTF-16 with a byte-order mark, {@code ;} comments) or plain {@code Name=Value} lines. Both are
 * what the Strategy Tester's {@code [TesterInputs]} section takes, so the lines pass through as they
 * are; only the encoding and the comments go.
 */
public final class TesterInputs {

    private static final Pattern ENTRY = Pattern.compile("^\\s*([A-Za-z_]\\w*)\\s*=(.*)$");

    /** One input line: its name, the value before any {@code ||}, and the line itself. */
    public record Entry(@NotNull String name, @NotNull String value, @NotNull String line, int lineNumber) {
    }

    private TesterInputs() {
    }

    /** {@code bytes} as text: UTF-16LE/BE with a byte-order mark, else UTF-8 (a UTF-8 mark is dropped). */
    @NotNull
    public static String decode(@NotNull byte[] bytes) {
        if (bytes.length >= 2 && (bytes[0] & 0xFF) == 0xFF && (bytes[1] & 0xFF) == 0xFE) {
            return new String(bytes, 2, bytes.length - 2, StandardCharsets.UTF_16LE);
        }
        if (bytes.length >= 2 && (bytes[0] & 0xFF) == 0xFE && (bytes[1] & 0xFF) == 0xFF) {
            return new String(bytes, 2, bytes.length - 2, StandardCharsets.UTF_16BE);
        }
        int skip = bytes.length >= 3 && (bytes[0] & 0xFF) == 0xEF && (bytes[1] & 0xFF) == 0xBB && (bytes[2] & 0xFF) == 0xBF ? 3 : 0;
        return new String(bytes, skip, bytes.length - skip, StandardCharsets.UTF_8);
    }

    /** The input lines of {@code text}, in order; comments, blank lines and anything else are left out. */
    @NotNull
    public static List<Entry> entries(@NotNull String text) {
        List<Entry> out = new ArrayList<>();
        String[] lines = text.split("\\r?\\n", -1);
        for (int i = 0; i < lines.length; i++) {
            String line = lines[i];
            if (line.trim().startsWith(";")) {
                continue;
            }
            Matcher m = ENTRY.matcher(line);
            if (m.matches()) {
                String rest = m.group(2);
                int bars = rest.indexOf("||");
                out.add(new Entry(m.group(1), (bars < 0 ? rest : rest.substring(0, bars)).trim(), line.trim(), i + 1));
            }
        }
        return out;
    }

    /** The {@code [TesterInputs]} body for {@code text}: one input per line, UTF-8, last one wins per name. */
    @NotNull
    public static String testerSection(@NotNull String text) {
        Map<String, String> byName = new LinkedHashMap<>();
        for (Entry e : entries(text)) {
            byName.put(e.name(), e.line());
        }
        return String.join("\n", byName.values()) + (byName.isEmpty() ? "" : "\n");
    }
}
