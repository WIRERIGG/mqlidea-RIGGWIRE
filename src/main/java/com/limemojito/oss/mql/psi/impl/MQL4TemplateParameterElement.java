/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.search.LocalSearchScope;
import com.intellij.psi.search.SearchScope;
import com.intellij.util.IncorrectOperationException;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * One {@code typename T} (or {@code class T}) in a {@code template<...>} header. File-local by
 * definition, so it is plain PSI with no stub; uses resolve to it through
 * {@link com.limemojito.oss.mql.reference.MqlResolveUtil#resolveTemplateParameter}.
 */
public class MQL4TemplateParameterElement extends MQL4PsiElement implements PsiNameIdentifierOwner {

    public MQL4TemplateParameterElement(@NotNull ASTNode node) {
        super(node);
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode id = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        return id == null ? null : id.getPsi();
    }

    @Override
    public String getName() {
        PsiElement id = getNameIdentifier();
        return id == null ? null : id.getText();
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode id = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        if (id != null) {
            getNode().replaceChild(id, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    @Override
    public int getTextOffset() {
        PsiElement id = getNameIdentifier();
        return id == null ? super.getTextOffset() : id.getTextOffset();
    }

    /** The template it heads never leaves this file. */
    @NotNull
    @Override
    public SearchScope getUseScope() {
        return new LocalSearchScope(getContainingFile());
    }

    @Override
    public String toString() {
        return "TEMPLATE_PARAMETER:" + getName();
    }
}
