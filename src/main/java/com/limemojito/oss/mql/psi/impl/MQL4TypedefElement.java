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

/** A {@code typedef int (*TName)(int,int);} function-pointer type; its name is the IDENTIFIER inside {@code (* )}. */
public class MQL4TypedefElement extends MQL4NamedStubElement<MQL4TypedefElement> {

    public MQL4TypedefElement(@NotNull ASTNode node) {
        super(node);
    }

    public MQL4TypedefElement(@NotNull MQL4NamedElementStub<MQL4TypedefElement> stub) {
        super(stub, MQL4Elements.TYPEDEF);
    }

    @NotNull
    @Override
    protected IElementType getDeclaredType() {
        return MQL4Elements.TYPEDEF;
    }

    @Override
    protected Icon getElementIcon() {
        return MQL4Icons.Typedef;
    }
}
