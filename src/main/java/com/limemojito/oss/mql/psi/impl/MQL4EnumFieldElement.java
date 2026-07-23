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

public class MQL4EnumFieldElement extends MQL4PsiElement implements PsiNameIdentifierOwner {

    public MQL4EnumFieldElement(@NotNull ASTNode node) {
        super(node);
    }

    @NotNull
    public String getFieldName() {
        ASTNode fieldNameElement = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        return fieldNameElement == null ? "???" : fieldNameElement.getText();
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode node = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        return node == null ? null : node.getPsi();
    }

    @Override
    public String getName() {
        return getFieldName();
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

}
