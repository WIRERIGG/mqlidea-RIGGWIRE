/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.daemon.GutterMark;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.List;

/**
 * Phase 1 (REVAMP_PLAN.md) test for {@link com.limemojito.oss.mql.editor.MqlEventHandlerLineMarkerProvider}:
 * a defined MQL5 event handler gets the "MT5 entry point" gutter marker; an ordinary function does not.
 */
public class MqlEventHandlerLineMarkerProviderTest extends BasePlatformTestCase {

    private List<GutterMark> gutters(String code) {
        myFixture.configureByText("test.mq5", code);
        myFixture.doHighlighting();
        return myFixture.findAllGutters();
    }

    public void testGutterOnEventHandler() {
        List<GutterMark> gutters = gutters("void OnTick() {\n  int x = 1;\n}\n");
        assertTrue("expected an entry-point gutter marker on OnTick",
                gutters.stream().anyMatch(g -> "MT5 entry point".equals(g.getTooltipText())));
    }

    public void testNoGutterOnPlainFunction() {
        List<GutterMark> gutters = gutters("void Helper() {\n  int x = 1;\n}\n");
        assertTrue("expected no entry-point gutter marker on a plain, non-handler function",
                gutters.stream().noneMatch(g -> "MT5 entry point".equals(g.getTooltipText())));
    }
}
