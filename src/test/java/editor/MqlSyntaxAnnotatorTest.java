/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.List;

/**
 * {@code MQL4Annotator} checks that mirror MetaEditor: character-code ranges (error 239, warning 85),
 * extern initializers in MQL5 (error 303), and keyword color for words the lexer leaves IDENTIFIERs.
 */
public class MqlSyntaxAnnotatorTest extends BasePlatformTestCase {

    private List<String> messages(String fileName, String code, HighlightSeverity severity) {
        myFixture.configureByText(fileName, code);
        return myFixture.doHighlighting(severity).stream()
                .filter(info -> info.getSeverity() == severity)
                .map(HighlightInfo::getDescription)
                .toList();
    }

    private List<String> keywords(String fileName, String code) {
        myFixture.configureByText(fileName, code);
        return myFixture.doHighlighting().stream()
                .filter(info -> info.forcedTextAttributesKey == DefaultLanguageHighlighterColors.KEYWORD)
                .map(HighlightInfo::getText)
                .toList();
    }

    public void testCharCodeOutOfRange() {
        List<String> errors = messages("test.mq5", "void OnStart() { ushort a = '\\99999'; ushort b = '\\x10000';"
                + " ushort c = '\\65535'; ushort d = '\\xFFFF'; Print(a, b, c, d); }\n", HighlightSeverity.ERROR);
        assertEquals(List.of("too big for character code (99999), must be in range [0,65535]",
                "only 4 hex digits expected"), errors);
    }

    public void testStringCharCodeOutOfRangeIsAWarning() {
        List<String> warnings = messages("test.mq5", "void OnStart() { Print(\"\\99999\", \"\\65535\", \"\\\\99999\", \"\\x10000\"); }\n",
                HighlightSeverity.WARNING);
        assertEquals(List.of("99999 is too big for character code, must be in range [0,65535]"), warnings);
    }

    public void testExternInitializerIsAnErrorInMql5Only() {
        String code = "extern int g_ext = 3;\nextern int g_plain;\n";
        assertEquals(List.of("extern variable initialization is not allowed"), messages("test.mq5", code, HighlightSeverity.ERROR));
        assertEquals(List.of(), messages("test.mq4", code, HighlightSeverity.ERROR));
    }

    public void testContextualKeywordsAreColored() {
        List<String> words = keywords("test.mq5", "union U pack(4) { int i; float f; };\n"
                + "typedef int (*TOp)(int);\ninput group \"Risk\";\n"
                + "struct S { int a; int b; };\nvoid OnStart() { int group = 1; Print(group, offsetof(S, b)); }\n");
        for (String w : List.of("union", "pack", "typedef", "group", "offsetof")) {
            assertTrue(w + " should be keyword-colored: " + words, words.contains(w));
        }
        assertEquals("only the 'input group' heading is a keyword, not the variable", 1,
                words.stream().filter("group"::equals).count());
    }

    public void testMatrixTypesAreKeywordsInMql5Only() {
        String code = "void OnStart() { vector v = vector::Zeros(3); matrixf m; Print(v.Size(), m.Rows()); }\n";
        assertTrue(keywords("test.mq5", code).containsAll(List.of("vector", "matrixf")));
        assertFalse(keywords("test.mq4", "int vector = 1;\n").contains("vector"));
    }
}
