/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.psi.search.searches.ReferencesSearch;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.Collection;

/**
 * A header is compiled inside the .mq5 that includes it, so it sees what that file declared or
 * included before it: an EA's LossAnalyzer.mqh reads globals from TrendConfirmation.mqh without
 * including it. Navigation, find usages and rename must follow the same rule.
 */
public class MqlIncluderResolveTest extends BasePlatformTestCase {

    @Override
    protected void setUp() throws Exception {
        super.setUp();
        myFixture.addFileToProject("Trend.mqh", """
                enum ETrend { TREND_UP, TREND_DOWN };
                bool g_bullish = false;
                struct Snapshot { bool active; int ticket; };
                """);
        myFixture.addFileToProject("Analyzer.mqh", """
                Snapshot g_last;
                void Record()
                  {
                   bool up = g_bullish;
                   ETrend t = TREND_UP;
                   g_last.active = up;
                   g_last.ticket = (int)t;
                  }
                """);
        myFixture.addFileToProject("EA.mq5", """
                #include "Trend.mqh"
                #include "Analyzer.mqh"
                void OnTick() { Record(); }
                """);
    }

    private PsiElement resolveIn(String file, String text, int offsetInText) {
        PsiFile f = myFixture.configureFromTempProjectFile(file);
        int offset = f.getText().indexOf(text) + offsetInText;
        PsiReference ref = f.findReferenceAt(offset);
        assertNotNull("no reference at '" + text + "'", ref);
        return ref.resolve();
    }

    public void testHeaderResolvesSiblingHeaderGlobalEnumAndStruct() {
        for (String use : new String[]{"g_bullish;", "ETrend t", "TREND_UP;", "Snapshot g_last"}) {
            PsiElement target = resolveIn("Analyzer.mqh", use, 1);
            assertNotNull(use + " should resolve", target);
            assertEquals(use, "Trend.mqh", target.getContainingFile().getName());
        }
    }

    public void testHeaderResolvesMembersOfSiblingHeaderStruct() {
        PsiElement active = resolveIn("Analyzer.mqh", "active = up", 1);
        assertNotNull(active);
        assertEquals("Trend.mqh", active.getContainingFile().getName());
    }

    public void testFindUsagesOfGlobalReachesTheSiblingHeader() {
        PsiFile trend = myFixture.configureFromTempProjectFile("Trend.mqh");
        PsiElement declaration = resolveIn("Analyzer.mqh", "g_bullish;", 1);
        assertEquals(trend, declaration.getContainingFile());
        Collection<PsiReference> usages = ReferencesSearch.search(declaration).findAll();
        assertTrue(usages.stream().anyMatch(r -> r.getElement().getContainingFile().getName().equals("Analyzer.mqh")));
    }

    public void testNameNotInAnyIncluderStaysUnresolved() {
        myFixture.addFileToProject("Orphan.mqh", "void Use() { int v = g_notDeclaredAnywhere; }\n");
        assertNull(resolveIn("Orphan.mqh", "g_notDeclaredAnywhere", 1));
    }
}
