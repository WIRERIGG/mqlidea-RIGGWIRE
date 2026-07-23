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
 * AST-based detection of unchecked {@code OrderSend()} calls: a bare
 * {@code EXPRESSION_STATEMENT} of the form {@code OrderSend(...);} whose result is discarded.
 * Checked usages live in different statement shapes and are never flagged: inside a control-flow
 * condition {@code (...)} block ({@code if(OrderSend(...))}), captured by an assignment or a
 * {@code VAR_DECLARATION_STATEMENT} ({@code int t = OrderSend(...);}), or returned from the
 * function ({@code return OrderSend(...);}).
 */
public class UncheckedOrderSendInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OrderSend() result should be checked for errors (retcode validation)";

    private static final String ORDER_SEND = "OrderSend";

    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    if (!ORDER_SEND.equals(ReturnValueIgnoredInspection.bareCallName(stmt))) return;
                    PsiElement psi = stmt.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createProblem(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
