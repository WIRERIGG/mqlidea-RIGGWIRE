/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Flags a function that grows the same array with a plain 2-arg {@code ArrayResize(array, n + 1)}
 * more than twice: the repeated-reallocation antipattern the message describes. Only growth counts:
 * a new size written with {@code +}, or a literal larger than the one before it in the same block. Clearing to 0, shrinking and resizing to a fixed size don't, and
 * nor do resizes of different arrays or a 3-arg call, which already reserves
 * ({@code ArrayResize(array, new_size, reserve_size)}, see arrayresize.html). Growth inside a loop
 * is {@link ArrayResizeInLoopInspection}'s.
 */
public class MissingArrayPreallocationInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "The same array grows by repeated ArrayResize() calls — use the reserve parameter to pre-allocate";

    private static final Set<String> ARRAY_RESIZE_NAMES = Set.of("ArrayResize");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                Map<String, Integer> growthsPerArray = new HashMap<>();
                // last literal size per array, per statement list it was set in
                Map<String, Long> lastLiteral = new HashMap<>();
                StatementAst.forEachCall(body, ARRAY_RESIZE_NAMES, callId -> {
                    if (StatementAst.callArgCount(callId) >= 3) return;
                    String array = StatementAst.nthCallArg(callId, 0);
                    String size = StatementAst.nthCallArg(callId, 1);
                    if (array == null || size == null) return;
                    String key = array.replaceAll("\\s", "");
                    if (size.contains("+")) {
                        growthsPerArray.merge(key, 1, Integer::sum);
                    } else {
                        // the first size of a growing literal chain is an allocation of its own too
                        growthsPerArray.merge(key, growsFromLiteral(callId, key, size.strip(), lastLiteral), Integer::sum);
                    }
                });
                if (growthsPerArray.values().stream().anyMatch(n -> n > 2)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * How many resizes {@code call} adds to a growing chain: 1 when {@code size} is a literal larger
     * than the last literal size given to the same array in the same statement list, 2 for the first
     * such step (counting the resize it grew from), 0 otherwise. {@code ArrayResize(a, 1); ArrayResize(a, 2);}
     * grows; resizes on different branches of an {@code if}/{@code else} sit in different lists, so
     * only one of them runs.
     */
    private static int growsFromLiteral(@NotNull ASTNode call, @NotNull String array, @NotNull String size,
                                        @NotNull Map<String, Long> lastLiteral) {
        if (!size.matches("\\d{1,18}")) return 0;
        ASTNode statement = StatementAst.enclosingStatement(call);
        ASTNode list = statement == null ? null : statement.getTreeParent();
        String key = array + "@" + (list == null ? -1 : list.getStartOffset());
        long value = Long.parseLong(size);
        boolean chainStarted = lastLiteral.containsKey(key + "#grown");
        Long previous = lastLiteral.put(key, value);
        if (previous == null || previous >= value) return 0;
        lastLiteral.put(key + "#grown", 1L);
        return chainStarted ? 1 : 2;
    }
}
