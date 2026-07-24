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

import java.util.List;
import java.util.Set;

/**
 * Flags a function that calls the plain 2-arg {@code ArrayResize(array, new_size)} more than twice
 * — the repeated-reallocation antipattern the message describes. An {@code ArrayResize} call that
 * already supplies the 3rd (reserve) argument (TrendConfirmation.mqh:660/675 — the doc-endorsed
 * {@code ArrayResize(array, new_size, reserve_size)} pre-allocation form, see arrayresize.html) is
 * already pre-allocated and must not count toward the threshold, whichever array it targets.
 */
public class MissingArrayPreallocationInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Multiple incremental ArrayResize() calls — use reserve parameter for pre-allocation";

    private static final Set<String> ARRAY_RESIZE_NAMES = Set.of("ArrayResize");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                int[] unreservedCount = {0};
                StatementAst.forEachCall(body, ARRAY_RESIZE_NAMES, callId -> {
                    if (StatementAst.callArgCount(callId) < 3) {
                        unreservedCount[0]++;
                    }
                });
                if (unreservedCount[0] > 2) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
