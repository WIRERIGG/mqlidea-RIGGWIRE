/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.UndefinedFunctionCallInspection;

import java.util.List;

/** MetaEditor's error 256 for global calls: undefined names are flagged, every declared kind is not. */
public class UndefinedFunctionCallInspectionTest extends BasePlatformTestCase {

    private List<String> undefinedIn(String existingPath) {
        myFixture.configureFromTempProjectFile(existingPath);
        myFixture.enableInspections(new UndefinedFunctionCallInspection());
        return myFixture.doHighlighting(HighlightSeverity.ERROR).stream()
                .map(HighlightInfo::getDescription)
                .filter(d -> d != null && d.contains("undeclared identifier"))
                .toList();
    }

    private List<String> undefined(String fileName, String code) {
        myFixture.configureByText(fileName, code);
        myFixture.enableInspections(new UndefinedFunctionCallInspection());
        return myFixture.doHighlighting(HighlightSeverity.ERROR).stream()
                .map(HighlightInfo::getDescription)
                .filter(d -> d != null && d.contains("undeclared identifier"))
                .toList();
    }

    public void testUndefinedCallsAreFlagged() {
        List<String> errors = undefined("test.mq5", "double CalcLotSize(double r) { return r; }\n"
                + "void OnTick() { double lot = CalcLotSise(0.01); NoSuchHelper(); Print(lot); }\n");
        assertEquals(List.of("'CalcLotSise' - undeclared identifier", "'NoSuchHelper' - undeclared identifier"), errors);
    }

    public void testDeclaredAndBuiltinCallsAreClean() {
        String code = """
                #define LOG(x) Print(x)
                #define MAKE(n) void n() {}
                typedef int (*TOp)(int);
                #import "user32.dll"
                int MessageBoxW(int h, string t, string c, int f);
                #import
                int Twice(int v);
                class CBase { public: void Help() {} };
                class CFoo : public CBase
                  {
                public:
                   int v;
                   CFoo(int x) { v = x; Help(); Inner(); }
                   ~CFoo() {}
                   void Inner() {}
                   bool operator==(const CFoo &o) { return v == o.v; }
                  };
                int Apply(TOp op, int v) { return op(v); }
                void OnStart()
                  {
                   LOG("x");
                   CFoo foo(1);
                   CFoo *p = new CFoo(2);
                   p.Inner(); CFoo::Inner();
                   MqlRates r[]; MqlTick t = MqlTick();
                   vector vv = vector::Zeros(3);
                   MqlCalendarValue cv[];
                   CalendarValueHistory(cv, 0, 0);
                   double a = MathArctan2(1, 2) + MathMax(1, 2);
                   int n = Twice(3) + ArraySize(r);
                   printf("%d", n);
                   delete p;
                  }
                int Twice(int v) { return v * 2; }
                """;
        assertEquals(List.of(), undefined("test.mq5", code));
    }

    public void testDatabaseColumnReadersAndSocketsAreBuiltins() {
        String code = """
                void OnStart()
                  {
                   int db = DatabaseOpen("x.sqlite", DATABASE_OPEN_READONLY);
                   int rq = DatabasePrepare(db, "SELECT 1");
                   int i; long n; double d; uchar blob[];
                   DatabaseColumnInteger(rq, 0, i);
                   DatabaseColumnLong(rq, 0, n);
                   DatabaseColumnDouble(rq, 0, d);
                   DatabaseColumnBlob(rq, 0, blob);
                   int s = SocketCreate();
                   if(SocketConnect(s, "example.com", 443, 1000) && SocketTlsHandshake(s, "example.com"))
                      SocketClose(s);
                  }
                """;
        assertEquals(List.of(), undefined("test.mq5", code));
    }

    public void testAMacroFromANonMqlHeaderDeeperInTheChainIsNotGuessed() {
        myFixture.addFileToProject("Std.h", "#define STRUCT_ENUM(S, E) S::E\n");
        myFixture.addFileToProject("Base.mqh", "#include \"Std.h\"\n");
        assertEquals(List.of(), undefined("test.mq5", "#include \"Base.mqh\"\nvoid OnStart() { Print(STRUCT_ENUM(A, B)); }\n"));
        myFixture.addFileToProject("Body.mqh", "void Run() { Print(PTR_ATTRIB(1)); }\n");
        myFixture.addFileToProject("Prog.mq5", "#include \"Std.h\"\n#include \"Body.mqh\"\n");
        assertEquals("a header whose including program reads a non-MQL header", List.of(),
                undefinedIn("Body.mqh"));
        assertEquals("the check still bites without such a header", List.of("'Missing' - undeclared identifier"),
                undefined("plain.mq5", "void OnStart() { Missing(); }\n"));
    }

    public void testNamesDeclaredByTokenPastingMacrosAreClean() {
        String code = """
                #define BOOL_PROP(PropName, OptionName) \\
                   bool is##PropName() const { return true; } \\
                   bool set##PropName(bool value) { return value; }
                class CChart
                  {
                public:
                   BOOL_PROP(ShowOHLC, 1)
                   void              setShow(bool v) { setShowOHLC(v); isShowOHLC(); setShowGrid(v); }
                  };
                """;
        assertEquals("only the name no macro pastes is flagged",
                List.of("'setShowGrid' - undeclared identifier"), undefined("test.mq5", code));
    }

    public void testMql4OnlyFunctionsAreFlaggedInMql5Only() {
        String code = "void OnStart() { double l = OrderLots(); int h = TimeHour(TimeCurrent()); Print(l, h, AccountInfoDouble(ACCOUNT_BALANCE)); }\n";
        assertEquals(List.of("'OrderLots' - undeclared identifier (an MQL4 function, not in MQL5)",
                "'TimeHour' - undeclared identifier (an MQL4 function, not in MQL5)"), undefined("test.mq5", code));
        assertEquals(List.of(), undefined("test.mq4", code));
    }

    public void testOwnWrapperForMql4FunctionIsClean() {
        assertEquals(List.of(), undefined("test.mq5", "double OrderLots() { return 0.1; }\nvoid OnStart() { Print(OrderLots()); }\n"));
    }

    public void testFileWithUnresolvedIncludeIsSkipped() {
        assertEquals(List.of(), undefined("test.mq5", "#include <NoSuch/Header.mqh>\nvoid OnStart() { FromTheHeader(); }\n"));
    }

    public void testFunctionInAnotherProjectFileIsFound() {
        myFixture.addFileToProject("Utils.mqh", "double RiskPercent() { return 1.0; }\n");
        assertEquals(List.of(), undefined("test.mq5", "#include \"Utils.mqh\"\nvoid OnStart() { Print(RiskPercent()); }\n"));
    }
}
