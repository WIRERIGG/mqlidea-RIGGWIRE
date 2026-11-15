/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.psi.PsiElement;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.UndeclaredIdentifierInspection;
import com.limemojito.oss.mql.inspection.UndefinedFunctionCallInspection;

import java.util.List;

/**
 * Shapes the corpus gate found in code MetaEditor compiles cleanly (the MetaQuotes Standard
 * Library and examples), each written from scratch: every one must stay free of errors.
 */
public class CorpusFalseErrorTest extends BasePlatformTestCase {

    private List<String> errors(String code) {
        myFixture.configureByText("test.mq5", code);
        myFixture.enableInspections(new UndeclaredIdentifierInspection(), new UndefinedFunctionCallInspection());
        return myFixture.doHighlighting(HighlightSeverity.ERROR).stream().map(HighlightInfo::getDescription).toList();
    }

    public void testConstructorStyleDeclarations() {
        assertEquals(List.of(), errors("""
                class CBox { public: int m_v; CBox(int v) { m_v = v; } void Add(int x) { m_v += x; } };
                template<typename T> class CBag { public: T m_v; CBag(int n) { } void Add(T x) { } };
                void OnStart()
                  {
                   CBox box(1);
                   CBag<int> bag(10), other(20);
                   complex z(1, 0);
                   box.Add(z.real > 0 ? 1 : 2);
                   bag.Add(box.m_v);
                   other.Add(bag.m_v);
                  }
                """));
    }

    public void testTemplateParametersAreDeclared() {
        assertEquals(List.of(), errors("""
                template<typename TKey, typename TValue>
                class CPair { public: TKey key; TValue value; };
                class CSorter
                  {
                public:
                   template<typename T> int Lowest(const T &data[], const int count) const
                     {
                      T best = data[0];
                      return count > 0 ? 0 : -1;
                     }
                  };
                template<typename T> T Twice(T x) { T r = x + x; return r; }
                void OnStart() { CPair<int, double> p; Print(p.key, Twice(2)); }
                """));
    }

    public void testMembersInheritedFromABuiltinStructure() {
        assertEquals(List.of(), errors("""
                struct CStamp : public MqlDateTime
                  {
                   void SetDay(const MqlDateTime &v) { day = v.day; mon = v.mon; }
                   int  Hours() { return hour; }
                  };
                void OnStart() { CStamp s; s.year = 2026; Print(s.Hours()); }
                """));
    }

    public void testResourceDeclaresAVariable() {
        assertEquals(List.of(), errors("""
                #resource "Kernels/sort.cl" as string cl_source
                void OnStart() { Print(StringLen(cl_source)); }
                """));
    }

    public void testStaticAfterTheType() {
        assertEquals(List.of(), errors("""
                void OnTick() { datetime static last = 0; last = TimeCurrent(); }
                """));
    }

    public void testMacroWithoutSemicolonBeforeACallIsNotADeclaration() {
        myFixture.configureByText("test.mq5", """
                #define CHECK_DONE if(failed) return;
                bool failed = false;
                void OnStart()
                  {
                   CHECK_DONE
                   Print("next");
                  }
                """);
        assertEmpty(com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(myFixture.getFile(),
                com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement.class).stream()
                .filter(v -> "Print".equals(v.getName())).toList());
    }

    public void testNumberSuffixes() {
        assertEquals(List.of(), errors("""
                void OnStart() { float t = 0.04f + 1.5F; ulong n = 2ull + 3ULL + 4LL + 5u + 6UL; Print(t, n); }
                """));
    }

    public void testTemplateTypedParameters() {
        assertEquals(List.of(), errors("""
                template<typename K, typename V> class CEntry { public: K k; V v; };
                class CTable
                  {
                public:
                   double Sum(const vector<double> &vect) const { return vect.Sum(); }
                   template<typename K, typename V> int CopyTo(CEntry<K,V>*&dst_array[], const int dst_start = 0)
                     {
                      return ArraySize(dst_array) - dst_start;
                     }
                  };
                void OnStart() { }
                """));
    }

    public void testConstInAForHeaderList() {
        assertEquals(List.of(), errors("""
                void OnStart() { int head = 1, size = 3; for(int i = head, const end = head + size; i < end; i++) Print(i); }
                """));
    }

    public void testMultiDimensionalArrayParameters() {
        assertEquals(List.of(), errors("""
                struct SInfo { int id; };
                int History(uint id, uint &count, SInfo &info[][], double grid[][4]) { return info[0][0].id + (int)grid[0][1]; }
                void OnStart() { }
                """));
        assertEmpty(com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(myFixture.getFile(), com.intellij.psi.PsiErrorElement.class));
    }

    public void testBackslashInAQuotedIncludePath() {
        myFixture.addFileToProject("DX/Handle.mqh", "int g_handle = 0;\n");
        myFixture.configureByText("test.mq5", "#include \"DX\\Handle.mqh\"\nvoid OnStart() { Print(g_handle); }\n");
        assertEmpty(com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(myFixture.getFile(), com.intellij.psi.PsiErrorElement.class));
    }

    public void testIndexOperatorResultIsNotTheContainer() {
        assertEquals(List.of(), errors("""
                class CRow { public: complex m_items[]; complex operator[](const int i) const { return m_items[i]; } int Size() { return ArraySize(m_items); } };
                class CDerivedRow : public CRow { };
                bool Finite(CRow &x, CDerivedRow &y) { return MathIsValidNumber(x[0].real) && MathIsValidNumber(y[0].imag) && x.Size() > 0; }
                void OnStart() { CRow rows[]; ArrayResize(rows, 1); Print(rows[0].Size()); }
                """));
        assertEquals(List.of("'NoSuch' - undeclared identifier"), errors("""
                class CPlain { public: int Size() { return 0; } };
                void OnStart() { CPlain items[]; ArrayResize(items, 1); Print(items[0].Size(), items[0].NoSuch); }
                """));
    }

    public void testArrayOfAClassWithIndexOperatorStillChecksElements() {
        assertEquals(List.of("'Missing' - undeclared identifier"), errors("""
                class CRow { public: complex operator[](const int i) const { complex z; return z; } int Size() { return 0; } };
                void OnStart() { CRow rows[]; ArrayResize(rows, 1); Print(rows[0].Size(), rows[0].Missing()); }
                """));
    }

    public void testIndexOperatorReturnTypeIsTheReceiver() {
        assertEquals(List.of("'Nope' - undeclared identifier"), errors("""
                class CLine { public: int m_v[]; void Set(const int i, const int v) { m_v[i] = v; } };
                class CGrid { public: CLine m_lines[]; CLine *operator[](const int i) { return GetPointer(m_lines[i]); } };
                void OnStart() { CGrid g; g[0].Set(1, 2); g[0].Nope(); }
                """));
        PsiElement set = myFixture.getFile().findReferenceAt(myFixture.getFile().getText().indexOf("Set(1") + 1).resolve();
        assertNotNull("g[0].Set resolves through operator[]'s return type", set);
    }

    public void testOperatorParameters() {
        assertEquals(List.of(), errors("""
                class CRowD
                  {
                public:
                   vector<double> m_array;
                   vector<double> operator+(const vector<double> &vect) const { return(m_array + vect); }
                   vector<double> operator-(const CRowD &vect) const          { return(m_array - vect.m_array); }
                   bool           operator==(const double value) const        { return(m_array.Size() > 0 && value == 0); }
                  };
                void OnStart() { }
                """));
    }

    public void testParametersDeclaredByAMacroSignature() {
        assertEquals(List.of(), errors("""
                #define HANDLER_BEGIN(cls) bool cls::OnEvent(const int id,const long& lparam,const double& dparam,const string& sparam) {
                #define HANDLER_END return(false); }
                class CBox { public: bool OnEvent(const int id,const long& lparam,const double& dparam,const string& sparam); void Hide(int a, int b, int c) { } };
                HANDLER_BEGIN(CBox)
                   Hide(id,(int)lparam,(int)dparam);
                HANDLER_END
                """));
    }

    public void testLocalUnionAndStruct() {
        assertEquals(List.of(), errors("""
                long Pack(const uchar &src[])
                  {
                   union res_data
                     {
                      uchar cdata[8];
                      long  ldata;
                     } res;
                   res.ldata = 0;
                   struct SHeader { uint width; uint height; };
                   SHeader header;
                   header.width = (uint)ArraySize(src);
                   return(res.ldata + header.width);
                  }
                """));
    }

    public void testOperatorsHaveNoNamingConvention() {
        myFixture.configureByText("test.mq5", """
                class CVec
                  {
                public:
                   double m_v;
                   double operator+(const CVec &o) const { return(m_v + o.m_v); }
                   double operator[](const int i) const  { return(m_v); }
                   double operatorish() const            { return(m_v); }
                  };
                """);
        myFixture.enableInspections(new com.limemojito.oss.mql.inspection.FunctionNamingConventionInspection());
        List<String> names = myFixture.doHighlighting().stream().map(HighlightInfo::getDescription)
                .filter(d -> d != null && d.contains("PascalCase")).toList();
        assertEquals(List.of("Function 'operatorish' should use PascalCase naming convention"), names);
    }
}
