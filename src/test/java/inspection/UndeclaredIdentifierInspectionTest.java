/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.psi.PsiErrorElement;
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

    public void testMisspeltVectorMatrixAndComplexMembersAreFlagged() {
        String code = """
                class CM
                  {
                   matrix<double>    m_matrix;
                   bool              Drop() { return m_matrix.Rowz() > 0; }
                  };
                template<typename T> bool Grow(vector<T> &x, const int n) { return x.Resze(n); }
                void OnStart()
                  {
                   vector v;
                   vectorf f;
                   complex z;
                   Print(v.Summ(), f.Mean(), z.rel);
                  }
                """;
        assertEquals(List.of("'Rowz' - undeclared identifier", "'Resze' - undeclared identifier",
                "'Summ' - undeclared identifier", "'rel' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testValidVectorMatrixAndComplexMembersAreClean() {
        String code = """
                class CM
                  {
                   matrix<double>    m_matrix;
                   bool              Drop() { return m_matrix.Resize(m_matrix.Rows() - 1, m_matrix.Cols()); }
                  };
                template<typename T> bool Grow(vector<T> &x, const int n) { return x.Resize(n); }
                void OnStart()
                  {
                   vector v = vector::Zeros(3);
                   matrix m(2, 2);
                   complex z;
                   z.real = 1;
                   Print(v.Sum(), v.Size(), m.Rows(), m.Transpose().Rows(), z.imag);
                  }
                """;
        assertEquals(List.of(), undeclared("test.mq5", code));
    }

    public void testVectorMembersAreCheckedOnlyWhenTheTypeIsProven() {
        String code = """
                class CFoo { public: int Summ() { return 0; } };
                template<typename T> int Use(T &t) { return t.Summ(); }
                bool Finite(complex &x[], const int n) { return (int)x.Size() >= n; }
                vector Make() { vector r; return r; }
                void Run(vector &v)
                  {
                   CFoo w;
                   vector arr[];
                   Print(Make().Summ(), arr[0].Summ(), w.Summ(), arr.Size());
                  }
                """;
        assertEquals(List.of(), undeclared("test.mq5", code));
    }

    public void testANearerDeclarationHidesAVectorParameter() {
        String code = """
                class CFoo { public: int Other() { return 0; } };
                void Run(vector &v)
                  {
                   if(v.Size() > 0)
                     {
                      CFoo v;
                      Print(v.Other());
                     }
                  }
                """;
        assertEquals(List.of(), undeclared("test.mq5", code));
    }

    public void testNoVectorChecksInMql4() {
        String code = """
                class vector { public: double Summ() { return 0; } };
                void OnStart() { vector v; Print(v.Summ()); }
                """;
        assertEquals(List.of(), undeclared("test.mq4", code));
    }

    public void testVariablesDeclaredAfterAStructBodyAreGlobals() {
        String code = """
                struct Settings
                  {
                   int    SelectedTab;
                   double Risk;
                  } sets, history[3];
                class CPanel
                  {
                   struct Inner { int depth; } inner;
                   int Depth() { return inner.depth; }
                  };
                void OnStart()
                  {
                   sets.SelectedTab = 1;
                   history[0].Risk = sets.Risk;
                   Print(sets.Nope);
                  }
                """;
        assertEquals(List.of("'Nope' - undeclared identifier"), undeclared("test.mq5", code));
        assertEquals("no parse errors", List.of(), PsiTreeUtil.findChildrenOfType(myFixture.getFile(), PsiErrorElement.class).stream()
                .map(PsiErrorElement::getErrorDescription).toList());
    }

    public void testQualifiedParameterTypesParseAndKeepTheirParameters() {
        String code = """
                namespace Shapes { class CBox { public: int w; }; }
                class Outer
                  {
                public:
                   class Item { public: int depth; };
                private:
                   static int  Count(const Item * const &list[]) { return ArraySize(list); }
                   static void Parse(const string &text, int &i, Outer::Item* item, Shapes::CBox &box)
                     {
                      i = StringLen(text) + item.depth + box.w;
                      Print(item.nope);
                     }
                  };
                """;
        assertEquals(List.of("'nope' - undeclared identifier"), undeclared("test.mqh", code));
        assertEquals("no parse errors", List.of(), PsiTreeUtil.findChildrenOfType(myFixture.getFile(), PsiErrorElement.class).stream()
                .map(PsiErrorElement::getErrorDescription).toList());
    }

    public void testForInitWithConstructorArgumentsDeclaresTheVariable() {
        String code = """
                template<typename T> class Iter { public: Iter(int s) {} bool end() { return true; } void next() {} };
                class CCursor { public: CCursor(int s) {} bool end() { return true; } void next() {} };
                void F(int s)
                  {
                   for(Iter<int> it(s); !it.end(); it.next()) { }
                   for(CCursor c(s); !c.end(); c.next()) { }
                   for(int i = 0; i < s; i++) { }
                   Print(nope);
                  }
                """;
        assertEquals("the check still bites", List.of("'nope' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testAMemberOfAnArrayIsNotCheckedAgainstTheElementClass() {
        String code = """
                class CItem { public: int depth; };
                CItem *items[];
                void OnStart()
                  {
                   Print(items.Size(), items[0].depth, items[0].nope);
                  }
                """;
        assertEquals("only the indexed element's member is checked",
                List.of("'nope' - undeclared identifier"), undeclared("test.mq5", code));
    }

    public void testAForLoopVariableIsOutOfScopeAfterTheLoopInMql5() {
        // MetaEditor 5 (build 6230): error 256 on the Print(i) after the loop
        String code = """
                void OnStart()
                  {
                   for(int i = 0; i < 2; i++) { Print(i); }
                   Print(i);
                  }
                """;
        assertEquals(List.of("'i' - undeclared identifier"), undeclared("test.mq5", code));
        assertEquals("a later declaration of the same name still counts",
                List.of(), undeclared("test2.mq5", code.replace("   Print(i);", "   int i = 3;\n   Print(i);")));
        assertEquals("MQL4 isn't judged", List.of(), undeclared("test.mq4", code));
        assertEquals("a loop a macro declares is used beside the macro call", List.of(), undeclared("test3.mq5", """
                #define each(n) for(int it = 0; it < n; it++)
                void OnStart()
                  {
                   each(3)
                     {
                      Print(it);
                     }
                  }
                """));
    }

    public void testImportedModuleQualifiesItsFunctions() {
        String code = """
                #import "kernel32.dll"
                uint GetLastError(void);
                int  CloseHandle(long hObject);
                #import
                void OnStart()
                  {
                   uint err = kernel32::GetLastError();
                   Print(err, user32::MessageBoxW(0, "a", "b", 0));
                  }
                """;
        assertEquals(List.of("'user32' - undeclared identifier"), undeclared("test.mq5", code));
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
