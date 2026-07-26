/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;

public interface MQL4EnumElementStub extends StubElement<MQL4EnumElement> {

    /** The enum TYPE name, or {@code null} for an anonymous enum ({@code enum { ... }}). */
    @Nullable
    String getName();
}
