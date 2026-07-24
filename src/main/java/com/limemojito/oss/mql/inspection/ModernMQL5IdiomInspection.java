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
import java.util.Map;

public class ModernMQL5IdiomInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Deprecated MQL4 function '%s()' used — consider MQL5 equivalent '%s()'";
    // NOTE: OrderSend() is NOT deprecated — bool OrderSend(MqlTradeRequest&, MqlTradeResult&) is the
    // current MQL5 trade function. Only functions genuinely absent from MQL5 belong here. (Preferring
    // the CTrade wrapper over raw OrderSend is a style choice, not a deprecation, so it is not flagged.)
    private static final Map<String, String> DEPRECATED_FUNCS = Map.ofEntries(
            Map.entry("OrderClose", "CTrade.PositionClose"),
            Map.entry("OrderModify", "CTrade.OrderModify"),
            Map.entry("OrderDelete", "CTrade.OrderDelete"),
            Map.entry("MarketInfo", "SymbolInfoDouble/SymbolInfoInteger"),
            Map.entry("AccountBalance", "AccountInfoDouble(ACCOUNT_BALANCE)"),
            Map.entry("AccountEquity", "AccountInfoDouble(ACCOUNT_EQUITY)"),
            Map.entry("AccountFreeMargin", "AccountInfoDouble(ACCOUNT_MARGIN_FREE)"),
            Map.entry("AccountNumber", "AccountInfoInteger(ACCOUNT_LOGIN)")
    );

    /**
     * The MQL4-only function names this inspection already knows are gone in MQL5, exposed so
     * completion (REVAMP_PLAN.md Phase 6) can reuse the exact same set for dialect filtering
     * instead of re-deriving it. See {@link com.limemojito.oss.mql.MqlBuiltinDialect}.
     */
    @NotNull
    public static java.util.Set<String> deprecatedMql4OnlyFunctionNames() {
        return DEPRECATED_FUNCS.keySet();
    }

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (!file.getName().toLowerCase().endsWith(".mq5")) return ProblemDescriptor.EMPTY_ARRAY;

        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                for (Map.Entry<String, String> entry : DEPRECATED_FUNCS.entrySet()) {
                    if (StatementAst.hasCall(body, entry.getKey())) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(),
                                String.format(MESSAGE, entry.getKey(), entry.getValue())));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
