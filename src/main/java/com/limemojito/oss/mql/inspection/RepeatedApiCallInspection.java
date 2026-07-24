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

public class RepeatedApiCallInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Function '%s()' called %d times in OnTick() — cache the result in a local variable for better performance";

    private static final int CALL_THRESHOLD = 2;

    private static final Set<String> EXPENSIVE_FUNCTIONS = Set.of(
            "SymbolInfoDouble", "SymbolInfoInteger", "SymbolInfoString",
            "AccountInfoDouble", "AccountInfoInteger",
            "MarketInfo",
            "iClose", "iOpen", "iHigh", "iLow", "iVolume", "iTime",
            "TimeCurrent", "TimeLocal"
    );

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && "OnTick".equals(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                checkExpensiveCalls(body, manager, child, problems);
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private void checkExpensiveCalls(@NotNull ASTNode body,
                                     @NotNull InspectionManager manager,
                                     @NotNull PsiElement function,
                                     @NotNull List<ProblemDescriptor> problems) {
        for (String funcName : EXPENSIVE_FUNCTIONS) {
            ProgressManager.checkCanceled();
            int count = StatementAst.countCalls(body, funcName);
            if (count > CALL_THRESHOLD) {
                problems.add(createWeakWarning(manager, function.getNavigationElement(),
                        String.format(MESSAGE, funcName, count)));
            }
        }
    }
}
