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
import com.intellij.psi.tree.IElementType;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * AST-based nesting depth: the function body counts as level 1 and every nested control-flow
 * statement ({@code if/for/while/do/switch}) or standalone {@code {...}} block adds a level.
 * An {@code else if} chained to a parent {@code if} stays on its parent's level, and a control
 * statement's own {@code {...}} body does not double-count. Unlike the old brace counting this
 * also measures brace-less nesting such as {@code if(a) if(b) if(c) ...}.
 */
public class DeepNestingInspection extends MQL5SafetyInspectionBase {

    private static final int MAX_NESTING_DEPTH = 4;
    private static final String MESSAGE = "Excessive nesting depth (%d levels) — consider extracting methods to reduce complexity";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(func);
                if (body == null) continue;
                int maxDepth = maxDepth(body, 1);
                if (maxDepth > MAX_NESTING_DEPTH) {
                    problems.add(createWeakWarning(manager, func.getNavigationElement(),
                            String.format(MESSAGE, maxDepth)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * @param node  a code block, control-flow statement or other composite whose children are at
     *              {@code depth}
     * @param depth nesting level assigned to direct child statements of {@code node}
     * @return maximum nesting level found in the subtree
     */
    private static int maxDepth(@NotNull ASTNode node, int depth) {
        int max = depth;
        boolean nodeIsControl = StatementAst.CONTROL_FLOW_STATEMENTS.contains(node.getElementType());
        boolean afterElse = false;
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (t == MQL4Elements.ELSE_KEYWORD) {
                afterElse = true;
                continue;
            }
            int childMax;
            if (StatementAst.CONTROL_FLOW_STATEMENTS.contains(t)) {
                // An else-if chained onto a parent if stays on the parent's nesting level.
                boolean elseIfChain = afterElse && t == MQL4Elements.IF_STATEMENT
                        && node.getElementType() == MQL4Elements.IF_STATEMENT;
                childMax = maxDepth(child, elseIfChain ? depth : depth + 1);
            } else if (StatementAst.isParenBlock(child)) {
                continue; // condition / header group — coarse, holds no statement structure
            } else if (StatementAst.isCodeBlock(child)) {
                // A control statement's own {} body is already counted by the statement itself;
                // a standalone nested {} block introduces a level of its own.
                childMax = maxDepth(child, nodeIsControl ? depth : depth + 1);
            } else if (child.getFirstChildNode() != null) {
                childMax = maxDepth(child, depth); // other composites (expression statements etc.)
            } else {
                continue;
            }
            if (childMax > max) {
                max = childMax;
            }
        }
        return max;
    }
}
