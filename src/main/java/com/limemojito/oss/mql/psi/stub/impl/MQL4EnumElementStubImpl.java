/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub.impl;

import com.intellij.psi.stubs.StubBase;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.stub.MQL4EnumElementStub;

import java.util.List;

public class MQL4EnumElementStubImpl extends StubBase<MQL4EnumElement> implements MQL4EnumElementStub {

    @Nullable
    private final String name;

    @NotNull
    private final List<String> fieldNames;

    public MQL4EnumElementStubImpl(StubElement parent, @Nullable String name, @NotNull List<String> fieldNames) {
        super(parent, MQL4Elements.ENUM_STATEMENT);
        this.name = name;
        this.fieldNames = List.copyOf(fieldNames);
    }

    @Nullable
    @Override
    public String getName() {
        return name;
    }

    @NotNull
    @Override
    public List<String> getFieldNames() {
        return fieldNames;
    }
}
