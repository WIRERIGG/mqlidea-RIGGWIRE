/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;

/**
 * PSI for a single VAR_DEFINITION -- one name inside a VAR_DEFINITION_LIST of a
 * VAR_DECLARATION_STATEMENT (see {@link com.limemojito.oss.mql.parser.parsing.statement.VarDeclarationStatement}).
 * Covers local variables, global variables (top-level) and class/struct member fields (Phase 4,
 * REVAMP_PLAN.md #3b) -- all three now share this exact PSI shape since
 * {@link com.limemojito.oss.mql.parser.MQL4Parser} and
 * {@link com.limemojito.oss.mql.parser.parsing.ClassParsing} were wired to reuse the same
 * tolerant var-declaration parse.
 */
public class MQL4VarDefinitionElement extends MQL4PsiElement implements PsiNameIdentifierOwner {

    public MQL4VarDefinitionElement(@NotNull ASTNode node) {
        super(node);
    }

    @Nullable
    private ASTNode getNameIdentifierNode() {
        return getNode().findChildByType(MQL4Elements.IDENTIFIER);
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode node = getNameIdentifierNode();
        return node == null ? null : node.getPsi();
    }

    @Override
    public String getName() {
        PsiElement id = getNameIdentifier();
        return id == null ? null : id.getText();
    }

    /**
     * The declared TYPE name of this variable/field, read from the leading type token of the
     * enclosing {@code VAR_DECLARATION_STATEMENT} (the child before the {@code VAR_DEFINITION_LIST}).
     * Returns {@code null} when that type is a built-in primitive keyword (never a class) or the
     * enclosing shape is unexpected. Used by
     * {@link com.limemojito.oss.mql.reference.MqlTypeResolver} to type-resolve {@code v.member};
     * today the tolerant parser only builds a {@code VAR_DECLARATION_STATEMENT} for primitive-typed
     * declarations, so this returns {@code null} in practice, but it is kept general so a future
     * custom-type declaration node resolves without further change.
     */
    @Nullable
    public String getDeclaredTypeName() {
        ASTNode list = getNode().getTreeParent();
        if (list == null || list.getElementType() != MQL4Elements.VAR_DEFINITION_LIST) {
            return null;
        }
        ASTNode statement = list.getTreeParent();
        if (statement == null || statement.getElementType() != MQL4Elements.VAR_DECLARATION_STATEMENT) {
            return null;
        }
        for (ASTNode child = statement.getFirstChildNode(); child != null && child != list; child = child.getTreeNext()) {
            // A custom (class) type appears as an IDENTIFIER; primitive keywords / modifiers are skipped.
            if (child.getElementType() == MQL4Elements.IDENTIFIER) {
                return child.getText();
            }
        }
        return null;
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getNameIdentifierNode();
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    @Override
    public String toString() {
        return "VAR_DEFINITION:" + getName();
    }
}
