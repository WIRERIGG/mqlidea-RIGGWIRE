/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

public class PreprocessorTest extends MQL4ParserTestBase {

    public PreprocessorTest() {
        super("parser/preprocessor");
    }

    public void testProperty() {
        doTest();
    }

    public void testPropertyColorList() {
        // #property indicator_colorN accepts a comma-separated color list for DRAW_COLOR_* plots
        // (e.g. clrGold,clrDodgerBlue,...) — the commas must not be reported as unexpected tokens.
        doTest();
    }

    public void testInclude() {
        doTest();
    }

    public void testUndef() {
        doTest();
    }

    public void testIfdef() {
        doTest();
    }

    public void testDefine() {
        doTest();
    }

}
