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
import java.util.regex.Pattern;

/**
 * MQL4-only. Flags a forward (ascending) loop over OrdersTotal() that closes
 * or deletes orders inside — the order pool re-indexes after each close, so a
 * forward loop skips every other order. Iterate downward instead.
 * <p>
 * The header shape is located structurally (the real {@code FOR_STATEMENT}'s condition
 * {@code (...)} block, via {@link StatementAst#findConditionBlock}) and the header-pattern regex
 * is now applied only to that block's own text — not the whole function — so it can no longer
 * match a for-header that belongs to a different loop. The body is likewise the real AST loop body
 * ({@link StatementAst#findLoopBody}), eliminating the old hand-rolled brace/semicolon scanner.
 */
public class OrderCloseLoopDirectionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Closing/deleting orders in a forward OrdersTotal() loop skips orders — iterate downward (for(i=OrdersTotal()-1; i>=0; i--))";

    /**
     * Matches an ascending for-header over OrdersTotal(): initialised to 0,
     * bounded with {@code < OrdersTotal()} and incremented with {@code ++}.
     * Descending loops ({@code i >= 0; i--}) do not match.
     */
    private static final Pattern FORWARD_ORDERS_LOOP = Pattern.compile(
            "^\\(\\s*[^;]*=\\s*0\\s*;[^;]*<\\s*OrdersTotal\\s*\\(\\s*\\)[^;]*;[^)]*\\+\\+\\s*\\)$");

    private static final TokenSet FOR_STATEMENT = TokenSet.create(MQL4Elements.FOR_STATEMENT);
    private static final Set<String> CLOSE_OR_DELETE = Set.of("OrderClose", "OrderDelete");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean[] flagged = {false};
                StatementAst.forEachDescendant(body, FOR_STATEMENT, forLoop -> {
                    if (flagged[0] || !isForwardOrdersLoop(forLoop)) return;
                    ASTNode loopBody = StatementAst.findLoopBody(forLoop);
                    if (loopBody != null && StatementAst.hasAnyCall(loopBody, CLOSE_OR_DELETE)) {
                        flagged[0] = true;
                    }
                });
                if (flagged[0]) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean isForwardOrdersLoop(@NotNull ASTNode forLoop) {
        ASTNode condition = StatementAst.findConditionBlock(forLoop);
        if (condition == null) return false;
        String header = StatementAst.heuristicText(condition).replaceAll("\\s+", " ").trim();
        return FORWARD_ORDERS_LOOP.matcher(header).find();
    }
}
