/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi;

import org.jetbrains.annotations.NonNls;
import org.jetbrains.annotations.NotNull;

import com.intellij.psi.tree.IElementType;
import com.limemojito.oss.mql.MQL4Language;

public class MQL4ElementType extends IElementType {

    public MQL4ElementType(@NotNull @NonNls String debugName) {
        super(debugName, MQL4Language.INSTANCE);
    }

    @Override
    public String toString() {
        return "MQL4ElementType." + super.toString();
    }
}
