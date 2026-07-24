/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.lexer.DelegateLexer;
import com.intellij.lexer.Lexer;
import com.intellij.psi.tree.IElementType;
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.jetbrains.annotations.Nullable;

/**
 * Fixes the lexer's over-eager color-literal rule without regenerating the JFlex lexer.
 *
 * <p>The grammar's {@code color_constant_literal = clr<name> | <name>} matches a BARE web-colour name
 * (e.g. {@code Gold}, {@code Silver}, {@code Lime}, {@code Pink}, {@code Tan}) as
 * {@code COLOR_CONSTANT_LITERAL} everywhere — so you literally could not declare a variable named
 * {@code Gold} (it wasn't an {@code IDENTIFIER}, which mis-coloured it and derailed declaration parsing).
 * This delegate re-maps a bare (non-{@code clr}) colour token back to {@code IDENTIFIER}. The prefixed
 * form ({@code clrGold}) stays a colour literal. A bare name that is genuinely the predefined colour
 * constant still resolves/highlights as a built-in constant via the doc catalog (it's now just an
 * identifier the catalog recognises), so nothing is lost.</p>
 */
public class MqlColorAwareLexer extends DelegateLexer {

    public MqlColorAwareLexer(Lexer delegate) {
        super(delegate);
    }

    @Override
    @Nullable
    public IElementType getTokenType() {
        IElementType type = super.getTokenType();
        if (type == MQL4Elements.COLOR_CONSTANT_LITERAL) {
            CharSequence text = getBufferSequence().subSequence(getTokenStart(), getTokenEnd());
            if (isBareColorName(text)) {
                return MQL4Elements.IDENTIFIER;
            }
        }
        return type;
    }

    /** True for a colour token that is NOT the {@code clr}-prefixed form — i.e. a bare name that must be an identifier. */
    public static boolean isBareColorName(CharSequence text) {
        return !(text.length() >= 3 && text.charAt(0) == 'c' && text.charAt(1) == 'l' && text.charAt(2) == 'r');
    }
}
