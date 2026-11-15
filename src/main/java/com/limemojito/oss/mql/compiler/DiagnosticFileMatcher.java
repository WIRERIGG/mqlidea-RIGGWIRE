/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;

/**
 * Decides which compiler diagnostics belong to a given file. MetaEditor attributes every diagnostic
 * to the file it occurred in, which for a program's compile includes each {@code #include}d header,
 * printed relative to the terminal data folder ({@code MQL5\Experts\X\Y.mqh}) or as an absolute path.
 *
 * <p>A diagnostic belongs to a file when its printed path is a path-suffix of the file's path (or the
 * other way round for an absolute Wine path such as {@code Z:\home\me\Y.mqh}). Matching on the bare
 * file name alone is unsafe for headers: {@code Trade.mqh}, {@code Utils.mqh} etc. commonly exist in
 * several folders, and the wrong one would be painted with another file's errors. The bare-name
 * fallback is therefore only allowed for the compiled program itself, and only when the name is
 * unambiguous within the log.</p>
 */
public final class DiagnosticFileMatcher {

    private DiagnosticFileMatcher() {
    }

    /**
     * The diagnostics in {@code all} that belong to the file known by {@code filePaths} (its path,
     * plus e.g. its canonical path when it is reached through a symlink).
     *
     * @param allowNameFallback when no diagnostic path-matches, accept diagnostics whose bare name
     *                          equals the file's, provided the log prints that name under exactly one
     *                          path. Only safe for the file that was itself compiled.
     */
    @NotNull
    public static List<CompilerDiagnostic> forFile(@NotNull List<CompilerDiagnostic> all,
                                                   @NotNull Collection<String> filePaths,
                                                   boolean allowNameFallback) {
        List<String> targets = new ArrayList<>();
        for (String p : filePaths) {
            if (p != null && !p.isBlank()) {
                targets.add(normalize(p));
            }
        }
        if (targets.isEmpty()) {
            return List.of();
        }
        List<CompilerDiagnostic> matched = new ArrayList<>();
        for (CompilerDiagnostic d : all) {
            if (pathMatches(normalize(d.path()), targets)) {
                matched.add(d);
            }
        }
        if (!matched.isEmpty() || !allowNameFallback) {
            return matched;
        }
        String name = baseName(targets.get(0));
        Set<String> distinctPaths = new HashSet<>();
        for (CompilerDiagnostic d : all) {
            if (name.equals(d.fileName().toLowerCase(Locale.ROOT))) {
                matched.add(d);
                distinctPaths.add(normalize(d.path()));
            }
        }
        return distinctPaths.size() <= 1 ? matched : List.of();
    }

    /** True when the diagnostic path {@code logPath} (normalized) names one of {@code targets}. */
    private static boolean pathMatches(@NotNull String logPath, @NotNull List<String> targets) {
        if (logPath.isEmpty()) {
            return false;
        }
        boolean bare = logPath.indexOf('/') < 0;
        for (String target : targets) {
            if (bare) {
                // A bare name carries no folder, so it identifies nothing beyond the name; the
                // caller's name fallback decides whether that is good enough.
                continue;
            }
            if (target.equals(logPath) || target.endsWith("/" + logPath)
                    || (target.startsWith("/") && logPath.endsWith(target))) {
                return true;
            }
        }
        return false;
    }

    @NotNull
    static String normalize(@Nullable String path) {
        if (path == null) {
            return "";
        }
        String p = path.trim().replace('\\', '/').toLowerCase(Locale.ROOT);
        while (p.startsWith("./")) {
            p = p.substring(2);
        }
        return p;
    }

    @NotNull
    private static String baseName(@NotNull String normalizedPath) {
        int slash = normalizedPath.lastIndexOf('/');
        return slash >= 0 ? normalizedPath.substring(slash + 1) : normalizedPath;
    }
}
