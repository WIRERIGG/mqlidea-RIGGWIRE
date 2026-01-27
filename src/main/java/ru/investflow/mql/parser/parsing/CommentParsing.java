/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.parser.parsing;

import com.intellij.lang.PsiBuilder;
import ru.investflow.mql.psi.MQL4Elements;

public class CommentParsing implements MQL4Elements {

    public static boolean parseComment(PsiBuilder b) {
        if (b.getTokenType() != LINE_COMMENT && b.getTokenType() != BLOCK_COMMENT) {
            return false;
        }
        b.advanceLexer();
        return true;
    }
}
