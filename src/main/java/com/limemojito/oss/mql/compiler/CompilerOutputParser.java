/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Parses a MetaEditor compile log into structured {@link CompilerDiagnostic}s. Pure and side-effect
 * free so it can be unit-tested against real log fixtures.
 *
 * <p>MetaEditor lines look like:</p>
 * <pre>
 *   MyExpert.mq5(12,5) : error 100: 'x' - some undeclared identifier
 *   MyExpert.mq5(20,10) : warning 43: declaration of 'y' hides a global declaration
 *   MyExpert.mq5 : information: compiling 'MyExpert.mq5'
 *   Result: 1 error(s), 1 warning(s), ...
 * </pre>
 * <p>The numeric code is optional (some builds emit {@code : error : text}); both forms are handled.
 * The {@code Result:} trailer is parsed separately via {@link #parseSummary(String)}.</p>
 */
public final class CompilerOutputParser {

    // file(line,col) : severity [code] : message      (code optional)
    private static final Pattern LOCATED = Pattern.compile(
            "^\\s*(.+?)\\((\\d+),(\\d+)\\)\\s*:\\s*(error|warning|information)\\b\\s*(\\d+)?\\s*:?\\s*(.*\\S)\\s*$",
            Pattern.CASE_INSENSITIVE);

    // file : information: message   (no location — e.g. "compiling ...")
    private static final Pattern FILE_LEVEL = Pattern.compile(
            "^\\s*(.+?)\\s*:\\s*(error|warning|information)\\b\\s*(\\d+)?\\s*:\\s*(.*\\S)\\s*$",
            Pattern.CASE_INSENSITIVE);

    // Result: N error(s), M warning(s), ...
    private static final Pattern SUMMARY = Pattern.compile(
            "^\\s*Result:\\s*(\\d+)\\s*error.*?(\\d+)\\s*warning", Pattern.CASE_INSENSITIVE);

    private CompilerOutputParser() {
    }

    /** Parses all located and file-level diagnostics from a full compile log. Never returns null. */
    @NotNull
    public static List<CompilerDiagnostic> parse(@Nullable String log) {
        List<CompilerDiagnostic> out = new ArrayList<>();
        if (log == null || log.isBlank()) {
            return out;
        }
        for (String raw : log.split("\\R")) {
            String line = raw.strip();
            if (line.isEmpty()) {
                continue;
            }
            Matcher m = LOCATED.matcher(line);
            if (m.matches()) {
                out.add(new CompilerDiagnostic(fileName(m.group(1)),
                        Integer.parseInt(m.group(2)), Integer.parseInt(m.group(3)),
                        severity(m.group(4)), m.group(5), m.group(6)));
                continue;
            }
            m = FILE_LEVEL.matcher(line);
            if (m.matches()) {
                out.add(new CompilerDiagnostic(fileName(m.group(1)), 0, 0,
                        severity(m.group(2)), m.group(3), m.group(4)));
            }
            // anything else (banners, blank lines, the Result: trailer) is ignored here
        }
        return out;
    }

    /** Extracts {@code (errors, warnings)} from a {@code Result:} line if present, else null. */
    @Nullable
    public static int[] parseSummary(@Nullable String log) {
        if (log == null) {
            return null;
        }
        for (String raw : log.split("\\R")) {
            Matcher m = SUMMARY.matcher(raw.strip());
            if (m.find()) {
                return new int[]{Integer.parseInt(m.group(1)), Integer.parseInt(m.group(2))};
            }
        }
        return null;
    }

    @NotNull
    private static CompilerDiagnostic.Severity severity(@NotNull String s) {
        return switch (s.toLowerCase()) {
            case "error" -> CompilerDiagnostic.Severity.ERROR;
            case "warning" -> CompilerDiagnostic.Severity.WARNING;
            default -> CompilerDiagnostic.Severity.INFORMATION;
        };
    }

    /** Reduces a path MetaEditor may print (with \\ or /) to its bare file name for matching. */
    @NotNull
    private static String fileName(@NotNull String path) {
        String p = path.trim();
        int slash = Math.max(p.lastIndexOf('\\'), p.lastIndexOf('/'));
        return slash >= 0 ? p.substring(slash + 1) : p;
    }
}
