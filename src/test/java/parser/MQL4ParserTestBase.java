/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.core.CoreApplicationEnvironment;
import com.intellij.lang.LanguageExtensionPoint;
import com.intellij.openapi.extensions.Extensions;
import com.intellij.testFramework.ParsingTestCase;
import org.jetbrains.annotations.NotNull;
import ru.investflow.mql.parser.MQL4ParserDefinition;

public abstract class MQL4ParserTestBase extends ParsingTestCase {

    public MQL4ParserTestBase(String dataPath) {
        this(dataPath, "mq4");
    }

    public MQL4ParserTestBase(String dataPath, String fileExt) {
        super(dataPath, fileExt, new MQL4ParserDefinition());
    }

    @NotNull
    @Override
    protected String getTestDataPath() {
        return "src/test/resources";
    }

    @Override
    protected boolean includeRanges() {
        return true;
    }

    protected void doTest() {
        super.doTest(true);
    }

    @Override
    protected void setUp() throws Exception {
        super.setUp();
        CoreApplicationEnvironment.registerExtensionPoint(Extensions.getRootArea(), "com.intellij.lang.braceMatcher", LanguageExtensionPoint.class);
    }
}
