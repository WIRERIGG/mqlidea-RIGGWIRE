/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.extapi.psi.StubBasedPsiElementBase;
import com.intellij.lang.ASTNode;
import com.intellij.navigation.ItemPresentation;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.tree.IElementType;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;
import com.limemojito.oss.mql.psi.stub.MQL4ClassElementStub;

import javax.swing.Icon;

public class MQL4ClassElement extends StubBasedPsiElementBase<MQL4ClassElementStub> implements PsiNameIdentifierOwner {

    public static final String UNKNOWN_NAME = "<unknown>";

    public MQL4ClassElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4ClassElement(@NotNull MQL4ClassElementStub stub) {
        super(stub, MQL4Elements.CLASS);
    }

    @NotNull
    public String getTypeName() {
        MQL4ClassElementStub stub = getStub();
        if (stub != null) {
            return stub.getName();
        }
        ASTNode fieldNameNode = getNode().findChildByType(MQL4Elements.IDENTIFIER);
        return fieldNameNode == null ? UNKNOWN_NAME : fieldNameNode.getText();
    }

    public boolean isDeclaration() {
        MQL4ClassElementStub stub = getStub();
        return stub == null && getInnerBlockNode() == null;
    }

    /**
     * The class/struct/interface name is always the first direct IDENTIFIER child (the
     * inheritance list's identifiers live under a nested CLASS_INHERITANCE_LIST composite, so a
     * direct-child search never confuses a base-class name with this type's own name).
     */
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
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getNameIdentifierNode();
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    @Nullable
    public ASTNode getInnerBlockNode() {
        return getNode().findChildByType(MQL4Elements.CLASS_INNER_BLOCK);
    }

    @NotNull
    public ItemPresentation getPresentation() {
        return new ItemPresentation() {
            public String getPresentableText() {
                return getTypeName();
            }

            public String getLocationString() {
                return getContainingFile().getName();
            }

            public Icon getIcon(boolean open) {
                return getClassType() == ClassType.Interface ? MQL4Icons.Interface : getClassType() == ClassType.Struct ? MQL4Icons.Struct : MQL4Icons.Class;
            }
        };
    }

    @Override
    public String getName() {
        return getTypeName();
    }

    public ClassType getClassType() {
        MQL4ClassElementStub stub = getStub();
        if (stub != null) {
            return stub.getClassType();
        }
        IElementType t = getNode().getFirstChildNode().getElementType();
        if (t == MQL4Elements.STRUCT_KEYWORD) {
            return ClassType.Struct;
        } else if (t == MQL4Elements.INCLUDE_PP_KEYWORD) {
            return ClassType.Struct;
        }
        return ClassType.Class;
    }

    public enum ClassType {
        Struct, Interface, Class;

        @NotNull
        public String serialize() {
            return this == Struct ? "s" : this == Interface ? "i" : "c";
        }

        @NotNull
        public static ClassType deserialize(@Nullable String s) {
            return "i".equals(s) ? Interface : "s".equals(s) ? Struct : Class;
        }

        @NotNull
        public static ClassType fromTokenType(@Nullable IElementType t) {
            return t == MQL4Elements.STRUCT_KEYWORD ? Struct : t == MQL4Elements.INTERFACE_KEYWORD ? Interface : Class;
        }
    }
}
