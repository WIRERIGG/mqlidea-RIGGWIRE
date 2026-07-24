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
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * AST-based detection of input-parameter reassignment: an assignment-operator token
 * ({@link StatementAst#ASSIGNMENT_OPERATORS}) or {@code ++}/{@code --} token directly adjacent to
 * an {@code IDENTIFIER} matching the input variable's name. Because assignment operators
 * ({@code EQ}, {@code PLUS_EQ}, ...) are already distinct lexer tokens from comparison operators
 * ({@code EQ_EQ}, {@code NOT_EQ}, {@code LESS_EQ}, {@code GT_EQ}), a comparison like
 * {@code if (Period == 20)} can never be mistaken for a reassignment — no negative-lookbehind
 * regex hack is needed to tell them apart.
 */
public class ImmutableInputParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Input parameter '%s' appears to be reassigned — input variables should be treated as immutable";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        List<String> inputNames = new ArrayList<>();

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == com.limemojito.oss.mql.psi.MQL4Elements.VAR_DECLARATION_STATEMENT
                    && isInputVariable(child)) {
                String name = getVariableName(child);
                if (name != null) inputNames.add(name);
            }
        }
        if (inputNames.isEmpty()) return ProblemDescriptor.EMPTY_ARRAY;

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                for (String inputName : inputNames) {
                    ASTNode target = findReassignment(body, inputName);
                    if (target != null) {
                        problems.add(createWarning(manager, StatementAst.anchor(target, child.getNavigationElement()),
                                String.format(MESSAGE, inputName), isOnTheFly));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** The {@code IDENTIFIER} node of the first reassignment of {@code name}, or null — for anchoring. */
    @Nullable
    private static ASTNode findReassignment(@NotNull ASTNode root, @NotNull String name) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (StatementAst.ASSIGNMENT_OPERATORS.contains(t)) {
                ASTNode prev = StatementAst.prevNonTrivia(child);
                if (isName(prev, name)) return prev;
            } else if (t == MQL4Elements.PLUS_PLUS || t == MQL4Elements.MINUS_MINUS) {
                ASTNode prev = StatementAst.prevNonTrivia(child);
                if (isName(prev, name)) return prev;
                ASTNode next = StatementAst.nextNonTrivia(child);
                if (isName(next, name)) return next;
            }
            ASTNode found = findReassignment(child, name);
            if (found != null) return found;
        }
        return null;
    }

    private static boolean isName(@Nullable ASTNode node, @NotNull String name) {
        return node != null && node.getElementType() == MQL4Elements.IDENTIFIER && name.equals(node.getText());
    }
}
