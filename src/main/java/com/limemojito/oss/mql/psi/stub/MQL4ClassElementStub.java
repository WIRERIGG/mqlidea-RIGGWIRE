/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;

public interface MQL4ClassElementStub extends StubElement<MQL4ClassElement> {

    @NotNull
    String getName();

    @NotNull
    MQL4ClassElement.ClassType getClassType();
}

