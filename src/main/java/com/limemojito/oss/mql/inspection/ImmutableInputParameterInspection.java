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
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AST-based detection of input-parameter reassignment: an assignment-operator token
 * ({@link StatementAst#ASSIGNMENT_OPERATORS}) or {@code ++}/{@code --} token directly adjacent to
 * an {@code IDENTIFIER} matching the input variable's name. Because assignment operators
 * ({@code EQ}, {@code PLUS_EQ}, ...) are already distinct lexer tokens from comparison operators
 * ({@code EQ_EQ}, {@code NOT_EQ}, {@code LESS_EQ}, {@code GT_EQ}), a comparison like
 * {@code if (Period == 20)} can never be mistaken for a reassignment — no negative-lookbehind
 * regex hack is needed to tell them apart.
 * <p>
 * An identifier that matches the input name but is itself a member-access target —
 * {@code cfg.MaxRisk = ...} — is not a reassignment of the input {@code MaxRisk}; it is a
 * completely unrelated field on some other object that merely happens to share the name. Skipped
 * whenever the identifier's previous non-trivia token is a {@code DOT}.
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
                // ONE walk of the body collecting every reassigned identifier name -> its first
                // reassignment IDENTIFIER node (in pre-order, exactly the node the old per-input
                // findReassignment would have returned), instead of a full recursive walk per input.
                Map<String, ASTNode> reassigned = new HashMap<>();
                collectReassignments(body, reassigned);
                for (String inputName : inputNames) {
                    ASTNode target = reassigned.get(inputName);
                    if (target != null) {
                        problems.add(createWarning(manager, StatementAst.anchor(target, child.getNavigationElement()),
                                String.format(MESSAGE, inputName), isOnTheFly));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * Single pre-order walk recording, for each reassigned identifier name, the first
     * ({@link Map#putIfAbsent}) {@code IDENTIFIER} node that reassigns it. "Reassigns" = the
     * identifier is the write target of an assignment operator or a {@code ++}/{@code --}, and is
     * not itself a member-access target ({@code obj.x}). Semantics are identical to the old
     * per-name {@code findReassignment}; only the traversal is shared across all names.
     */
    private static void collectReassignments(@NotNull ASTNode root, @NotNull Map<String, ASTNode> out) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (StatementAst.ASSIGNMENT_OPERATORS.contains(t)) {
                record(StatementAst.prevNonTrivia(child), out);
            } else if (t == MQL4Elements.PLUS_PLUS || t == MQL4Elements.MINUS_MINUS) {
                record(StatementAst.prevNonTrivia(child), out);
                record(StatementAst.nextNonTrivia(child), out);
            }
            collectReassignments(child, out);
        }
    }

    /** Records {@code node} as a reassignment (first-wins) when it is a plain (non-member) identifier. */
    private static void record(@Nullable ASTNode node, @NotNull Map<String, ASTNode> out) {
        if (node != null && node.getElementType() == MQL4Elements.IDENTIFIER && !isMemberAccessTarget(node)) {
            out.putIfAbsent(node.getText(), node);
        }
    }

    /** True when {@code identifier} is preceded by a {@code DOT} — i.e. it is {@code x} in {@code obj.x}, a member access, not a plain variable. */
    private static boolean isMemberAccessTarget(@NotNull ASTNode identifier) {
        ASTNode before = StatementAst.prevNonTrivia(identifier);
        return before != null && before.getElementType() == MQL4Elements.DOT;
    }
}
