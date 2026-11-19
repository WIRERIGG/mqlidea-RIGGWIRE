/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package lexer;

import com.intellij.lexer.FlexAdapter;
import com.intellij.lexer.Lexer;
import com.intellij.psi.tree.IElementType;
import com.limemojito.oss.mql.MQL4Lexer;
import com.limemojito.oss.mql.MqlColorAwareLexer;
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class MqlColorAwareLexerTest {

    private static IElementType typeOf(String code, String target) {
        Lexer lx = new MqlColorAwareLexer(new FlexAdapter(new MQL4Lexer(null)));
        lx.start(code, 0, code.length(), 0);
        while (lx.getTokenType() != null) {
            if (target.contentEquals(code.subSequence(lx.getTokenStart(), lx.getTokenEnd()))) {
                return lx.getTokenType();
            }
            lx.advance();
        }
        return null;
    }

    @Test
    void bareColorNameLexesAsIdentifier() {
        // the bug: you could not name a variable `Gold`
        assertThat(typeOf("double Gold = 1.0;", "Gold")).isEqualTo(MQL4Elements.IDENTIFIER);
    }

    @Test
    void clrPrefixedStaysColorLiteral() {
        assertThat(typeOf("color c = clrGold;", "clrGold")).isEqualTo(MQL4Elements.COLOR_CONSTANT_LITERAL);
    }

    @Test
    void otherBareColorNamesAreIdentifiers() {
        for (String name : new String[]{"Silver", "Lime", "Pink", "Tan", "Green", "Navy"}) {
            assertThat(typeOf("int " + name + ";", name)).as(name).isEqualTo(MQL4Elements.IDENTIFIER);
        }
    }

    @Test
    void unsignedBeforeAnIntegerTypeIsAModifier() {
        // MetaEditor 5 takes 'unsigned int' (build 6230); the parser skips the modifier
        for (String code : new String[]{"unsigned int x;", "unsigned  long x;", "void F(int a, unsigned char c)", "unsigned\nshort s;"}) {
            assertThat(typeOf(code, "unsigned")).as(code).isEqualTo(MQL4Elements.UNSIGNED_KEYWORD);
        }
    }

    @Test
    void unsignedAnywhereElseStaysAnIdentifier() {
        for (String code : new String[]{"int unsigned;", "unsigned x;", "unsigned integer;", "unsigned int_t;", "unsigned"}) {
            assertThat(typeOf(code, "unsigned")).as(code).isEqualTo(MQL4Elements.IDENTIFIER);
        }
    }
}
