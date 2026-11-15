/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.navigation.ItemPresentation;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import javax.swing.Icon;

/**
 * {@code namespace Name { ... }}. Its body ({@code NAMESPACE_BODY}) holds the same declarations as a
 * file. A namespace may be reopened, so several blocks can share a name.
 */
public class MQL4NamespaceElement extends MQL4PsiElement implements PsiNameIdentifierOwner {

    public MQL4NamespaceElement(@NotNull ASTNode node) {
        super(node);
    }

    @Nullable
    private ASTNode getNameNode() {
        return getNode().findChildByType(MQL4Elements.IDENTIFIER);
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode node = getNameNode();
        return node == null ? null : node.getPsi();
    }

    @Nullable
    @Override
    public String getName() {
        ASTNode node = getNameNode();
        return node == null ? null : node.getText();
    }

    @Override
    public int getTextOffset() {
        ASTNode node = getNameNode();
        return node == null ? super.getTextOffset() : node.getStartOffset();
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getNameNode();
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    /** The body's direct children (declarations), or empty for a block without a body. */
    @NotNull
    public PsiElement[] getDeclarations() {
        ASTNode body = getNode().findChildByType(MQL4Elements.NAMESPACE_BODY);
        return body == null ? PsiElement.EMPTY_ARRAY : body.getPsi().getChildren();
    }

    /** The enclosing namespace names, outermost first, ending with this one: {@code A::B} gives [A, B]. */
    @NotNull
    public List<String> getPath() {
        List<String> path = new ArrayList<>();
        for (MQL4NamespaceElement ns = this; ns != null; ns = PsiTreeUtil.getParentOfType(ns, MQL4NamespaceElement.class)) {
            path.add(ns.getName());
        }
        Collections.reverse(path);
        return path;
    }

    @Override
    public ItemPresentation getPresentation() {
        return new ItemPresentation() {
            @Override
            public String getPresentableText() {
                return getName();
            }

            @Override
            public String getLocationString() {
                return getContainingFile() == null ? null : getContainingFile().getName();
            }

            @Override
            public Icon getIcon(boolean unused) {
                return MQL4Icons.Namespace;
            }
        };
    }
}
