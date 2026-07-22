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

/**
 * MQL5-only. Flags {@code return 0;} / {@code return(0);} inside
 * OnCalculate() — returning 0 tells the terminal that nothing was calculated,
 * forcing a full indicator recalculation on every tick. Return rates_total
 * (or prev_calculated) instead.
 */
public class OnCalculateReturnInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "OnCalculate() returning 0 forces a full recalculation each tick — return rates_total (or prev_calculated)";

    /** Whole-token return of literal 0, with or without parentheses. */
    private static final String RETURN_ZERO_REGEX = "\\breturn\\s*\\(?\\s*0\\s*\\)?\\s*;";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && "OnCalculate".equals(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                if (BracketBlockTokenWalker.containsPattern(body, RETURN_ZERO_REGEX)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
