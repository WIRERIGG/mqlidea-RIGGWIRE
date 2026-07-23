/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.FilenameIndex;
import org.jetbrains.annotations.NotNull;

/**
 * Central resolver for whether a file should be treated as MQL4 or MQL5.
 *
 * <p>Extension is authoritative for {@code .mq5}/{@code .mql5} and {@code .mq4}/{@code .mql4}. The hard
 * case is a {@code .mqh} header (or any other file), which carries no dialect in its name — it inherits
 * the dialect of the program that {@code #include}s it. Filename-only detection previously left
 * {@code .mqh} as neither dialect, so MQL4-only inspections (whose guard is
 * {@code if (isMql5Source(file)) return}) fired on MQL5 headers and offered MQL4-only advice
 * (e.g. {@code IsTradeContextBusy()}), which does not exist in MQL5.</p>
 *
 * <p>For headers we infer from the project's main sources: a project that contains {@code .mq4} sources
 * and no {@code .mq5} sources is MQL4; otherwise we default to MQL5 (the modern default, and the safe
 * choice — it suppresses dead MQL4-only advice rather than emitting it). Inference is best-effort and
 * never throws: any lookup failure (e.g. dumb mode) falls back to MQL5.</p>
 */
public final class MqlDialect {

    public enum Kind {MQL4, MQL5}

    private MqlDialect() {
    }

    /** True when {@code file} should be treated as MQL5 (includes {@code .mqh} unless the project is MQL4-only). */
    public static boolean isMql5(@NotNull PsiFile file) {
        return kind(file) == Kind.MQL5;
    }

    /** True when {@code file} should be treated as MQL4. */
    public static boolean isMql4(@NotNull PsiFile file) {
        return kind(file) == Kind.MQL4;
    }

    @NotNull
    public static Kind kind(@NotNull PsiFile file) {
        String n = file.getName().toLowerCase();
        if (n.endsWith(".mq5") || n.endsWith(".mql5")) {
            return Kind.MQL5;
        }
        if (n.endsWith(".mq4") || n.endsWith(".mql4")) {
            return Kind.MQL4;
        }
        return inferFromProject(file);
    }

    @NotNull
    private static Kind inferFromProject(@NotNull PsiFile file) {
        try {
            Project project = file.getProject();
            boolean hasMql5 = hasExt(project, "mq5") || hasExt(project, "mql5");
            boolean hasMql4 = hasExt(project, "mq4") || hasExt(project, "mql4");
            if (hasMql4 && !hasMql5) {
                return Kind.MQL4;
            }
        } catch (RuntimeException ignored) {
            // index not ready / no project scope — fall through to the safe default
        }
        return Kind.MQL5;
    }

    private static boolean hasExt(@NotNull Project project, @NotNull String ext) {
        return !FilenameIndex.getAllFilesByExt(project, ext).isEmpty();
    }
}
