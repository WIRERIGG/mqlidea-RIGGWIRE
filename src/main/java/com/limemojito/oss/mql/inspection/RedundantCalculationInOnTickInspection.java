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

public class RedundantCalculationInOnTickInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Constant lookups repeated in OnTick() — consider caching in a variable";
    private static final Set<String> EXPENSIVE_FUNCS = Set.of(
            "SymbolInfoDouble", "SymbolInfoInteger", "SymbolInfoString",
            "AccountInfoDouble", "AccountInfoInteger", "AccountInfoString",
            "MarketInfo", "SymbolInfoTick"
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
                for (String funcName : EXPENSIVE_FUNCS) {
                    if (StatementAst.countCalls(body, funcName) > 1) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                        break;
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
