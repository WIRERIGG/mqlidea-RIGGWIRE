/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.highlighting.ReadWriteAccessDetector;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiReference;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.util.ASTUtils;
import org.jetbrains.annotations.NotNull;

/**
 * Drives "Highlight usages" read/write colouring (and the equivalent gutter marks) for MQL
 * identifiers. Kept deliberately conservative -- only the identifier leaf's immediate next
 * sibling token is consulted to decide write-vs-read, matching the plain assignment/increment
 * idioms MQL actually uses; anything more elaborate (e.g. an lvalue behind a cast) falls back to
 * {@link Access#Read}, which is the safe default (under-highlighting a write is far less
 * confusing than mislabeling an ordinary read as a write).
 */
public class MqlReadWriteAccessDetector extends ReadWriteAccessDetector {

    /** Plain and compound assignment operator tokens ('=', '+=', '-=', ...); '==' is excluded. */
    private static final TokenSet ASSIGNMENT_OPERATORS = TokenSet.create(
            MQL4Elements.EQ, MQL4Elements.PLUS_EQ, MQL4Elements.MINUS_EQ, MQL4Elements.MUL_EQ,
            MQL4Elements.DIV_EQ, MQL4Elements.MOD_EQ, MQL4Elements.AND_EQ, MQL4Elements.OR_EQ,
            MQL4Elements.XOR_EQ, MQL4Elements.TILDA_EQ, MQL4Elements.POW_EQ,
            MQL4Elements.SH_LEFT_EQ, MQL4Elements.SH_RIGHT_EQ, MQL4Elements.USH_RIGHT_EQ
    );

    private static final TokenSet INCREMENT_DECREMENT = TokenSet.create(
            MQL4Elements.PLUS_PLUS, MQL4Elements.MINUS_MINUS
    );

    @Override
    public boolean isReadWriteAccessible(@NotNull PsiElement element) {
        ASTNode node = element.getNode();
        return node != null && node.getElementType() == MQL4Elements.IDENTIFIER;
    }

    @Override
    public boolean isDeclarationWriteAccess(@NotNull PsiElement element) {
        if (!(element.getParent() instanceof MQL4VarDefinitionElement)) {
            return false;
        }
        ASTNode node = element.getNode();
        if (node == null) {
            return false;
        }
        ASTNode next = ASTUtils.getNextIgnoreCommentsAndWs(node);
        return next != null && next.getElementType() == MQL4Elements.EQ;
    }

    /**
     * Used when the site under inspection was reached via a resolved {@link PsiReference} (e.g. a
     * Find-Usages result) rather than as a raw expression -- delegates to
     * {@link #getExpressionAccess(PsiElement)} on the reference's own element, which is exactly
     * the identifier leaf that method expects.
     */
    @NotNull
    @Override
    public Access getReferenceAccess(@NotNull PsiElement referencedElement, @NotNull PsiReference reference) {
        return getExpressionAccess(reference.getElement());
    }

    @NotNull
    @Override
    public Access getExpressionAccess(@NotNull PsiElement expression) {
        ASTNode node = expression.getNode();
        if (node == null) {
            return Access.Read;
        }

        ASTNode next = ASTUtils.getNextIgnoreCommentsAndWs(node);
        if (next != null) {
            IElementType nextType = next.getElementType();
            if (ASSIGNMENT_OPERATORS.contains(nextType) || INCREMENT_DECREMENT.contains(nextType)) {
                return Access.Write;
            }
        }

        ASTNode prev = ASTUtils.getPrevIgnoreCommentsAndWs(node);
        if (prev != null && INCREMENT_DECREMENT.contains(prev.getElementType())) {
            return Access.Write;
        }

        return Access.Read;
    }
}
