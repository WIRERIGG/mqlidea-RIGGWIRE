/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.extapi.psi.StubBasedPsiElementBase;
import com.intellij.lang.ASTNode;
import com.intellij.navigation.ColoredItemPresentation;
import com.intellij.navigation.ItemPresentation;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.stub.MQL4FunctionElementStub;
import com.limemojito.oss.mql.util.ASTUtils;

import javax.swing.Icon;

import static com.limemojito.oss.mql.util.TextUtils.abbreviate;
import static com.limemojito.oss.mql.util.TextUtils.simplify;

public class MQL4FunctionElement extends StubBasedPsiElementBase<MQL4FunctionElementStub> {

    public static final String UNKNOWN_NAME = "<unknown>";

    public MQL4FunctionElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4FunctionElement(@NotNull MQL4FunctionElementStub stub) {
        super(stub, stub.isDeclaration() ? MQL4Elements.FUNCTION_DECLARATION : MQL4Elements.FUNCTION);
    }

    @NotNull
    public String getFunctionName() {
        MQL4FunctionElementStub stub = getStub();
        if (stub != null) {
            return stub.getName();
        }

        ASTNode argsListStartNode = getNode().findChildByType(MQL4Elements.L_ROUND_BRACKET);
        ASTNode nameNode = argsListStartNode == null ? null : ASTUtils.findLastPrevByType(argsListStartNode, MQL4Elements.IDENTIFIER);
        if (nameNode == null) {
            return UNKNOWN_NAME;
        }
        ASTNode prevNode = ASTUtils.getPrevIgnoreCommentsAndWs(nameNode);
        return (prevNode != null && prevNode.getElementType() == MQL4Elements.TILDA ? "~" : "") + nameNode.getText();
    }

    public boolean isDeclaration() {
        MQL4FunctionElementStub stub = getStub();
        if (stub != null) {
            return stub.isDeclaration();
        }
        return getNode().getElementType() == MQL4Elements.FUNCTION_DECLARATION;
    }

    @NotNull
    public String getSignature() {
        MQL4FunctionElementStub stub = getStub();
        if (stub != null) {
            return stub.getSignature();
        }
        ASTNode argsList = getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        return argsList == null ? "" : argsList.getText();
    }

    @Override
    public String getName() {
        return getFunctionName();
    }

    @NotNull
    public ItemPresentation getPresentation() {
        return new ColoredItemPresentation() {
            public TextAttributesKey getTextAttributesKey() {
                return null;
            }

            public String getPresentableText() {
                return getFunctionName() + "(" + abbreviate(simplify(getSignature()), 140) + ")";
            }

            public String getLocationString() {
                return getContainingFile().getName();
            }

            public Icon getIcon(boolean open) {
                boolean declaration = isDeclaration();
                PsiElement p = getParent();
                if (p != null) {
                    if (p.getNode().getElementType() == MQL4Elements.CLASS_INNER_BLOCK) {
                        return declaration ? MQL4Icons.MethodDeclaration : MQL4Icons.MethodDefinition;
                    }
                }
                return declaration ? MQL4Icons.FunctionDeclaration : MQL4Icons.FunctionDefinition;
            }
        };
    }
}

