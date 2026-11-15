/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.intention.IntentionAction;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.MissingIndicatorReleaseInspection;
import com.limemojito.oss.mql.inspection.UncheckedOrderSendInspection;

import java.util.List;

/** The OrderSend and IndicatorRelease quick-fixes: applied, the result is what MetaEditor expects and the warning is gone. */
public class TradingSafetyQuickFixTest extends BasePlatformTestCase {

    private String apply(LocalInspectionTool inspection, String fileName, String code, String needle) {
        myFixture.configureByText(fileName, code);
        myFixture.enableInspections(inspection);
        List<IntentionAction> fixes = myFixture.getAllQuickFixes();
        IntentionAction target = fixes.stream().filter(a -> a.getText().contains(needle)).findFirst().orElse(null);
        assertNotNull("no fix containing '" + needle + "' in " + fixes, target);
        assertNotNull("preview", myFixture.getIntentionPreviewText(target));
        myFixture.launchAction(target);
        return myFixture.getFile().getText();
    }

    public void testOrderSendMql5UsesTheBoolResult() {
        String text = apply(new UncheckedOrderSendInspection(), "ea.mq5",
                "void OnTick()\n  {\n   OrderSend(request, result);\n  }\n", "failure check");
        assertTrue(text, text.contains("   if(!OrderSend(request, result))\n      Print(__FUNCTION__, \": OrderSend failed, error \", GetLastError());"));
        assertEmpty(myFixture.getAllQuickFixes().stream().filter(a -> a.getText().contains("failure check")).toList());
    }

    public void testOrderSendMql4ChecksTheTicket() {
        String text = apply(new UncheckedOrderSendInspection(), "ea.mq4",
                "void OnTick()\n  {\n   OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0);\n  }\n", "failure check");
        assertTrue(text, text.contains("if(OrderSend(Symbol(), OP_BUY, 0.1, Ask, 3, 0, 0) < 0)"));
    }

    public void testReleaseIsAppendedToAnExistingOnDeinit() {
        String text = apply(new MissingIndicatorReleaseInspection(), "ea.mq5", """
                int g_ma, g_rsi;
                int OnInit()
                  {
                   g_ma = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);
                   g_rsi = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);
                   int tmp = iATR(_Symbol, PERIOD_H1, 14);
                   return INIT_SUCCEEDED;
                  }
                void OnDeinit(const int reason)
                  {
                   Comment("");
                  }
                """, "OnDeinit");
        assertTrue(text, text.contains("""
                   Comment("");
                   if(g_ma != INVALID_HANDLE)
                      IndicatorRelease(g_ma);
                   if(g_rsi != INVALID_HANDLE)
                      IndicatorRelease(g_rsi);
                  }
                """));
        assertFalse("a local handle is gone by OnDeinit", text.contains("IndicatorRelease(tmp)"));
        assertEmpty(myFixture.getAllQuickFixes().stream().filter(a -> a.getText().startsWith("Release ")).toList());
    }

    public void testOnDeinitIsAddedWhenMissing() {
        String text = apply(new MissingIndicatorReleaseInspection(), "ea.mq5",
                "int g_ma;\nint OnInit() { g_ma = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n", "OnDeinit");
        assertTrue(text, text.endsWith("void OnDeinit(const int reason)\n  {\n   if(g_ma != INVALID_HANDLE)\n      IndicatorRelease(g_ma);\n  }\n"));
    }

    public void testNoFixWhenOnlyLocalHandlesExist() {
        myFixture.configureByText("ea.mq5", "int OnInit() { int h = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }\n");
        myFixture.enableInspections(new MissingIndicatorReleaseInspection());
        assertEmpty(myFixture.getAllQuickFixes().stream().filter(a -> a.getText().startsWith("Release ")).toList());
    }
}
