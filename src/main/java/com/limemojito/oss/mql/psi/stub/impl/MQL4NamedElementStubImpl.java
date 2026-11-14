/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.impl;

import com.intellij.psi.PsiElement;
import com.intellij.psi.stubs.IStubElementType;
import com.intellij.psi.stubs.StubBase;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.stub.MQL4NamedElementStub;

public class MQL4NamedElementStubImpl<T extends PsiElement> extends StubBase<T> implements MQL4NamedElementStub<T> {

    @Nullable
    private final String name;

    public MQL4NamedElementStubImpl(StubElement<?> parent, IStubElementType<?, ?> elementType, @Nullable String name) {
        super(parent, elementType);
        this.name = name;
    }

    @Nullable
    @Override
    public String getName() {
        return name;
    }
}
