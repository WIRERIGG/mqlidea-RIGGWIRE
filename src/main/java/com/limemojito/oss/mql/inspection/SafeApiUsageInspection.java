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
 * Flags an {@code OrderSend()} call with no visible lot-size validation nearby — but only the MQL4
 * positional form ({@code OrderSend(symbol, cmd, volume, price, ...)}), where a volume argument is
 * actually present to validate. The MQL5 request/result struct form
 * ({@code OrderSend(request, result)} — two bare-identifier arguments, e.g.
 * DualOrderManager.mqh:1048's {@code TRADE_ACTION_SLTP} call, or TradingUtilities.mqh:615/983's
 * {@code TRADE_ACTION_SLTP}/{@code TRADE_ACTION_MODIFY}/{@code TRADE_ACTION_DEAL} calls) carries no
 * volume parameter at the call site at all — the volume (if any) lives inside the
 * {@code MqlTradeRequest} struct, built up over many statements before the call in ways this
 * single-call text/identifier scan cannot follow — so "validate lot size before sending" is
 * meaningless there and must not be demanded.
 */
public class SafeApiUsageInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OrderSend() without volume validation — validate lot size before sending orders";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode call = StatementAst.findCall(body, "OrderSend");
                if (call != null && !StatementAst.callArgsAreBareIdentifiers(call, 2)) {
                    boolean hasVolumeCheck = StatementAst.hasIdentifier(body, "SYMBOL_VOLUME_MIN")
                            || StatementAst.hasIdentifier(body, "SYMBOL_VOLUME_MAX")
                            || StatementAst.hasIdentifier(body, "SYMBOL_VOLUME_STEP")
                            || StatementAst.hasCall(body, "MarketInfo")
                            || StatementAst.hasCall(body, "SymbolInfoDouble");
                    if (!hasVolumeCheck) {
                        problems.add(createWarning(manager, StatementAst.anchor(call, child.getNavigationElement()), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
