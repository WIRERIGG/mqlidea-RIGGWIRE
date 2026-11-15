/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import com.intellij.psi.PsiFile;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * The {@code input}/{@code sinput} parameters an EA compiles with (its own and its includes'), name
 * to declared type, or null when that can't be known for certain: an include doesn't resolve, or a
 * line declares several inputs.
 */
public final class EaInputs {

    private static final Pattern INPUT = Pattern.compile(
            "(?m)^[ \\t]*(?:input|sinput)\\s+(?!group\\b)(?:const\\s+)?(\\w+)\\s+(\\w+)\\s*(=[^;]*)?;");
    private static final Pattern ANY_INPUT = Pattern.compile("(?m)^[ \\t]*(?:input|sinput)\\s+(?!group\\b)");

    private EaInputs() {
    }

    @Nullable
    public static Map<String, String> of(@NotNull PsiFile ea) {
        return CachedValuesManager.getCachedValue(ea, () -> CachedValueProvider.Result.create(compute(ea),
                PsiModificationTracker.MODIFICATION_COUNT));
    }

    @Nullable
    private static Map<String, String> compute(@NotNull PsiFile ea) {
        Map<String, String> inputs = new LinkedHashMap<>();
        java.util.Set<PsiFile> visited = new java.util.LinkedHashSet<>();
        java.util.Deque<PsiFile> queue = new java.util.ArrayDeque<>();
        visited.add(ea);
        queue.add(ea);
        while (!queue.isEmpty()) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            PsiFile f = queue.poll();
            String code = SourceText.code(f.getViewProvider().getContents());
            int declared = 0;
            for (Matcher any = ANY_INPUT.matcher(code); any.find(); ) {
                declared++;
            }
            int parsed = 0;
            for (Matcher m = INPUT.matcher(code); m.find(); ) {
                if (m.group(3) != null && topLevelComma(m.group(3))) {
                    return null; // input int a = 1, b = 2;
                }
                inputs.putIfAbsent(m.group(2), m.group(1));
                parsed++;
            }
            if (parsed != declared) {
                return null; // input int a = 1, b = 2; or a form this reader doesn't know
            }
            for (com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock include
                    : com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(f, com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock.class)) {
                PsiFile target = include.resolveIncludedFile();
                if (target == null) {
                    return null; // an unresolved include may declare inputs
                }
                if (visited.add(target)) {
                    queue.add(target);
                }
            }
        }
        return inputs;
    }

    private static boolean topLevelComma(@NotNull String initializer) {
        int depth = 0;
        for (int i = 0; i < initializer.length(); i++) {
            char c = initializer.charAt(i);
            if (c == '(' || c == '{' || c == '[') {
                depth++;
            } else if (c == ')' || c == '}' || c == ']') {
                depth--;
            } else if (c == ',' && depth == 0) {
                return true;
            }
        }
        return false;
    }

    /** Why {@code value} can't be the value of an input of {@code type}, or null when it can (or the type isn't checked). */
    @Nullable
    public static String badValue(@NotNull String type, @NotNull String value) {
        switch (type) {
            case "bool":
                return value.matches("(?i)true|false|0|1") ? null : "not true or false";
            case "int", "long", "short", "char", "uint", "ulong", "ushort", "uchar":
                return value.matches("-?\\d+") ? null : "not a whole number";
            case "double", "float":
                return value.matches("-?(\\d+\\.?\\d*|\\.\\d+)([eE][-+]?\\d+)?") ? null : "not a number";
            default:
                return null; // string, datetime, color and enums take many spellings
        }
    }
}
