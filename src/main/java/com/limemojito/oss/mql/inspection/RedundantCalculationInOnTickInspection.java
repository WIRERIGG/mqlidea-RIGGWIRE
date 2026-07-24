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
 * Flags a constant lookup repeated in {@code OnTick()}. Excludes volatile market properties
 * ({@code SYMBOL_ASK}/{@code SYMBOL_BID}/{@code SYMBOL_LAST}, {@code SymbolInfoTick},
 * {@code TimeCurrent}, {@code TimeLocal}) from the repeat count — those change on every tick and
 * MUST NOT be cached across ticks (see {@link StatementAst#isVolatileMarketCall}).
 */
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
                Map<String, Integer> counts = new HashMap<>();
                StatementAst.forEachCall(body, EXPENSIVE_FUNCS, id -> {
                    if (StatementAst.isVolatileMarketCall(id)) return;
                    counts.merge(id.getText(), 1, Integer::sum);
                });
                if (counts.values().stream().anyMatch(count -> count > 1)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
