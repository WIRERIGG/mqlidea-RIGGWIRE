/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.core.CoreApplicationEnvironment;
import com.intellij.lang.LanguageASTFactory;
import com.intellij.lang.LanguageExtensionPoint;
import com.intellij.openapi.extensions.Extensions;
import com.intellij.testFramework.ParsingTestCase;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.parser.MQL4ParserDefinition;
import com.limemojito.oss.mql.psi.impl.MQL4ASTFactory;

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
        // com.intellij.lang.LanguageASTFactory.INSTANCE caches its per-language lookup in a way
        // that survives across this lightweight ParsingTestCase environment and the full
        // BasePlatformTestCase environment used by reference/*Test -- whichever one resolves the
        // MQL4 language's ASTFactory first "wins" for the rest of the JVM. Register the real
        // MQL4ASTFactory here explicitly (the same class plugin.xml registers via
        // lang.ast.factory) so identifier leaves get contributor-reference support
        // (see MQL4IdentifierLeaf) no matter which test class runs first in the suite.
        addExplicitExtension(LanguageASTFactory.INSTANCE, MQL4Language.INSTANCE, new MQL4ASTFactory());
    }
}
