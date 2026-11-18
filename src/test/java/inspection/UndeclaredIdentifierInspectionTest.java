/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.UndeclaredIdentifierInspection;

import java.util.List;

/** MetaEditor's error 256 for names that aren't global calls: variables, constants, types and members. */
public class UndeclaredIdentifierInspectionTest extends BasePlatformTestCase {

    private List<String> undeclared(String fileName, String code) {
        myFixture.configureByText(fileName, code);
        myFixture.enableInspections(new UndeclaredIdentifierInspection());
        return myFixture.doHighlighting(HighlightSeverity.ERROR).stream()
                .map(HighlightInfo::getDescription)
                .filter(d -> d != null && d.contains("undeclared identifier"))
                .toList();
    }

    public void testUndeclaredVariableAndMemberAreFlagged() {
        String code = """
                class CRisk { public: double m_max; double Lots() { return 1; } };
                CRisk risk;
                void OnTick()
                  {
                   double lots = risk.Lot();
                   if(lots > MaxLots) Print(lots, risk.m_mx);
                  }
                """;
        assertEquals(List.of("'Lot' - undeclared identifier", "'MaxLots' - undeclared identifier",
                "'m_mx' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testTemplateParameterNameOutsideItsTemplateIsFlagged() {
        String code = """
                template<typename T> T Twice(T x) { T r = x + x; return r; }
                void OnStart() { T stray = 1; Print(Twice(2), stray); }
                """;
        assertEquals(List.of("'T' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testDeclaredNamesBuiltinsAndPreprocessorAreClean() {
        String code = """
                #property copyright "x"
                #property indicator_buffers 2
                #define LIMIT 5
                #define SQ(v) ((v) * (v))
                enum ESide { SIDE_BUY, SIDE_SELL };
                input ENUM_TIMEFRAMES InpTf = PERIOD_M15;
                class CBase { public: int m_id; };
                class CPos : public CBase
                  {
                public:
                   double m_lots;
                   void Set(double lots) { m_lots = lots; m_id = LIMIT; this.m_lots = lots; }
                  };
                int g_count = 0;
                void Draw(string name, color clr = clrNONE, int anchor = ANCHOR_LEFT_UPPER, CPos *pos = NULL)
                  {
                   Print(name, clr, anchor, pos.m_lots, pos.m_id);
                  }
                void OnStart()
                  {
                   ESide side = SIDE_BUY;
                   CPos p;
                   p.Set(SQ(2));
                   MqlRates r[];
                   double pt = _Point * SymbolInfoDouble(_Symbol, SYMBOL_BID);
                   int s = 1;
                   #ifdef DEBUG
                      string timing = (s > 0) ? "Up" : "Re";
                      Print(timing);
                   #endif
                   Print(side, p.m_lots, r[0].close, pt, g_count, InpTf, INDICATOR_DATA, _Digits);
                  }
                """;
        assertEquals(List.of(), undeclared("test.mq5", code));
    }

    public void testMemberOfClassWithUnknownBaseIsNotChecked() {
        String code = "class CMy : public CNotDeclaredHere { public: int a; };\n"
                + "void OnStart() { CMy m; Print(m.a, m.FromTheBase); }\n";
        // the missing base itself is an error; the members it might supply are not checked
        assertEquals(List.of("'CNotDeclaredHere' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testHeaderSeesWhatItsIncluderDeclared() {
        myFixture.addFileToProject("Settings.mqh", "int g_magic = 42;\n");
        myFixture.addFileToProject("Uses.mqh", "void Show() { Print(g_magic, g_fromMain); }\n");
        myFixture.addFileToProject("Main.mq5", "int g_fromMain = 1;\n#include \"Settings.mqh\"\n#include \"Uses.mqh\"\nvoid OnStart() { Show(); }\n");
        myFixture.configureFromTempProjectFile("Uses.mqh");
        myFixture.enableInspections(new UndeclaredIdentifierInspection());
        assertEquals(List.of(), myFixture.doHighlighting(HighlightSeverity.ERROR).stream()
                .map(HighlightInfo::getDescription).filter(d -> d != null && d.contains("undeclared")).toList());
    }

    public void testBuiltinStructMembersAreCheckedByName() {
        String code = """
                MqlTick g_last;
                void OnStart()
                  {
                   MqlDateTime dt;
                   TimeToStruct(TimeCurrent(), dt);
                   MqlRates rates[];
                   CopyRates(_Symbol, PERIOD_M5, 0, 2, rates);
                   MqlCalendarValue v;
                   Print(dt.hour, dt.day_of_week, rates[0].close, g_last.time_msc, v.HasActualValue());
                   Print(dt.hours, rates[1].closee, g_last.spread);
                  }
                """;
        assertEquals(List.of("'hours' - undeclared identifier", "'closee' - undeclared identifier",
                "'spread' - undeclared identifier"), undeclared("test.mq5", code));
    }
}
