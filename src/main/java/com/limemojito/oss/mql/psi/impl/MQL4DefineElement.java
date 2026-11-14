/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.stub.MQL4NamedElementStub;

import javax.swing.Icon;

/** A {@code #define NAME [body]} macro; its name is the first IDENTIFIER after {@code #define}. */
public class MQL4DefineElement extends MQL4NamedStubElement<MQL4DefineElement> {

    public MQL4DefineElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4DefineElement(@NotNull MQL4NamedElementStub<MQL4DefineElement> stub) {
        super(stub, MQL4Elements.PREPROCESSOR_DEFINE_BLOCK);
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
