/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Stub for a TOP-LEVEL (file-scope) global variable definition. Only globals are ever stubbed —
 * class fields and locals share the same {@code VAR_DEFINITION} element type but are filtered out
 * of stub creation (see {@link com.limemojito.oss.mql.psi.stub.type.MQL4GlobalVarElementStubType}).
 */
public interface MQL4GlobalVarElementStub extends StubElement<MQL4VarDefinitionElement> {

    /** The variable name, or {@code null} if the declaration was malformed (no identifier). */
    @Nullable
    String getName();
}
