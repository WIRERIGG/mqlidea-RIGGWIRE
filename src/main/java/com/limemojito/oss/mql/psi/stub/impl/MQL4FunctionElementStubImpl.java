/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.impl;

import com.intellij.psi.stubs.StubBase;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.stub.MQL4FunctionElementStub;

import static com.limemojito.oss.mql.psi.stub.MQL4StubElements.FUNCTION;
import static com.limemojito.oss.mql.psi.stub.MQL4StubElements.FUNCTION_DECLARATION;

public class MQL4FunctionElementStubImpl extends StubBase<MQL4FunctionElement> implements MQL4FunctionElementStub {

    @NotNull
    private String name;
    @NotNull
    private String signature;

    private boolean declaration;

    public MQL4FunctionElementStubImpl(StubElement parent, @NotNull String name, @NotNull String signature, boolean declaration) {
        super(parent, declaration ? FUNCTION_DECLARATION : FUNCTION);
        this.name = name;
        this.signature = signature;
        this.declaration = declaration;
    }


    @NotNull
    @Override
    public String getName() {
        return name;
    }

    @NotNull
    @Override
    public String getSignature() {
        return signature;
    }

    @Override
    public boolean isDeclaration() {
        return declaration;
    }
}
