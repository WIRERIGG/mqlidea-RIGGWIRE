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

/**
 * MQL4-only. Flags OrderSelect() called as a bare statement with its boolean
 * result ignored — order data read afterwards may be stale or invalid. Detection reuses
 * {@link ReturnValueIgnoredInspection#bareCallName}: a bare {@code EXPRESSION_STATEMENT} whose
 * only content is {@code OrderSelect(...)} with no capturing assignment. Because the condition
 * of an {@code if}/{@code while} and a call's argument list are never themselves
 * {@code EXPRESSION_STATEMENT} nodes in this grammar, {@code if(OrderSelect(...))},
 * {@code ok = OrderSelect(...)} and {@code return OrderSelect(...)} are excluded by construction
 * — no hand-rolled paren-depth/statement-boundary text scan is needed.
 */
public class OrderSelectUncheckedInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "OrderSelect() result ignored — check its bool return before reading order data";

    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                ASTNode[] offending = {null};
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    if (offending[0] == null && "OrderSelect".equals(ReturnValueIgnoredInspection.bareCallName(stmt))) {
                        offending[0] = stmt;
                    }
                });
                if (offending[0] != null) {
                    problems.add(createWeakWarning(manager, StatementAst.anchor(offending[0], child.getNavigationElement()), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
