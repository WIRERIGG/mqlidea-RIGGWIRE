/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.editorActions.SimpleTokenSetQuoteHandler;
import com.limemojito.oss.mql.psi.MQL4Elements;

/**
 * Auto-closes and skips over matching quotes for MQL string ({@code "..."}) and char
 * ({@code '...'}) literals — typing an opening quote inserts the closer, and typing the closer at
 * the caret steps over it instead of inserting a duplicate.
 */
public final class MQL4QuoteHandler extends SimpleTokenSetQuoteHandler {

    public MQL4QuoteHandler() {
        super(MQL4Elements.STRING_LITERAL, MQL4Elements.CHAR_LITERAL);
    }
}
