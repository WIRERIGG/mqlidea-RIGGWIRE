/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Shared helpers for telling apart a "declaration name" IDENTIFIER leaf (the name a
 * function/class/enum/variable/parameter is declared with) from a "usage" IDENTIFIER leaf (a
 * call, a read/write, a type reference, a base-class name...). Phase 4 (REVAMP_PLAN.md #3b)
 * attaches a {@link MqlReference} to every IDENTIFIER leaf that is NOT a declaration name.
 */
public final class MqlPsiUtil {

    private MqlPsiUtil() {
    }

    public static boolean isDeclarationNameIdentifier(@NotNull PsiElement leaf) {
        if (leaf.getNode() == null || leaf.getNode().getElementType() != MQL4Elements.IDENTIFIER) {
            return false;
        }
        PsiElement parent = leaf.getParent();
        if (parent instanceof MQL4FunctionElement) {
            return leaf.equals(((MQL4FunctionElement) parent).getNameIdentifier());
        }
        if (parent instanceof MQL4ClassElement) {
            return leaf.equals(((MQL4ClassElement) parent).getNameIdentifier());
        }
        if (parent instanceof MQL4EnumElement) {
            return leaf.equals(((MQL4EnumElement) parent).getNameIdentifier());
        }
        if (parent instanceof MQL4EnumFieldElement) {
            return leaf.equals(((MQL4EnumFieldElement) parent).getNameIdentifier());
        }
        if (parent instanceof MQL4VarDefinitionElement) {
            return leaf.equals(((MQL4VarDefinitionElement) parent).getNameIdentifier());
        }
        if (parent instanceof MQL4FunctionArgElement) {
            return leaf.equals(((MQL4FunctionArgElement) parent).getNameIdentifier());
        }
        return false;
    }

    /**
     * True when {@code node} is a "{}" code block (a function/nested-block body) as opposed to a
     * BRACKETS_BLOCK standing in for parens or a "[...]" index -- see
     * {@link com.limemojito.oss.mql.parser.parsing.BracketBlockParsing}, which only pushes the
     * CODE_BLOCK parsing scope (and only there does the tolerant statement/local-declaration
     * parser run) when the opening bracket is '{'.
     */
    public static boolean isCodeBlock(@NotNull PsiElement element) {
        ASTNode node = element.getNode();
        if (node == null || node.getElementType() != MQL4Elements.BRACKETS_BLOCK) {
            return false;
        }
        ASTNode first = node.getFirstChildNode();
        return first != null && first.getElementType() == MQL4Elements.L_CURLY_BRACKET;
    }

    /**
     * The {@code (...)} header block when {@code element} is a {@code FOR_STATEMENT}, otherwise null. Its direct children
     * hold the init-clause {@code VAR_DECLARATION_STATEMENT} when the loop declares its variable.
     */
    @org.jetbrains.annotations.Nullable
    public static ASTNode forHeaderOf(@org.jetbrains.annotations.Nullable PsiElement element) {
        ASTNode forStatement = element == null ? null : element.getNode();
        if (forStatement == null || forStatement.getElementType() != MQL4Elements.FOR_STATEMENT) {
            return null;
        }
        for (ASTNode child = forStatement.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (child.getElementType() == MQL4Elements.BRACKETS_BLOCK) {
                ASTNode first = child.getFirstChildNode();
                return first != null && first.getElementType() == MQL4Elements.L_ROUND_BRACKET ? child : null;
            }
        }
        return null;
    }
}
