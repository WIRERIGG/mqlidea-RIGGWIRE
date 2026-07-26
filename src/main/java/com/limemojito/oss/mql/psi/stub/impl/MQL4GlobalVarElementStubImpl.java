/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.impl;

import com.intellij.psi.stubs.StubBase;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.psi.stub.MQL4GlobalVarElementStub;

public class MQL4GlobalVarElementStubImpl extends StubBase<MQL4VarDefinitionElement> implements MQL4GlobalVarElementStub {

    @Nullable
    private final String name;

    public MQL4GlobalVarElementStubImpl(StubElement parent, @Nullable String name) {
        super(parent, MQL4Elements.VAR_DEFINITION);
        this.name = name;
    }

    @Nullable
    @Override
    public String getName() {
        return name;
    }
}
