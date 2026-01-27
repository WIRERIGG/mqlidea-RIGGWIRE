/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.impl;

import com.intellij.psi.stubs.StubBase;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.stub.MQL4ClassElementStub;

public class MQL4ClassElementStubImpl extends StubBase<MQL4ClassElement> implements MQL4ClassElementStub {

    @NotNull
    private final String name;

    @NotNull
    private final MQL4ClassElement.ClassType classType;

    public MQL4ClassElementStubImpl(@NotNull StubElement parent, @NotNull String name, @NotNull MQL4ClassElement.ClassType classType) {
        super(parent, MQL4Elements.CLASS);
        this.name = name;
        this.classType = classType;
    }

    @NotNull
    @Override
    public String getName() {
        return name;
    }

    @NotNull
    @Override
    public MQL4ClassElement.ClassType getClassType() {
        return classType;
    }
}
