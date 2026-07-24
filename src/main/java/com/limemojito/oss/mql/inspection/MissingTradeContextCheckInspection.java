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
 * MQL4-only. Flags a function that performs a trade operation without any
 * trade-context guard (IsTradeAllowed()/IsTradeContextBusy()) — in MQL4 the
 * trade context is single-threaded and may be busy when the EA tries to trade.
 */
public class MissingTradeContextCheckInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Trade operation without an IsTradeAllowed()/IsTradeContextBusy() check — the trade context may be busy";

    private static final Set<String> TRADE_OPERATIONS = Set.of(
            "OrderSend", "OrderClose", "OrderModify", "OrderDelete"
    );

    private static final Set<String> SKIPPED_HANDLERS = Set.of("OnInit", "OnDeinit");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && !SKIPPED_HANDLERS.contains(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                if (StatementAst.hasAnyCall(body, TRADE_OPERATIONS)
                        && !StatementAst.hasCall(body, "IsTradeAllowed")
                        && !StatementAst.hasCall(body, "IsTradeContextBusy")) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
