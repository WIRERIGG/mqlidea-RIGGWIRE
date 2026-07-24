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

public class ArrayAccessWithoutSizeCheckInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Array access without ArraySize() check — risk of out-of-bounds access";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode access = StatementAst.findArrayAccess(body);
                if (access != null && body != null && !isSizeAware(body)) {
                    // Anchor the warning at the array access itself, not the whole function header.
                    problems.add(createWarning(manager, StatementAst.anchor(access, child.getNavigationElement()), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    // Signals that the function is already size-aware, so its array indexing is governed by a known
    // bound — don't flag it. Covers explicit size calls (ArraySize/ArrayRange), the OnCalculate size
    // contract (rates_total/prev_calculated), and bar-count bounds (Bars/BarsCalculated/iBars).
    // Computed in one identifier walk. This removes the flood of false positives on indicator code
    // that indexes timeseries/buffers by rates_total rather than ArraySize.
    private static boolean isSizeAware(@NotNull ASTNode body) {
        java.util.Set<String> ids = StatementAst.collectIdentifiers(body);
        return ids.contains("ArraySize") || ids.contains("ArrayRange")
                || ids.contains("rates_total") || ids.contains("prev_calculated")
                || ids.contains("Bars") || ids.contains("BarsCalculated") || ids.contains("iBars");
    }
}
