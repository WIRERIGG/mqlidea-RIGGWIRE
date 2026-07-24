/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package formatter;

import com.intellij.openapi.command.WriteCommandAction;
import com.intellij.psi.PsiFile;
import com.intellij.psi.codeStyle.CodeStyleManager;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

/**
 * Phase 7 (REVAMP_PLAN.md #Phase 7) formatter tests: the {@code MQL4FormattingModelBuilder} +
 * {@code MQL4Block} indentation model, run through the real platform {@link CodeStyleManager}
 * (the same "Reformat Code" entry point an end user triggers).
 *
 * <p>Core claims under test: an unindented {@code {...}} block gets indented one level; nested
 * blocks indent cumulatively; already-formatted code is a no-op (idempotence -- the constraint
 * REVAMP_PLAN.md Phase 7 calls non-negotiable); and both {@code .mq4} and {@code .mq5} are
 * covered.</p>
 */
public class MQL4FormatterTest extends BasePlatformTestCase {

    private String reformat(String fileName, String code) {
        PsiFile file = myFixture.configureByText(fileName, code);
        CodeStyleManager styleManager = CodeStyleManager.getInstance(getProject());
        WriteCommandAction.runWriteCommandAction(getProject(),
                () -> styleManager.reformatText(file, 0, file.getTextLength()));
        return file.getText();
    }

    public void testUnindentedFunctionBodyGetsIndented() {
        String before = "void OnTick()\n{\nint x = 1;\n}\n";
        String after = reformat("test.mq4", before);
        assertEquals("void OnTick()\n{\n    int x = 1;\n}\n", after);
    }

    public void testReformatIsIdempotent() {
        String once = reformat("test.mq4", "void OnTick()\n{\nint x = 1;\nif(x>0)\n{\nx = 2;\n}\n}\n");
        String twice = reformat("test.mq4", once);
        assertEquals("reformatting already-formatted code must be a no-op", once, twice);
    }

    public void testNestedBlocksIndentCumulatively() {
        String before = "void OnTick()\n{\nif(true)\n{\nint x = 1;\n}\n}\n";
        String after = reformat("test.mq4", before);
        // The default style puts a space between a control keyword and its condition's '(' --
        // see MQL4LanguageCodeStyleSettingsProvider's SPACE_BEFORE_IF_PARENTHESES default.
        String expected = "void OnTick()\n{\n    if (true)\n    {\n        int x = 1;\n    }\n}\n";
        assertEquals(expected, after);
    }

    public void testDoublyNestedBlocksIndentThreeLevels() {
        String before = "void OnTick()\n{\nif(true)\n{\nfor(int i=0;i<1;i++)\n{\nint x = 1;\n}\n}\n}\n";
        String after = reformat("test.mq4", before);
        assertTrue("expected the innermost statement indented three normal-indent levels deep",
                after.contains("\n            int x = 1;\n"));
    }

    public void testAlreadyFormattedMq4CodeIsUnchanged() {
        String code = "void OnTick()\n{\n    int x = 1;\n}\n";
        assertEquals(code, reformat("test.mq4", code));
    }

    public void testAlreadyFormattedMq5CodeIsUnchanged() {
        String code = "void OnTick()\n{\n    int x = 1;\n    if (x > 0)\n    {\n        x = 2;\n    }\n}\n";
        assertEquals(code, reformat("test.mq5", code));
    }

    public void testMq5UnindentedClassBodyGetsIndented() {
        String before = "class CFoo\n{\npublic:\nvoid Run()\n{\nint x = 1;\n}\n};\n";
        String after = reformat("test.mq5", before);
        assertTrue("expected the class body member indented one level",
                after.contains("\n    void Run()\n"));
        assertTrue("expected the method body statement indented two levels",
                after.contains("\n        int x = 1;\n"));
    }

    public void testCommaSpacingAndNoSpaceBeforeSemicolon() {
        String before = "void OnTick()\n{\n    OrderSelect(1,SELECT_BY_POS) ;\n}\n";
        String after = reformat("test.mq4", before);
        assertTrue("expected a space after the comma", after.contains("OrderSelect(1, SELECT_BY_POS)"));
        assertTrue("expected no space before the semicolon", after.contains("SELECT_BY_POS);"));
    }
}
