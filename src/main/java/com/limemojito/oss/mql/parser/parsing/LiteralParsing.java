/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing;

import com.intellij.lang.PsiBuilder;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

public class LiteralParsing {

    public static boolean parseLiteral(@NotNull PsiBuilder b) {
        if (MQL4TokenSets.LITERALS.contains(b.getTokenType())) {
            b.advanceLexer();
            return true;
        }
        return false;
    }

}
