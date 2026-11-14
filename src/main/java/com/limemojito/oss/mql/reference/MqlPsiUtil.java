/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4NamedStubElement;
import com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement;
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
        if (parent instanceof MQL4NamedStubElement<?> named) { // typedef, #define
            return leaf.equals(named.getNameIdentifier());
        }
        if (parent instanceof MQL4NamespaceElement namespace) {
            return leaf.equals(namespace.getNameIdentifier());
        }
        return false;
    }

    /**
     * {@code X} in an out-of-line definition {@code T X::Name(...) { }}: the IDENTIFIER before the
     * function's direct {@code ::}, or null for a function defined in place.
     */
    @Nullable
    public static String outOfLineClassName(@NotNull MQL4FunctionElement function) {
        ASTNode colons = function.getNode().findChildByType(MQL4Elements.COLON_COLON);
        ASTNode id = colons == null ? null : prevMeaningful(colons);
        return id != null && id.getElementType() == MQL4Elements.IDENTIFIER ? id.getText() : null;
    }

    /**
     * The declared return type when it is a user type ({@code CFoo *Get()} gives {@code CFoo}): the
     * function's first direct IDENTIFIER, unless that is the class of {@code X::X()} or the name
     * itself. Null for a primitive return type, a constructor or a destructor.
     */
    @Nullable
    public static String returnTypeName(@NotNull MQL4FunctionElement function) {
        for (ASTNode child = function.getNode().getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType t = child.getElementType();
            if (MQL4TokenSets.COMMENTS_OR_WS.contains(t) || FUNCTION_MODIFIERS.contains(t)) {
                continue;
            }
            if (t != MQL4Elements.IDENTIFIER) {
                return null; // a primitive keyword, '~', or the name/argument list
            }
            ASTNode next = nextMeaningful(child);
            if (next == null || next.getElementType() == MQL4Elements.COLON_COLON
                    || next.getElementType() == MQL4Elements.L_ROUND_BRACKET) {
                return null; // X::X() or a name with no return type
            }
            return child.getText();
        }
        return null;
    }

    private static final TokenSet FUNCTION_MODIFIERS = TokenSet.create(
            MQL4Elements.VIRTUAL_KEYWORD, MQL4Elements.CONST_KEYWORD, MQL4Elements.STATIC_KEYWORD);

    /** True when {@code leaf} lies after the argument list of {@code function} (its body or initializer list). */
    public static boolean isAfterArguments(@NotNull MQL4FunctionElement function, @NotNull PsiElement leaf) {
        ASTNode args = function.getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        return args != null && leaf.getTextRange().getStartOffset() >= args.getTextRange().getEndOffset();
    }

    @Nullable
    private static ASTNode prevMeaningful(@NotNull ASTNode node) {
        ASTNode n = node.getTreePrev();
        while (n != null && MQL4TokenSets.COMMENTS_OR_WS.contains(n.getElementType())) {
            n = n.getTreePrev();
        }
        return n;
    }

    @Nullable
    private static ASTNode nextMeaningful(@NotNull ASTNode node) {
        ASTNode n = node.getTreeNext();
        while (n != null && MQL4TokenSets.COMMENTS_OR_WS.contains(n.getElementType())) {
            n = n.getTreeNext();
        }
        return n;
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
