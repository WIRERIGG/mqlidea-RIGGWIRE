/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.stub.MQL4NamedElementStub;

import javax.swing.Icon;
import java.util.ArrayList;
import java.util.List;

/** A {@code #define NAME [body]} macro; its name is the first IDENTIFIER after {@code #define}. */
public class MQL4DefineElement extends MQL4NamedStubElement<MQL4DefineElement> {

    public MQL4DefineElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4DefineElement(@NotNull MQL4NamedElementStub<MQL4DefineElement> stub) {
        super(stub, MQL4Elements.PREPROCESSOR_DEFINE_BLOCK);
    }

    /**
     * The parameter names of a function-like macro, {@code #define MAX(a,b) ...} giving [a, b]; empty
     * for an object-like macro. The {@code (} must touch the name, as in the preprocessor.
     */
    @NotNull
    public List<String> getParameterNames() {
        PsiElement name = getNameIdentifier();
        ASTNode open = name == null ? null : name.getNode().getTreeNext();
        if (open == null || open.getElementType() != MQL4Elements.L_ROUND_BRACKET) {
            return List.of();
        }
        List<String> names = new ArrayList<>();
        for (ASTNode n = open.getTreeNext(); n != null && n.getElementType() != MQL4Elements.R_ROUND_BRACKET; n = n.getTreeNext()) {
            if (n.getElementType() == MQL4Elements.IDENTIFIER) {
                names.add(n.getText());
            }
        }
        return names;
    }

    @NotNull
    @Override
    protected IElementType getDeclaredType() {
        return MQL4Elements.PREPROCESSOR_DEFINE_BLOCK;
    }

    @Override
    protected Icon getElementIcon() {
        return MQL4Icons.Define;
    }
}
