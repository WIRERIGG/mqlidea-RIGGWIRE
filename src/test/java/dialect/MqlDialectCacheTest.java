/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package dialect;

import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.MqlDialect;

/**
 * M3 regression: the project-dialect {@code CachedValue} in {@code MqlDialect} is computed from file
 * CONTENT (which {@code .mq4}/{@code .mq5} sources exist, via {@code FilenameIndex}) but used to depend
 * only on {@code ProjectRootModificationTracker}, which a mere file ADD does not bump. So adding the
 * first {@code .mq5} to a {@code .mq4}-only project left {@code .mqh} headers classified as MQL4 until
 * restart. Adding {@code PsiModificationTracker.MODIFICATION_COUNT} to the dependency list fixes it.
 */
public class MqlDialectCacheTest extends BasePlatformTestCase {

    public void testHeaderDialectRefreshesWhenFirstMq5IsAdded() {
        myFixture.addFileToProject("Expert.mq4", "void OnStart() {}\n");
        PsiFile header = myFixture.addFileToProject("Lib.mqh", "void Helper() {}\n");

        // A .mqh in a .mq4-only project inherits MQL4 (its sole dialect).
        assertEquals(MqlDialect.Kind.MQL4, MqlDialect.kind(header));

        // Adding the first .mq5 must flip the header to MQL5 WITHOUT an IDE restart.
        myFixture.addFileToProject("Strategy.mq5", "void OnTick() {}\n");

        assertEquals("adding the first .mq5 must invalidate the stale MQL4 header classification",
                MqlDialect.Kind.MQL5, MqlDialect.kind(header));
    }
}
