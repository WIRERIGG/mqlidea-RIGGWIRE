/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Declarations beyond {@code <builtin type> name (; | =)}: user, qualified and template types,
 * pointers, arrays and comma lists (locals, globals and class fields), and {@code for} loop
 * variables. Every snippet compiles in MetaEditor; before the widened declaration gate these names
 * had no definition, so Go to Declaration, rename and find usages missed them.
 */
public class MqlDeclarationResolveTest extends BasePlatformTestCase {

    /** Configures {@code code}, resolves the reference at {@code marker} and returns the definition. */
    private MQL4VarDefinitionElement definitionAt(String code, String marker) {
        PsiFile file = myFixture.configureByText("test.mq5", code);
        assertNoParseErrors(file);
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at " + marker, ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected a variable definition for " + marker + ", got " + resolved, resolved instanceof MQL4VarDefinitionElement);
        return (MQL4VarDefinitionElement) resolved;
    }

    private static void assertNoParseErrors(PsiFile file) {
        PsiErrorElement error = PsiTreeUtil.findChildOfType(file, PsiErrorElement.class);
        assertNull("unexpected parse error: " + (error == null ? "" : error.getErrorDescription()), error);
    }

    /** Line (1-based) of the definition's name, to tell two same-named declarations apart. */
    private static int lineOf(MQL4VarDefinitionElement def) {
        return def.getContainingFile().getText().substring(0, def.getTextOffset()).split("\n", -1).length;
    }

    public void testUserTypeLocal() {
        MQL4VarDefinitionElement def = definitionAt("struct SCfg { int period; };\nvoid f() { SCfg cfg; cfg.period=1; }", "cfg.period");
        assertEquals("cfg", def.getName());
        assertEquals("SCfg", def.getDeclaredTypeName());
    }

    public void testPointerLocal() {
        assertEquals("ptr", definitionAt("class CItem { };\nvoid f() { CItem *ptr=NULL; delete ptr; }", "ptr; }").getName());
    }

    public void testArrayLocals() {
        String code = "void f() { int fixed[3]; int grid[2][2]={{1,2},{3,4}}; int n[]={1,2,3}; fixed[0]=grid[1][1]+n[0]; }";
        assertEquals("fixed", definitionAt(code, "fixed[0]").getName());
        assertEquals("grid", definitionAt(code, "grid[1][1]").getName());
        assertEquals("n", definitionAt(code, "n[0]").getName());
    }

    public void testCommaListWithoutInitializer() {
        String code = "void f() { int i,j; i=j; }";
        assertEquals("i", definitionAt(code, "i=j").getName());
        assertEquals("j", definitionAt(code, "j; }").getName());
    }

    public void testCommaListWithInitializers() {
        String code = "void f() { int a=1, b=Max(a,2), c; c=a+b; }\nint Max(int x,int y) { return x>y ? x : y; }";
        assertEquals("a", definitionAt(code, "a+b").getName());
        assertEquals("b", definitionAt(code, "b; }").getName());
        assertEquals("c", definitionAt(code, "c=a").getName());
    }

    public void testPointerCommaList() {
        String code = "class CItem { };\nvoid f() { CItem *first, *second; first=second; }";
        assertEquals("second", definitionAt(code, "second; }").getName());
    }

    public void testGlobals() {
        String code = "class CItem { public: int v; };\nCItem g_obj;\nint g_arr[5];\ndouble g_init[]={1.0,2.0};\n"
                + "void f() { g_obj.v=g_arr[0]+(int)g_init[1]; }";
        assertEquals("g_obj", definitionAt(code, "g_obj.v").getName());
        assertEquals("g_arr", definitionAt(code, "g_arr[0]").getName());
        assertEquals("g_init", definitionAt(code, "g_init[1]").getName());
    }

    public void testEnumTypedInput() {
        String code = "enum ENUM_MODE { MODE_FAST, MODE_SLOW };\ninput ENUM_MODE InpMode=MODE_FAST;\nvoid f() { Print(InpMode); }";
        MQL4VarDefinitionElement def = definitionAt(code, "InpMode); }");
        assertEquals("InpMode", def.getName());
        assertEquals("ENUM_MODE", def.getDeclaredTypeName());
    }

    public void testPointerAndArrayFieldsThroughUserTypedLocal() {
        String code = "class CItem { };\nclass CEngine\n  {\npublic:\n   CItem *m_ptr;\n   double m_buf[];\n  };\n"
                + "void f() { CEngine e; e.m_ptr=NULL; ArrayResize(e.m_buf,3); }";
        assertEquals("m_ptr", definitionAt(code, "m_ptr=NULL").getName());
        assertEquals("m_buf", definitionAt(code, "m_buf,3").getName());
    }

    public void testQualifiedAndTemplateTypeNames() {
        String code = "class CStack { };\nvoid f() { CStack<double> s; Data::CRow row; Print(s,row); }";
        assertEquals("CStack", definitionAt(code, "s,row").getDeclaredTypeName());
        assertEquals("CRow", definitionAt(code, "row); }").getDeclaredTypeName());
    }

    public void testForLoopVariableInBody() {
        MQL4VarDefinitionElement def = definitionAt("void f() { for(int i=0; i<2; i++) { Print(i); } }", "i); }");
        assertEquals("i", def.getName());
    }

    public void testForLoopVariableInHeader() {
        assertEquals("i", definitionAt("void f() { for(int i=0; i<2; i++) Print(i); }", "i<2").getName());
    }

    public void testConsecutiveForLoopsEachResolveToTheirOwnVariable() {
        String code = "void f()\n  {\n   for(int i=0; i<2; i++) Print(i);\n   for(int i=0; i<3; i++) Print(i*2);\n  }";
        assertEquals(4, lineOf(definitionAt(code, "i*2")));
        assertEquals(3, lineOf(definitionAt(code, "i);")));
    }

    public void testForLoopCommaList() {
        String code = "void f() { for(int k=0, n=3; k<n; k++) Print(k*n); }";
        assertEquals("k", definitionAt(code, "k*n").getName());
        assertEquals("n", definitionAt(code, "n); }").getName());
    }

    public void testUnterminatedResourceLineDoesNotSwallowTheNextFunction() {
        String code = "#resource \"\\\\Images\\\\dollar.bmp\" as bitmap g_pixels[][]\nvoid OnStart() { Print(1); }";
        PsiFile file = myFixture.configureByText("test.mq5", code);
        assertNoParseErrors(file);
        MQL4FunctionElement onStart = PsiTreeUtil.findChildOfType(file, MQL4FunctionElement.class);
        assertNotNull("OnStart must still be parsed as a function", onStart);
        assertEquals("OnStart", onStart.getFunctionName());
    }

    public void testTypedefAndPrototypesAreNotVariables() {
        String code = "class CFoo { };\ntypedef CFoo CBar;\nCFoo Make(int seed);\nvoid f() { }";
        PsiFile file = myFixture.configureByText("test.mq5", code);
        assertNoParseErrors(file);
        assertNull("no variable should be declared", PsiTreeUtil.findChildOfType(file, MQL4VarDefinitionElement.class));
    }
}
