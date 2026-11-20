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

import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.reference.MqlPsiUtil;
import java.util.List;

/**
 * AST-based detection of {@code if(x);} / {@code for(...);} / {@code while(y);}: a control
 * statement whose body (the first statement node after the condition {@code (...)} block) is an
 * {@code EMPTY_STATEMENT}. Semicolons inside a {@code for} header are children of the condition
 * block, and calls in the header (e.g. {@code for(i=Foo(); i<n; i++){...}}) never produce false
 * positives because only the statement's body node is examined.
 */
public class SuspiciousSemicolonInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Suspicious semicolon after control statement — likely a logic error (empty body)";

    /** Operators that change a variable: the step clause of {@code for(k=0; k<3; k++);} uses one. */
    private static final TokenSet SIDE_EFFECTS = TokenSet.create(MQL4Elements.PLUS_PLUS, MQL4Elements.MINUS_MINUS,
            MQL4Elements.EQ, MQL4Elements.PLUS_EQ, MQL4Elements.MINUS_EQ, MQL4Elements.MUL_EQ, MQL4Elements.DIV_EQ,
            MQL4Elements.MOD_EQ, MQL4Elements.AND_EQ, MQL4Elements.OR_EQ, MQL4Elements.XOR_EQ,
            MQL4Elements.SH_LEFT_EQ, MQL4Elements.SH_RIGHT_EQ);

    /**
     * True for a {@code for} whose step clause (after the header's second {@code ;}) changes a
     * variable or calls a function: {@code for(k=0; k<3; k++);} runs its loop for the side effect,
     * an idiom MetaEditor doesn't warn about (it warns only for {@code if(...);}).
     */
    private static boolean advancesInStep(@NotNull ASTNode statement) {
        ASTNode header = MqlPsiUtil.forHeaderOf(statement.getPsi());
        if (header == null) {
            return false;
        }
        // the step clause follows the last child ending in ';' (the header's semicolons sit in
        // EMPTY_STATEMENT nodes, or in the init clause's VAR_DECLARATION_STATEMENT)
        for (ASTNode child = header.getLastChildNode(); child != null; child = child.getTreePrev()) {
            ASTNode last = child.getLastChildNode() == null ? child : child.getLastChildNode();
            if (last.getElementType() == MQL4Elements.SEMICOLON) {
                return false;
            }
            if (hasSideEffect(child)) {
                return true;
            }
        }
        return false;
    }

    /**
     * True for a loop that does its work in its header, so an empty body is intended: a {@code while} or
     * {@code do} whose condition calls a function or assigns ({@code while(StringReplace(s, a, b) > 0);},
     * {@code while(!GlobalVariableTemp(lock));}), or a {@code for} whose step does ({@link #advancesInStep}).
     */
    static boolean headerDoesWork(@NotNull ASTNode loop) {
        if (loop.getElementType() == MQL4Elements.FOR_STATEMENT) {
            return advancesInStep(loop);
        }
        if (loop.getElementType() == MQL4Elements.WHILE_STATEMENT || loop.getElementType() == MQL4Elements.DO_STATEMENT) {
            ASTNode condition = StatementAst.findConditionBlock(loop);
            return condition != null && hasSideEffect(condition);
        }
        return false;
    }

    private static boolean hasSideEffect(@NotNull ASTNode node) {
        if (SIDE_EFFECTS.contains(node.getElementType())) {
            return true;
        }
        if (node.getElementType() == MQL4Elements.IDENTIFIER) {
            return StatementAst.isCallIdentifierAnyScope(node); // a call: '(' or a wrapped (...) block
        }
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (hasSideEffect(child)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.CONDITION_STATEMENTS, stmt -> {
                    ASTNode stmtBody = StatementAst.findBodyAfterCondition(stmt);
                    if (stmtBody != null && stmtBody.getElementType() == MQL4Elements.EMPTY_STATEMENT
                            && !headerDoesWork(stmt)) {
                        PsiElement psi = stmt.getPsi();
                        if (psi != null && psi.isValid()) {
                            problems.add(createWarning(manager, psi, MESSAGE, isOnTheFly));
                        }
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
