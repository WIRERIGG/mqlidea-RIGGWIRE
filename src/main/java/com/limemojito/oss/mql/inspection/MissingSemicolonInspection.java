/*
 * Copyright (c) 2026.  RIGGWIRE Trading Systems.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.index.MQL4DefineNameIndex;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * A statement whose {@code ;} is missing. MetaEditor rejects it (error 154 "semicolon expected", or
 * "unexpected token" on the next line). The parser lets a statement run on to the next {@code ;}, so two
 * shapes are checked: a statement cut off without its {@code ;} by a {@code }}, a keyword or the next
 * declaration ({@code a = b <newline> if (...)}), and two operands with no operator between them across a
 * line break ({@code Print(1) <newline> Print(2);}, {@code int a = 1 <newline> int b = 2;}).
 * <p>
 * A statement that names a {@code #define} macro is left alone (its body may carry the {@code ;}), and so
 * is every statement in a file whose {@code #include}s the plugin can't all read, where the macro may be.
 */
public class MissingSemicolonInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "';' expected";
    private static final TokenSet STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT,
            MQL4Elements.RETURN_STATEMENT, MQL4Elements.VAR_DECLARATION_STATEMENT, MQL4Elements.SINGLE_WORD_STATEMENT);
    /** Tokens that can end an operand. */
    private static final TokenSet OPERAND_END = TokenSet.orSet(MQL4TokenSets.LITERALS, TokenSet.create(MQL4Elements.IDENTIFIER,
            MQL4Elements.BRACKETS_BLOCK, MQL4Elements.R_ROUND_BRACKET, MQL4Elements.R_SQUARE_BRACKET,
            MQL4Elements.PLUS_PLUS, MQL4Elements.MINUS_MINUS));
    /** Tokens that start an operand or a declaration. */
    private static final TokenSet OPERAND_START = TokenSet.orSet(MQL4TokenSets.LITERALS, MQL4TokenSets.DATA_TYPES,
            MQL4TokenSets.MEMORY_CLASSES, TokenSet.create(MQL4Elements.IDENTIFIER, MQL4Elements.CONST_KEYWORD));

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (UndeclaredNames.hasUnresolvedInclude(file)) {
            return ProblemDescriptor.EMPTY_ARRAY;
        }
        List<ProblemDescriptor> problems = new SmartList<>();
        String text = file.getText();
        Map<String, Boolean> macros = new HashMap<>();
        GlobalSearchScope scope = GlobalSearchScope.allScope(file.getProject());
        StatementAst.forEachDescendant(file.getNode(), STATEMENTS, stmt -> {
            ProgressManager.checkCanceled();
            ASTNode first = stmt.getFirstChildNode();
            if (first != null && (first.getElementType() == MQL4Elements.CASE_KEYWORD || first.getElementType() == MQL4Elements.DEFAULT_KEYWORD)) {
                return;
            }
            if (inParentheses(stmt) || hasError(stmt) || namesMacro(stmt, file, scope, macros)) {
                return;
            }
            ASTNode at = juxtaposedOperand(stmt, text);
            if (at == null && !endsWithSemicolon(stmt) && cutOff(stmt)) {
                at = lastLeafOf(stmt);
            }
            if (at != null && at.getPsi() != null) {
                problems.add(createProblem(manager, at.getPsi(), MESSAGE, isOnTheFly));
            }
        });
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** The first operand followed, across a line break and with no operator between, by another. */
    @Nullable
    private static ASTNode juxtaposedOperand(@NotNull ASTNode stmt, @NotNull String text) {
        ASTNode prev = null;
        for (ASTNode n = stmt.getFirstChildNode(); n != null; n = n.getTreeNext()) {
            if (StatementAst.isTrivia(n)) continue;
            if (prev != null && OPERAND_END.contains(prev.getElementType()) && OPERAND_START.contains(n.getElementType())
                    && !(MQL4TokenSets.STRINGS_AND_CHARS.contains(prev.getElementType())
                         && MQL4TokenSets.STRINGS_AND_CHARS.contains(n.getElementType()))
                    && text.substring(prev.getTextRange().getEndOffset(), n.getStartOffset()).contains("\n")) {
                return lastLeafOf(prev);
            }
            prev = n.getElementType() == MQL4Elements.VAR_DEFINITION_LIST ? lastLeafOf(n) : n; // int a <newline> int b;
        }
        return null;
    }

    private static boolean endsWithSemicolon(@NotNull ASTNode stmt) {
        ASTNode last = lastLeafOf(stmt);
        return last != null && last.getElementType() == MQL4Elements.SEMICOLON;
    }

    /** True when what follows the statement is something a {@code ;} must come before: not a preprocessor line or the end of the file. */
    private static boolean cutOff(@NotNull ASTNode stmt) {
        ASTNode next = stmt;
        while (next != null && next.getTreeNext() == null) next = next.getTreeParent(); // the last statement of a branch or block
        next = next == null ? null : next.getTreeNext();
        while (next != null && StatementAst.isTrivia(next)) next = next.getTreeNext();
        while (next != null && next.getFirstChildNode() != null) next = next.getFirstChildNode();
        // a label ends at its ':' (case X:, default:, name:), never at a ';'
        return next != null && !MQL4TokenSets.PREPROCESSOR.contains(next.getElementType()) && next.getElementType() != MQL4Elements.COLON;
    }

    /** Inside a {@code (...)}: a for header's clauses, or a misparse the parser already reports. */
    private static boolean inParentheses(@NotNull ASTNode stmt) {
        for (ASTNode p = stmt.getTreeParent(); p != null; p = p.getTreeParent()) {
            if (p.getElementType() == MQL4Elements.BRACKETS_BLOCK && p.getFirstChildNode() != null) {
                IElementType open = p.getFirstChildNode().getElementType();
                if (open == MQL4Elements.L_ROUND_BRACKET) return true;
                if (open == MQL4Elements.L_CURLY_BRACKET) return isInitializer(p);
            }
        }
        return false;
    }

    /** A {@code {...}} after {@code =}, {@code ,} or another {@code {}: an initializer list's rows, not statements. */
    private static boolean isInitializer(@NotNull ASTNode curly) {
        ASTNode prev = StatementAst.prevNonTrivia(curly);
        if (prev == null) return false;
        IElementType t = prev.getElementType();
        if (t == MQL4Elements.EQ || t == MQL4Elements.COMMA || t == MQL4Elements.L_CURLY_BRACKET) return true;
        ASTNode parent = curly.getTreeParent();
        return parent != null && parent.getElementType() == MQL4Elements.BRACKETS_BLOCK && isInitializer(parent);
    }

    private static boolean hasError(@NotNull ASTNode node) {
        if (node.getPsi() instanceof PsiErrorElement || node.getElementType() == com.intellij.psi.TokenType.BAD_CHARACTER) {
            return true;
        }
        for (ASTNode c = node.getFirstChildNode(); c != null; c = c.getTreeNext()) {
            if (hasError(c)) return true;
        }
        return false;
    }

    private static boolean namesMacro(@NotNull ASTNode node, @NotNull PsiFile file, @NotNull GlobalSearchScope scope,
                                      @NotNull Map<String, Boolean> macros) {
        if (node.getElementType() == MQL4Elements.IDENTIFIER) {
            return macros.computeIfAbsent(node.getText(), name ->
                    !MQL4DefineNameIndex.getInstance().getElements(name, file.getProject(), scope).isEmpty());
        }
        for (ASTNode c = node.getFirstChildNode(); c != null; c = c.getTreeNext()) {
            if (namesMacro(c, file, scope, macros)) return true;
        }
        return false;
    }

    @Nullable
    private static ASTNode lastLeafOf(@NotNull ASTNode node) {
        if (node.getFirstChildNode() == null) return StatementAst.isTrivia(node) ? null : node;
        for (ASTNode c = node.getLastChildNode(); c != null; c = c.getTreePrev()) {
            ASTNode leaf = lastLeafOf(c);
            if (leaf != null) return leaf;
        }
        return null;
    }
}
