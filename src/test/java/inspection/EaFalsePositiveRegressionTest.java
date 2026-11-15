/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.AccountInfoExposureInspection;
import com.limemojito.oss.mql.inspection.ArrayResizeReturnCheckInspection;
import com.limemojito.oss.mql.inspection.MissingArrayPreallocationInspection;
import com.limemojito.oss.mql.inspection.MissingDefaultCaseInspection;
import com.limemojito.oss.mql.inspection.StringConcatInLoopInspection;

import java.util.List;

/**
 * False positives found in RIGGWIRE-EA-LIVE (RiskManager, NEWS, SessionRules, PositionManagement,
 * MQLTA Pattern Detector), each next to the real defect the inspection must still report.
 */
public class EaFalsePositiveRegressionTest extends BasePlatformTestCase {

    private List<HighlightInfo> highlights(LocalInspectionTool tool, String code) {
        myFixture.configureByText("test.mq5", code);
        myFixture.enableInspections(tool);
        return myFixture.doHighlighting(HighlightSeverity.WEAK_WARNING).stream()
                .filter(h -> h.getDescription() != null && h.getSeverity().compareTo(HighlightSeverity.INFORMATION) > 0)
                .toList();
    }

    private List<String> messages(LocalInspectionTool tool, String code, String containing) {
        return highlights(tool, code).stream().map(HighlightInfo::getDescription).filter(d -> d.contains(containing)).toList();
    }

    // ---- ArrayResizeReturnCheck -------------------------------------------------------------

    public void testShrinkRollbackAndCompactionResizesAreNotFlagged() {
        String code = """
                ulong g_t[]; bool g_c[]; double g_p[];
                void Queue(ulong ticket, bool is_close)
                  {
                   int n = ArraySize(g_t);
                   if(ArrayResize(g_t, n + 1) != n + 1 || ArrayResize(g_c, n + 1) != n + 1)
                     {
                      ArrayResize(g_t, n);
                      ArrayResize(g_c, n);
                      return;
                     }
                   g_t[n] = ticket;
                  }
                void Compact()
                  {
                   int n = ArraySize(g_t);
                   int keep = 0;
                   for(int i = 0; i < n; i++)
                     {
                      if(g_t[i] == 0) continue;
                      g_t[keep] = g_t[i];
                      keep++;
                     }
                   ArrayResize(g_t, keep);
                  }
                void RemoveAt(const int index)
                  {
                   int n = ArraySize(g_p);
                   for(int i = index; i < n - 1; i++) g_p[i] = g_p[i + 1];
                   ArrayResize(g_p, n - 1);
                  }
                """;
        assertEquals(List.of(), messages(new ArrayResizeReturnCheckInspection(), code, "ArrayResize"));
    }

    public void testGrowingResizesAreStillFlagged() {
        String code = """
                double g_p[];
                void Add(double v, int extra)
                  {
                   int n = ArraySize(g_p);
                   ArrayResize(g_p, n + 1);
                   g_p[n] = v;
                   int count = 0;
                   count += extra;
                   ArrayResize(g_p, count);
                  }
                """;
        assertEquals(2, messages(new ArrayResizeReturnCheckInspection(), code, "ArrayResize").size());
    }

    // ---- MissingDefaultCase -----------------------------------------------------------------

    public void testSwitchCoveringEveryEnumValueOrFollowedByReturnIsClean() {
        String code = """
                enum EPhase { PHASE_1, PHASE_2, PHASE_FUNDED };
                double Target(EPhase p)
                  {
                   double t = 0;
                   switch(p)
                     {
                      case PHASE_1: t = 10; break;
                      case PHASE_2: case EPhase::PHASE_FUNDED: t = 5; break;
                     }
                   return t;
                  }
                string Label(int code)
                  {
                   switch(code)
                     {
                      case 1: return "one";
                      case 2: return "two";
                     }
                   return "?";
                  }
                """;
        assertEquals(List.of(), messages(new MissingDefaultCaseInspection(), code, "default"));
    }

    public void testSwitchMissingAnEnumValueIsStillFlagged() {
        String code = """
                enum EPhase { PHASE_1, PHASE_2, PHASE_FUNDED };
                void Apply(EPhase p)
                  {
                   double t = 0;
                   switch(p)
                     {
                      case PHASE_1: t = 10; break;
                      case PHASE_2: t = 5; break;
                     }
                   Print(t);
                  }
                """;
        assertEquals(1, messages(new MissingDefaultCaseInspection(), code, "default").size());
    }

    // ---- MissingArrayPreallocation ----------------------------------------------------------

    public void testClearsFixedSizesAndOneGrowPerArrayAreClean() {
        String code = """
                double a[]; double b[]; string s[];
                void Reset() { ArrayResize(a, 0); ArrayResize(b, 0); ArrayResize(s, 0); }
                void Fill(int total, int used)
                  {
                   ArrayResize(a, 0);
                   ArrayResize(a, total);
                   ArrayResize(a, used);
                  }
                void Symbols(string ccy)
                  {
                   if(ccy == "USD") ArrayResize(s, 7);
                   else if(ccy == "EUR") ArrayResize(s, 5);
                   else ArrayResize(s, 3);
                  }
                void Queue() { int n = ArraySize(a); ArrayResize(a, n + 1); ArrayResize(b, n + 1); }
                """;
        assertEquals(List.of(), messages(new MissingArrayPreallocationInspection(), code, "ArrayResize"));
    }

    public void testSameArrayGrowingThreeTimesIsFlagged() {
        String code = """
                double a[];
                void AddThree(double x, double y, double z)
                  {
                   int n = ArraySize(a);
                   ArrayResize(a, n + 1); a[n] = x;
                   ArrayResize(a, n + 2); a[n + 1] = y;
                   ArrayResize(a, n + 3); a[n + 2] = z;
                  }
                """;
        assertEquals(1, messages(new MissingArrayPreallocationInspection(), code, "ArrayResize").size());
    }

    // ---- StringConcatInLoop -----------------------------------------------------------------

    public void testReassignmentAndShortLoopsAreClean() {
        String code = """
                void Parse(string response)
                  {
                   int pos = 0;
                   while(pos >= 0)
                     {
                      string when = response;
                      when = StringSubstr(when, 0, 19);
                      pos = StringFind(response, "x", pos + 1);
                     }
                   string line = "";
                   for(int i = 0; i < 5; i++) line = line + IntegerToString(i) + ",";
                   Print(line);
                  }
                """;
        assertEquals(List.of(), messages(new StringConcatInLoopInspection(), code, "loop"));
    }

    public void testAccumulationInAnOpenEndedLoopIsFlagged() {
        String code = """
                void Join(int n)
                  {
                   string all = "";
                   for(int i = 0; i < n; i++) all = all + IntegerToString(i) + ",";
                   Print(all);
                  }
                """;
        assertEquals(List.of("String built up with + inside a loop — StringAdd(s, x) appends in place"),
                messages(new StringConcatInLoopInspection(), code, "loop"));
    }

    // ---- AccountInfoExposure ----------------------------------------------------------------

    public void testMailToOwnerIsWeakAndWebRequestIsAWarning() {
        String code = """
                void Notify() { string body = AccountName() + " alert"; SendMail("x", body); }
                void Upload()
                  {
                   char data[], result[]; string headers;
                   string body = AccountInfoString(ACCOUNT_NAME);
                   WebRequest("POST", "https://example.com", "", 5000, data, result, headers);
                  }
                """;
        List<HighlightInfo> found = highlights(new AccountInfoExposureInspection(), code).stream()
                .filter(h -> h.getDescription().contains("Account information")).toList();
        assertEquals(2, found.size());
        assertEquals(HighlightSeverity.WEAK_WARNING, found.get(0).getSeverity());
        assertEquals(HighlightSeverity.WARNING, found.get(1).getSeverity());
    }
}
