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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.Set;

/**
 * AST-based detection of loops with no obvious exit: a {@code WHILE_STATEMENT} whose condition
 * is a constant-true ({@code true} / nonzero integer literal), or a {@code FOR_STATEMENT} with
 * an empty {@code (;;)} header, whose body subtree contains no {@code break}
 * ({@code SINGLE_WORD_STATEMENT}), no {@code RETURN_STATEMENT} and no terminal-exit call.
 * Conservative by design: any break/return anywhere in the body (even inside nested statements)
 * suppresses the warning, and non-constant conditions are never flagged — the old regex/brace
 * scan could mispair braces when the loop body was not the next {@code {...}} region.
 */
public class InfiniteLoopRiskInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Potential infinite loop — 'while(true)' or 'for(;;)' without visible 'break' or 'return' statement";

    private static final TokenSet WHILE_OR_FOR = TokenSet.create(
            MQL4Elements.WHILE_STATEMENT, MQL4Elements.FOR_STATEMENT
    );

    /** Calls that terminate the expert/script, treated as loop exits. */
    private static final Set<String> EXIT_CALLS = Set.of("ExpertRemove", "TerminalClose");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, WHILE_OR_FOR, loop -> {
                    if (!hasConstantTrueCondition(loop)) return;
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null || hasExit(loopBody)) return;
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * True when the loop clearly runs forever by its header alone: {@code while(true)},
     * {@code while(1)} (any nonzero integer constant) or {@code for(;;)}.
     */
    private static boolean hasConstantTrueCondition(@NotNull ASTNode loop) {
        ASTNode condition = StatementAst.findConditionBlock(loop);
        if (condition == null) return false;
        String inner = innerConditionText(condition);
        if (loop.getElementType() == MQL4Elements.WHILE_STATEMENT) {
            return "true".equals(inner) || isNonZeroIntegerConstant(inner);
        }
        // FOR_STATEMENT: empty header — only the two semicolons, no condition at all.
        return ";;".equals(inner.replaceAll("\\s+", ""));
    }

    @NotNull
    private static String innerConditionText(@NotNull ASTNode conditionBlock) {
        String text = BracketBlockTokenWalker.stripCommentsAndStrings(conditionBlock.getText()).trim();
        if (text.startsWith("(")) text = text.substring(1);
        if (text.endsWith(")")) text = text.substring(0, text.length() - 1);
        return text.trim();
    }

    private static boolean isNonZeroIntegerConstant(@NotNull String s) {
        if (s.isEmpty() || !s.chars().allMatch(Character::isDigit)) return false;
        return !s.chars().allMatch(c -> c == '0');
    }

    /**
     * True when the subtree contains any obvious exit: a {@code break}
     * ({@code SINGLE_WORD_STATEMENT} or raw token), a {@code RETURN_STATEMENT}, or a call to a
     * terminal-exit function.
     */
    private static boolean hasExit(@NotNull ASTNode node) {
        IElementType t = node.getElementType();
        if (t == MQL4Elements.RETURN_STATEMENT) return true;
        if (t == MQL4Elements.BREAK_KEYWORD) return true;
        if (t == MQL4Elements.SINGLE_WORD_STATEMENT
                && node.findChildByType(MQL4Elements.BREAK_KEYWORD) != null) {
            return true;
        }
        if (t == MQL4Elements.IDENTIFIER && EXIT_CALLS.contains(node.getText())) return true;
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (hasExit(child)) {
                return true;
            }
        }
        return false;
    }
}
