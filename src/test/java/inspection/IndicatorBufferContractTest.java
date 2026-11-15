/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.IndicatorBufferContractInspection;

import java.util.List;

/**
 * The indicator/EA buffer contract. The headline case is the shape of a real bug: an indicator
 * with more buffers than its plots use bound the extra ones as INDICATOR_DATA, the EA's CopyBuffer
 * got -1 (error 4806) and silently fell back.
 */
public class IndicatorBufferContractTest extends BasePlatformTestCase {

    /** Three plots (a line, a color line = 2 buffers, an arrow) use buffers 0-3; 4 and 5 are extra. */
    private static final String INDICATOR = """
            #property indicator_chart_window
            #property indicator_buffers 6
            #property indicator_plots   3
            #property indicator_type1   DRAW_LINE
            #property indicator_type2   DRAW_COLOR_LINE
            #property indicator_type3   DRAW_ARROW
            input int    InpPeriod = 14;
            input double InpLevel  = 70.0;
            double a[], b[], bc[], c[], rsi[], atr[];
            int OnInit()
              {
               SetIndexBuffer(0, a, INDICATOR_DATA);
               SetIndexBuffer(1, b, INDICATOR_DATA);
               SetIndexBuffer(2, bc, INDICATOR_COLOR_INDEX);
               SetIndexBuffer(3, c, INDICATOR_DATA);
               SetIndexBuffer(4, rsi, %s);
               SetIndexBuffer(5, atr, INDICATOR_CALCULATIONS);
               return INIT_SUCCEEDED;
              }
            int OnCalculate(const int rates_total, const int prev_calculated, const datetime &time[], const double &open[],
                            const double &high[], const double &low[], const double &close[], const long &tick_volume[],
                            const long &volume[], const int &spread[]) { return rates_total; }
            """;

    private List<String> warnings(String fileName) {
        myFixture.configureFromTempProjectFile(fileName);
        myFixture.enableInspections(new IndicatorBufferContractInspection());
        return myFixture.doHighlighting(HighlightSeverity.WARNING).stream()
                .filter(h -> h.getSeverity() == HighlightSeverity.WARNING)
                .map(HighlightInfo::getDescription).filter(d -> d != null && d.contains("buffer") || d != null && d.contains("iCustom"))
                .toList();
    }

    private void indicator(String fifthType) {
        myFixture.addFileToProject("Indicators/Cipher.mq5", INDICATOR.formatted(fifthType));
    }

    public void testDataBufferPastThePlotsIsFlaggedInTheIndicator() {
        indicator("INDICATOR_DATA");
        List<String> w = warnings("Indicators/Cipher.mq5");
        assertEquals(w.toString(), 1, w.size());
        assertTrue(w.get(0), w.get(0).contains("INDICATOR_DATA buffer 4") && w.get(0).contains("4806"));
    }

    public void testCalculationsBufferThereIsFine() {
        indicator("INDICATOR_CALCULATIONS");
        assertEmpty(warnings("Indicators/Cipher.mq5"));
    }

    public void testEaReadingTheUnreadableBufferIsFlaggedThroughADefine() {
        indicator("INDICATOR_DATA");
        myFixture.addFileToProject("Experts/BufferIndex.mqh", "#define TC_BUF_RSI 4\n#define TC_BUF_ATR 5\n");
        myFixture.addFileToProject("Experts/Handles.mqh", """
                int g_cipher = INVALID_HANDLE;
                void Create() { g_cipher = iCustom(_Symbol, PERIOD_M5, "Cipher"); }
                """);
        myFixture.addFileToProject("Experts/EA.mq5", """
                #include "BufferIndex.mqh"
                #include "Handles.mqh"
                void OnTick()
                  {
                   double v[];
                   CopyBuffer(g_cipher, TC_BUF_RSI, 1, 1, v);
                   CopyBuffer(g_cipher, TC_BUF_ATR, 1, 1, v);
                   CopyBuffer(g_cipher, 0, 1, 1, v);
                  }
                """);
        List<String> w = warnings("Experts/EA.mq5");
        assertEquals(w.toString(), 1, w.size());
        assertTrue(w.get(0), w.get(0).startsWith("Cipher's INDICATOR_DATA buffer 4"));
    }

    public void testEaReadingAMissingOrUnboundBufferIsFlagged() {
        indicator("INDICATOR_CALCULATIONS");
        myFixture.addFileToProject("Experts/EA.mq5", """
                int h;
                int OnInit() { h = iCustom(_Symbol, PERIOD_M5, "Indicators\\\\Cipher.ex5"); return INIT_SUCCEEDED; }
                void OnTick() { double v[]; CopyBuffer(h, 6, 0, 1, v); CopyBuffer(h, 5, 0, 1, v); }
                """);
        List<String> w = warnings("Experts/EA.mq5");
        assertEquals(w.toString(), 1, w.size());
        assertTrue(w.get(0), w.get(0).contains("declares 6 buffers") && w.get(0).contains("buffer 6"));
    }

    public void testNearestCopyOfTheIndicatorWinsAndATieStaysSilent() {
        indicator("INDICATOR_DATA");
        myFixture.addFileToProject("Backup/Cipher.mq5", INDICATOR.formatted("INDICATOR_CALCULATIONS"));
        myFixture.addFileToProject("Indicators/EA.mq5", "int h = INVALID_HANDLE;\nvoid F() { h = iCustom(_Symbol, PERIOD_M5, \"Cipher\"); double v[]; CopyBuffer(h, 4, 0, 1, v); }\n");
        assertEquals(1, warnings("Indicators/EA.mq5").size());
        myFixture.addFileToProject("Elsewhere/EA2.mq5", "int g = INVALID_HANDLE;\nvoid F() { g = iCustom(_Symbol, PERIOD_M5, \"Cipher\"); double v[]; CopyBuffer(g, 4, 0, 1, v); }\n");
        assertEmpty(warnings("Elsewhere/EA2.mq5"));
    }

    public void testTooManyIcustomParametersIsFlaggedButDefaultsAreFine() {
        indicator("INDICATOR_CALCULATIONS");
        myFixture.addFileToProject("Experts/EA.mq5", """
                int a, b, c;
                int OnInit()
                  {
                   a = iCustom(_Symbol, PERIOD_M5, "Cipher");
                   b = iCustom(_Symbol, PERIOD_M5, "Cipher", 21, 75.0);
                   c = iCustom(_Symbol, PERIOD_M5, "Cipher", 21, 75.0, PRICE_CLOSE);
                   return INIT_SUCCEEDED;
                  }
                """);
        List<String> w = warnings("Experts/EA.mq5");
        assertEquals(w.toString(), 1, w.size());
        assertTrue(w.get(0), w.get(0).contains("has 2 inputs but iCustom passes 3"));
    }

    public void testInputsFromAnIncludedHeaderCount() {
        myFixture.addFileToProject("Clock.mqh", "input group \"Clock\"\ninput int ClockOffset = 2;\ninput bool ClockDst = true;\n");
        myFixture.addFileToProject("Sessions.mq5", "#property indicator_buffers 1\n#property indicator_plots 1\n#property indicator_type1 DRAW_LINE\n"
                + "input int Bars = 10;\n#include \"Clock.mqh\"\ndouble a[];\nint OnInit() { SetIndexBuffer(0, a); return 0; }\n");
        myFixture.addFileToProject("EA.mq5", "int h;\nint OnInit() { h = iCustom(_Symbol, PERIOD_M5, \"Sessions\", 10, 2, true); return 0; }\n");
        assertEmpty(warnings("EA.mq5"));
    }

    public void testAnUnresolvedIncludeMakesTheInputCountUnknown() {
        myFixture.addFileToProject("Sessions.mq5", "#property indicator_buffers 1\n#include \"Missing.mqh\"\ninput int Bars = 10;\n");
        myFixture.addFileToProject("EA.mq5", "int h;\nint OnInit() { h = iCustom(_Symbol, PERIOD_M5, \"Sessions\", 10, 2, true); return 0; }\n");
        assertEmpty(warnings("EA.mq5"));
    }

    public void testUnknownThingsStaySilent() {
        indicator("INDICATOR_DATA");
        myFixture.addFileToProject("Experts/EA.mq5", """
                int h, other;
                void Pick(bool x) { h = iCustom(_Symbol, PERIOD_M5, "Cipher"); if(x) h = iCustom(_Symbol, PERIOD_M5, "Elsewhere"); }
                double Read(int buf) { double v[]; CopyBuffer(h, 4, 0, 1, v); CopyBuffer(other, 4, 0, 1, v); CopyBuffer(h, buf, 0, 1, v); return v[0]; }
                """);
        // h may hold either indicator, other is never an iCustom handle, buf is computed.
        assertEmpty(warnings("Experts/EA.mq5"));
    }

    public void testBindingPastIndicatorBuffersAndTooFewBuffersForThePlots() {
        myFixture.addFileToProject("Small.mq5", """
                #property indicator_buffers 1
                #property indicator_plots   1
                #property indicator_type1   DRAW_COLOR_LINE
                double a[], c[];
                int OnInit() { SetIndexBuffer(0, a); SetIndexBuffer(1, c, INDICATOR_COLOR_INDEX); return INIT_SUCCEEDED; }
                """);
        List<String> w = warnings("Small.mq5");
        assertEquals(w.toString(), 2, w.size());
        assertTrue(w.toString(), w.get(0).contains("draw from 2 buffers but indicator_buffers is 1"));
        assertTrue(w.toString(), w.get(1).contains("Buffer 1 is past indicator_buffers 1"));
    }

    public void testDynamicDrawTypeAndCandlesAreNotGuessed() {
        myFixture.addFileToProject("Candles.mq5", """
                #property indicator_buffers 5
                #property indicator_plots   1
                #property indicator_type1   DRAW_CANDLES
                double o[], h[], l[], c[], x[];
                int OnInit() { SetIndexBuffer(0, o); SetIndexBuffer(1, h); SetIndexBuffer(2, l); SetIndexBuffer(3, c); SetIndexBuffer(4, x); return INIT_SUCCEEDED; }
                """);
        assertEmpty(warnings("Candles.mq5"));
    }

    public void testCommentedOutCodeIsIgnored() {
        myFixture.addFileToProject("Commented.mq5", """
                #property indicator_buffers 1
                #property indicator_plots   1
                #property indicator_type1   DRAW_LINE
                double a[];
                int OnInit() { SetIndexBuffer(0, a); /* SetIndexBuffer(3, a); */ // SetIndexBuffer(4, a);
                   Print("SetIndexBuffer(5, a)"); return INIT_SUCCEEDED; }
                """);
        assertEmpty(warnings("Commented.mq5"));
    }
}
