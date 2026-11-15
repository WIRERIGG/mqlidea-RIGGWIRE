/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.extapi.psi.StubBasedPsiElementBase;
import com.intellij.lang.ASTNode;
import com.intellij.navigation.ItemPresentation;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.stubs.IStubElementType;
import com.intellij.psi.tree.IElementType;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;
import com.limemojito.oss.mql.psi.stub.MQL4NamedElementStub;

import javax.swing.Icon;

/** A declaration named by its first direct IDENTIFIER child; base of {@code typedef} and {@code #define}. */
public abstract class MQL4NamedStubElement<T extends MQL4NamedStubElement<T>>
        extends StubBasedPsiElementBase<MQL4NamedElementStub<T>> implements PsiNameIdentifierOwner {

    protected MQL4NamedStubElement(@NotNull ASTNode node) {
        super(node);
    }

    protected MQL4NamedStubElement(@NotNull MQL4NamedElementStub<T> stub, @NotNull IStubElementType<?, ?> type) {
        super(stub, type);
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
        MQL4NamedElementStub<T> stub = getGreenStub();
        if (stub != null) {
            return stub.getName();
        }
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

    @Nullable
    protected abstract Icon getElementIcon();

    /** This element's type, known per subclass, so {@link #toString()} needs neither stub nor AST. */
    @NotNull
    protected abstract IElementType getDeclaredType();

    @Override
    public String toString() {
        return getClass().getSimpleName() + "(" + getDeclaredType() + ")";
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
                return getElementIcon();
            }
        };
    }
}
