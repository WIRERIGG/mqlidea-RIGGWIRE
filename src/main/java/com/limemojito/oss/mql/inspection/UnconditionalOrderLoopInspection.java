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
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Set;

/**
 * AST-based detection of order-status calls driven unconditionally by a loop in {@code OnTick}:
 * a {@code FOR/WHILE/DO_STATEMENT} whose header {@code (...)} block calls one of the order
 * functions, or whose body contains a bare {@code EXPRESSION_STATEMENT} call to one of them
 * directly (not nested inside an {@code IF_STATEMENT} guard within the loop). Calls guarded by
 * an {@code if} inside the loop, or appearing outside any loop, are no longer flagged — the old
 * heuristic fired whenever {@code OnTick} merely contained such a call without caching keywords.
 */
public class UnconditionalOrderLoopInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OrdersTotal()/PositionsTotal() called every tick without change detection — consider caching or event-driven check";
    private static final Set<String> ORDER_LOOP_FUNCS = Set.of(
            "OrdersTotal", "PositionsTotal", "OrderSelect", "PositionSelect"
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
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    if (!isUnconditionalOrderLoop(loop)) return;
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWeakWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean isUnconditionalOrderLoop(@NotNull ASTNode loop) {
        // Header call — e.g. for(int i = PositionsTotal() - 1; i >= 0; i--) — runs every tick.
        ASTNode header = StatementAst.findConditionBlock(loop);
        if (header != null && BracketBlockTokenWalker.containsAnyFunctionCall(header, ORDER_LOOP_FUNCS)) {
            return true;
        }
        ASTNode loopBody = StatementAst.findLoopBody(loop);
        if (loopBody == null) return false;
        if (StatementAst.isCodeBlock(loopBody)) {
            for (ASTNode stmt = loopBody.getFirstChildNode(); stmt != null; stmt = stmt.getTreeNext()) {
                ProgressManager.checkCanceled();
                if (isBareOrderCall(stmt)) {
                    return true;
                }
            }
            return false;
        }
        // Brace-less loop body: the single statement itself.
        return isBareOrderCall(loopBody);
    }

    /** True for a bare {@code EXPRESSION_STATEMENT} calling one of the order functions. */
    private static boolean isBareOrderCall(@Nullable ASTNode statement) {
        if (statement == null || statement.getElementType() != MQL4Elements.EXPRESSION_STATEMENT) {
            return false;
        }
        String name = ReturnValueIgnoredInspection.bareCallName(statement);
        return name != null && ORDER_LOOP_FUNCS.contains(name);
    }
}
