/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.extapi.psi.StubBasedPsiElementBase;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;
import com.limemojito.oss.mql.psi.stub.MQL4EnumElementStub;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class MQL4EnumElement extends StubBasedPsiElementBase<MQL4EnumElementStub> implements PsiNameIdentifierOwner {

    public MQL4EnumElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4EnumElement(@NotNull MQL4EnumElementStub stub) {
        super(stub, MQL4Elements.ENUM_STATEMENT);
    }

    @Nullable
    public String getTypeName() {
        MQL4EnumElementStub stub = getGreenStub();
        if (stub != null) {
            return stub.getName();
        }
        ASTNode typeNameElement = getTypeNameNode();
        return typeNameElement == null ? null : typeNameElement.getText();
    }

    @Nullable
    public ASTNode getTypeNameNode() {
        return getNode().findChildByType(MQL4Elements.IDENTIFIER);
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode node = getTypeNameNode();
        return node == null ? null : node.getPsi();
    }

    @Override
    public String getName() {
        return getTypeName();
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getTypeNameNode();
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    public List<MQL4EnumFieldElement> getFields() {
        ASTNode listNode = getNode().findChildByType(MQL4Elements.ENUM_FIELDS_LIST);
        if (listNode == null) {
            return Collections.emptyList();
        }
        List<MQL4EnumFieldElement> fields = new ArrayList<>();
        for (PsiElement child : listNode.getPsi().getChildren()) {
            fields.add((MQL4EnumFieldElement) child);
        }
        return fields;
    }
}
