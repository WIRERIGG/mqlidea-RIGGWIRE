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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.Set;

/**
 * AST-based detection: a call to a trading function whose {@code (...)} args block directly
 * contains a {@code DOUBLE_LITERAL} token. Scoping the literal search to the specific call's own
 * args block (rather than a regex over the whole function with a {@code [^)]*} gap) means a
 * float literal in an unrelated later call in the same function can no longer be mistaken for
 * this call's argument.
 */
public class MagicNumberInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Hardcoded numeric value in trading operation — use named constants or input parameters for maintainability";

    private static final Set<String> TRADING_FUNCS = Set.of(
            "OrderSend", "OrderModify", "PositionOpen", "PositionClose",
            "CTrade", "Buy", "Sell", "BuyLimit", "SellLimit", "BuyStop", "SellStop");

    private static final TokenSet DOUBLE_LITERAL = TokenSet.create(MQL4Elements.DOUBLE_LITERAL);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean[] flagged = {false};
                StatementAst.forEachCall(body, TRADING_FUNCS, callId -> {
                    if (flagged[0]) return;
                    ASTNode args = StatementAst.callArgsBlock(callId);
                    if (args != null && StatementAst.hasDescendant(args, DOUBLE_LITERAL)) {
                        flagged[0] = true;
                    }
                });
                if (flagged[0]) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
