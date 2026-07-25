/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package refactoring;

import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.refactoring.MqlIntroduceVariableHandler;

/**
 * Phase 6b: Extract Variable. Selects an expression, invokes the handler programmatically, and
 * asserts the {@code <type> name = expr;} declaration appears on the line above and the occurrence
 * is replaced with the name.
 */
public class MqlIntroduceVariableTest extends BasePlatformTestCase {

    private void extractSelection(String code, String selectText) {
        myFixture.configureByText("test.mq4", code);
        int start = code.indexOf(selectText);
        assertTrue("selection text not found: " + selectText, start >= 0);
        myFixture.getEditor().getSelectionModel().setSelection(start, start + selectText.length());
        new MqlIntroduceVariableHandler().invoke(getProject(), myFixture.getEditor(), myFixture.getFile(), null);
    }

    public void testExtractArithmeticExpressionIntroducesDoubleDeclaration() {
        extractSelection("void f() {\n    double sl = 20*Point;\n}", "20*Point");
        myFixture.checkResult("void f() {\n"
                + "    double extracted = 20*Point;\n"
                + "    double sl = extracted;\n"
                + "}");
    }

    public void testExtractStringExpressionInfersStringType() {
        extractSelection("void f() {\n    Print(\"hello\");\n}", "\"hello\"");
        myFixture.checkResult("void f() {\n"
                + "    string extracted = \"hello\";\n"
                + "    Print(extracted);\n"
                + "}");
    }

    public void testExtractIntegerLiteralInfersIntType() {
        extractSelection("void f() {\n    int n = 42;\n}", "42");
        myFixture.checkResult("void f() {\n"
                + "    int extracted = 42;\n"
                + "    int n = extracted;\n"
                + "}");
    }

    public void testNoSelectionIsNoOp() {
        myFixture.configureByText("test.mq4", "void f() {\n    int n = 42;\n}");
        // No selection set.
        new MqlIntroduceVariableHandler().invoke(getProject(), myFixture.getEditor(), myFixture.getFile(), null);
        myFixture.checkResult("void f() {\n    int n = 42;\n}");
    }

    public void testInferTypeToken() {
        assertEquals("string", MqlIntroduceVariableHandler.inferTypeToken("\"x\""));
        assertEquals("int", MqlIntroduceVariableHandler.inferTypeToken("42"));
        assertEquals("int", MqlIntroduceVariableHandler.inferTypeToken("-7"));
        assertEquals("double", MqlIntroduceVariableHandler.inferTypeToken("20*Point"));
        assertEquals("double", MqlIntroduceVariableHandler.inferTypeToken("3.14"));
    }
}
