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

import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

/**
 * Literal forms from the MQL5 reference that used to fall apart into BAD_CHARACTER tokens: datetime
 * constants ({@code D'...'}, Datetime Type) and numeric character codes ({@code \xhhhh}, {@code \d},
 * Character Constants). Every snippet here compiles with 0 errors in MetaEditor.
 */
class MqlLiteralLexerTest {

    private record Token(IElementType type, String text) {
    }

    private static List<Token> lex(String code) {
        Lexer lx = new MqlColorAwareLexer(new FlexAdapter(new MQL4Lexer(null)));
        lx.start(code, 0, code.length(), 0);
        List<Token> out = new ArrayList<>();
        while (lx.getTokenType() != null) {
            if (lx.getTokenType() != MQL4Elements.WHITE_SPACE) {
                out.add(new Token(lx.getTokenType(), code.substring(lx.getTokenStart(), lx.getTokenEnd())));
            }
            lx.advance();
        }
        return out;
    }

    /** The single token lexed from {@code literal}, asserting the whole input is exactly one token. */
    private static Token only(String literal) {
        List<Token> tokens = lex(literal);
        assertThat(tokens).as("tokens of %s", literal).hasSize(1);
        return tokens.get(0);
    }

    @Test
    void datetimeLiteralIsOneToken() {
        // the forms on the Datetime Type page, plus a full date and time
        for (String literal : new String[]{"D'2024.01.15 12:30:00'", "D'1980.07.19 12:30:27'",
                "D'19.07.1980 12:30:27'", "D'19.07.1980 12'", "D'01.01.2004'", "D'2015.01.01 00:00'"}) {
            assertThat(only(literal).type()).isEqualTo(MQL4Elements.DATETIME_LITERAL);
        }
    }

    @Test
    void datetimeLiteralInsideADeclaration() {
        List<Token> tokens = lex("datetime ny=D'2015.01.01 00:00';");
        assertThat(tokens).extracting(Token::type).containsExactly(
                MQL4Elements.DATETIME_KEYWORD, MQL4Elements.IDENTIFIER, MQL4Elements.EQ,
                MQL4Elements.DATETIME_LITERAL, MQL4Elements.SEMICOLON);
    }

    @Test
    void identifierNamedDIsStillAnIdentifier() {
        assertThat(lex("int D=1;")).extracting(Token::type).containsExactly(
                MQL4Elements.INT_KEYWORD, MQL4Elements.IDENTIFIER, MQL4Elements.EQ,
                MQL4Elements.INTEGER_LITERAL, MQL4Elements.SEMICOLON);
    }

    @Test
    void characterConstantIsOneToken() {
        for (String literal : new String[]{"'\\x41'", "'\\xAE'", "'\\x10'", "'\\x00A9'", "'\\169'", "'\\0'", "'\\65535'",
                "'\\n'", "'\\\\'", "'\\''", "'A'"}) {
            assertThat(only(literal).type()).isEqualTo(MQL4Elements.CHAR_LITERAL);
        }
    }

    @Test
    void stringWithEscapesIsOneToken() {
        for (String literal : new String[]{"\"Copyright\\t\\x00A9\"", "\"\\x41\\x42\"", "\"code \\169 here\"",
                "\"C:\\\\Program Files\\\\MetaTrader 5\"", "\"a\\\"b\\n\""}) {
            assertThat(only(literal).type()).isEqualTo(MQL4Elements.STRING_LITERAL);
        }
    }

    @Test
    void codeAfterAHexEscapedStringLexesNormally() {
        List<Token> tokens = lex("Print(\"\\x00A9\");int x=1;");
        assertThat(tokens).extracting(Token::type).doesNotContain(MQL4Elements.BAD_CHARACTER);
        assertThat(tokens).extracting(Token::text).contains("\"\\x00A9\"", "x");
    }

    @Test
    void leadingZeroIntegerIsOneToken() {
        // MetaEditor accepts zero-padded decimals (enum ENUM_HOUR { h07=07, h08=08 } in MQLTA Utils.mqh)
        for (String literal : new String[]{"00", "07", "08", "09", "0012", "0", "10"}) {
            assertThat(only(literal).type()).isEqualTo(MQL4Elements.INTEGER_LITERAL);
        }
        assertThat(lex("enum E { h00=00, h08=08 };")).extracting(Token::type).containsExactly(
                MQL4Elements.ENUM_KEYWORD, MQL4Elements.IDENTIFIER, MQL4Elements.L_CURLY_BRACKET,
                MQL4Elements.IDENTIFIER, MQL4Elements.EQ, MQL4Elements.INTEGER_LITERAL, MQL4Elements.COMMA,
                MQL4Elements.IDENTIFIER, MQL4Elements.EQ, MQL4Elements.INTEGER_LITERAL,
                MQL4Elements.R_CURLY_BRACKET, MQL4Elements.SEMICOLON);
    }

    /**
     * These keywords used to be recognised only by a hand-written fallback patched into the generated
     * lexer; after regenerating from MQL4Lexer.flex they must come from the DFA itself.
     */
    @Test
    void formerlyPatchedKeywordsComeFromTheGeneratedLexer() {
        for (String pair : new String[]{"final,FINAL_KEYWORD", "sinput,SINPUT_KEYWORD", "abstract,ABSTRACT_KEYWORD",
                "override,OVERRIDE_KEYWORD", "namespace,NAMESPACE_KEYWORD", "dynamic_cast,DYNAMIC_CAST_KEYWORD",
                "interface,INTERFACE_KEYWORD", "template,TEMPLATE_KEYWORD", "typename,TYPENAME_KEYWORD"}) {
            String word = pair.split(",")[0];
            String type = pair.split(",")[1];
            assertThat(only(word).type().toString()).endsWith(type);
        }
    }

    @Test
    void macroOperatorsAndExportLexAsTokens() {
        assertThat(lex("#define CAT(a,b) a##b")).extracting(Token::type).containsExactly(
                MQL4Elements.DEFINE_PP_KEYWORD, MQL4Elements.IDENTIFIER, MQL4Elements.L_ROUND_BRACKET,
                MQL4Elements.IDENTIFIER, MQL4Elements.COMMA, MQL4Elements.IDENTIFIER,
                MQL4Elements.R_ROUND_BRACKET, MQL4Elements.IDENTIFIER, MQL4Elements.PP_CONCAT,
                MQL4Elements.IDENTIFIER);
        assertThat(lex("#x")).extracting(Token::type)
                .containsExactly(MQL4Elements.PP_STRINGIZE, MQL4Elements.IDENTIFIER);
        // directives stay the longer match
        assertThat(only("#property").type()).isEqualTo(MQL4Elements.PROPERTY_PP_KEYWORD);
        assertThat(only("#include").type()).isEqualTo(MQL4Elements.INCLUDE_PP_KEYWORD);
        assertThat(only("export").type()).isEqualTo(MQL4Elements.EXPORT_KEYWORD);
        // pack is not reserved in MQL5
        assertThat(only("pack").type()).isEqualTo(MQL4Elements.IDENTIFIER);
    }

    /** T-3: {@code 5.} and {@code 5.e2} are doubles (MetaEditor compiles both), not an integer and a dot. */
    @Test
    void trailingDotFloatIsOneDouble() {
        for (String literal : new String[]{"5.", "5.e2", "5.E-1", "10."}) {
            assertThat(only(literal).type()).as(literal).isEqualTo(MQL4Elements.DOUBLE_LITERAL);
        }
        assertThat(lex("1.+2.")).extracting(Token::type).containsExactly(
                MQL4Elements.DOUBLE_LITERAL, MQL4Elements.PLUS, MQL4Elements.DOUBLE_LITERAL);
    }

    /** An out-of-range character code stays one CHAR_LITERAL so the annotator can report it. */
    @Test
    void outOfRangeCharacterCodeIsStillOneToken() {
        for (String literal : new String[]{"'\\99999'", "'\\65536'", "'\\x10000'"}) {
            assertThat(only(literal).type()).as(literal).isEqualTo(MQL4Elements.CHAR_LITERAL);
        }
    }
}
