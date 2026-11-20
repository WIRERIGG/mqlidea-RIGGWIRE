/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

import java.util.ArrayList;
import java.util.List;

/**
 * Valid MQL5 that used to get a false parse error (which also switches off the compiler annotator
 * for the file). Every snippet compiles in MetaEditor with 0 errors and 0 warnings.
 */
public class MqlValidSyntaxTest extends BasePlatformTestCase {

    private PsiFile parse(String code) {
        PsiFile file = myFixture.configureByText("test.mq5", code);
        PsiErrorElement error = PsiTreeUtil.findChildOfType(file, PsiErrorElement.class);
        assertNull("unexpected parse error: " + (error == null ? "" : error.getErrorDescription()
                + " at '" + error.getParent().getText() + "'"), error);
        List<String> bad = new ArrayList<>();
        PsiTreeUtil.processElements(file, e -> {
            if (e.getNode().getElementType() == MQL4Elements.BAD_CHARACTER) bad.add(e.getText());
            return true;
        });
        assertEquals("bad characters", List.of(), bad);
        return file;
    }

    private static List<String> classNames(PsiFile file) {
        List<String> names = new ArrayList<>();
        for (MQL4ClassElement c : PsiTreeUtil.findChildrenOfType(file, MQL4ClassElement.class)) {
            names.add(c.getName());
        }
        return names;
    }

    private PsiElement resolveAt(String code, String marker) {
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at " + marker, ref);
        return ref.resolve();
    }

    // S-1: pack(n) alignment on class / struct, either side of final, before a base list

    public void testPackSpecifier() {
        PsiFile file = parse("class CP pack(8) { public: int a; double b; };\n"
                + "struct SA { int q; };\n"
                + "struct SB pack(2) : SA { char z; };\n"
                + "struct SN pack(1) { char c; };\n"
                + "class C1 pack(4) final { public: int a; };\n"
                + "class C2 final pack(4) { public: int a; };\n"
                + "void OnStart() { CP p; Print(sizeof(p), sizeof(SN)); }\n");
        assertEquals(List.of("CP", "SA", "SB", "SN", "C1", "C2"), classNames(file));
    }

    public void testTemplateArgumentsInANewInitializerStayInIt() {
        // Standard Library SortedMap.mqh: the ',' in <TKey,TValue> doesn't start another declaration
        PsiFile file = parse("void Add(int key, int value) {\n"
                + "  CKeyValuePair<TKey,TValue>*pair=new CKeyValuePair<TKey,TValue>(key,value);\n  Print(pair);\n"
                // sibvic Array.mqh: explicit template arguments on a call
                + "  const int n = Array::Size<int, ITArray<string> *>(arr, INT_MIN), m = Get<CStack<CArray<int>>>(0);\n}\n");
        List<String> declared = com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(file, com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement.class)
                .stream().map(com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement::getName).toList();
        assertEquals(List.of("pair", "n", "m"), declared);
        assertEmpty(com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(file, com.intellij.psi.PsiErrorElement.class));
    }

    public void testPackStaysAnOrdinaryName() {
        // pack is not reserved in MQL5: int pack=1; compiles
        String code = "void OnStart()\n  {\n   int pack=1;\n   Print(pack);\n  }\n";
        parse(code);
        assertNotNull(resolveAt(code, "pack);"));
    }

    // F-2: export on library function definitions and prototypes

    public void testExportedFunctions() {
        String code = "#property library\nint Ex(int v) export;\nint Twice(int v) export\n  {\n   return v*2;\n  }\n"
                + "int Ex(int v) export { return v; }\n";
        PsiFile file = parse(code);
        List<String> functions = new ArrayList<>();
        for (MQL4FunctionElement f : PsiTreeUtil.findChildrenOfType(file, MQL4FunctionElement.class)) {
            functions.add(f.getFunctionName() + (f.isDeclaration() ? ";" : "{}"));
        }
        assertEquals(List.of("Ex;", "Twice{}", "Ex{}"), functions);
        assertNotNull("parameter v resolves inside an exported body", resolveAt(code, "v*2"));
    }

    // P-2: stringize # and token-paste ## in macro bodies

    public void testMacroStringizeAndPaste() {
        parse("#define STR(x)   #x\n#define CAT(a,b) a##b\n"
                + "void OnStart() { Print(STR(hello)); }\n");
    }

    public void testStrayHashOutsideAMacroIsStillAnError() {
        myFixture.configureByText("test.mq5", "void OnStart() { int a = 1 # 2; int b = a ## 3; }\n");
        List<String> errors = new ArrayList<>();
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            errors.add(h.getDescription());
        }
        assertTrue(errors.toString(), errors.contains("'#' is only valid in a #define body"));
        assertTrue(errors.toString(), errors.contains("'##' is only valid in a #define body"));
    }

    public void testUnknownDirectiveIsAnError() {
        // MetaEditor: error 109 "invalid preprocessor command"
        myFixture.configureByText("test.mq5", "#region Helpers\nvoid OnStart() { }\n#endregion\n");
        List<String> errors = new ArrayList<>();
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            errors.add(h.getDescription());
        }
        assertTrue(errors.toString(), errors.contains("Invalid preprocessor command '#region'"));
        assertTrue(errors.toString(), errors.contains("Invalid preprocessor command '#endregion'"));
    }

    public void testMacroOperatorsInsideADefineAreNotErrors() {
        myFixture.configureByText("test.mq5", "#define STR(x)   #x\n#define CAT(a,b) \\\n   a##b\nvoid OnStart() { }\n");
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            fail("unexpected error: " + h.getDescription());
        }
    }

    // T-4/N-1/O-2/S-5: union, typedef, namespace, operator methods, input group

    public void testUnionIsAClassOfKindUnion() {
        PsiFile file = parse("union LongDouble { long l; double d; };\n"
                + "union UP pack(4) { int i; char c[4]; };\n"
                + "void OnStart() { LongDouble u; u.d = 1.0; Print(u.l); }\n");
        assertEquals(List.of("LongDouble", "UP"), classNames(file));
        for (MQL4ClassElement c : PsiTreeUtil.findChildrenOfType(file, MQL4ClassElement.class)) {
            assertEquals(MQL4ClassElement.ClassType.Union, c.getClassType());
        }
    }

    public void testUnionStaysAnOrdinaryNameInMql4() {
        String code = "int union = 1;\nvoid OnStart() { Print(union); }\n";
        PsiFile file = parse(code);
        assertEquals(List.of(), classNames(file));
    }

    public void testInterfaceKindFromAst() {
        PsiFile file = parse("interface IShape { double Area(); };\nabstract class CBase { };\n");
        List<MQL4ClassElement> classes = new ArrayList<>(PsiTreeUtil.findChildrenOfType(file, MQL4ClassElement.class));
        assertEquals(MQL4ClassElement.ClassType.Interface, classes.get(0).getClassType());
        assertEquals(MQL4ClassElement.ClassType.Class, classes.get(1).getClassType());
    }

    public void testFunctionPointerTypedef() {
        String code = "typedef int (*TBinaryOp)(int, int);\n"
                + "int Add(int a, int b) { return a + b; }\n"
                + "class CCalc { public: TBinaryOp m_op; };\n"
                + "void OnStart() { TBinaryOp op = Add; Print(op(1, 2)); }\n";
        PsiFile file = parse(code);
        com.limemojito.oss.mql.psi.impl.MQL4TypedefElement typedef =
                PsiTreeUtil.findChildOfType(file, com.limemojito.oss.mql.psi.impl.MQL4TypedefElement.class);
        assertNotNull(typedef);
        assertEquals("TBinaryOp", typedef.getName());
        assertEquals(List.of("CCalc"), classNames(file));
    }

    public void testNamespaceBodyHoldsDeclarations() {
        PsiFile file = parse("namespace Outer\n  {\n   int g_count = 0;\n"
                + "   namespace Inner { int Twice(int x) { return 2 * x; } }\n"
                + "   class CItem { public: int id; };\n  }\n"
                + "namespace Outer { void Bump() { g_count++; } }\n"
                + "void OnStart() { Print(Outer::Inner::Twice(3)); }\n");
        List<String> ns = new ArrayList<>();
        for (com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement n
                : PsiTreeUtil.findChildrenOfType(file, com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement.class)) {
            ns.add(String.join("::", n.getPath()));
        }
        assertEquals(List.of("Outer", "Outer::Inner", "Outer"), ns);
        assertEquals(List.of("CItem"), classNames(file));
        assertTrue(functionNames(file).containsAll(List.of("Twice", "Bump", "OnStart")));
    }

    public void testOperatorMethods() {
        PsiFile file = parse("class CVec\n  {\npublic:\n   double x;\n"
                + "   bool operator==(const CVec &o) { return x == o.x; }\n"
                + "   double operator[](int i) { return x; }\n"
                + "   void operator=(const CVec &o) { x = o.x; }\n"
                + "   CVec *Clone(void) { return GetPointer(this); }\n"
                + "   CVec *operator!(void);\n  };\n"
                + "CVec *CVec::operator!(void) { return GetPointer(this); }\n");
        assertEquals(List.of("operator==", "operator[]", "operator=", "Clone", "operator!", "operator!"), functionNames(file));
    }

    public void testInputGroup() {
        PsiFile file = parse("input group \"Risk\";\ninput double InpLots = 0.1;\n"
                + "input group \"Signals\"\ninput int InpPeriod = 14;\n");
        int groups = 0;
        for (PsiElement e : PsiTreeUtil.collectElements(file, e -> e.getNode().getElementType() == MQL4Elements.INPUT_GROUP)) {
            groups++;
        }
        assertEquals(2, groups);
    }

    public void testMultiNameDeclarationWithInitializers() {
        String code = "void OnStart() { int a = 1, b = a + 2, c = b * 3; Print(a + b + c); }\n";
        parse(code);
        assertNotNull(resolveAt(code, "c);"));
        assertNotNull(resolveAt(code, "b * 3"));
    }

    private static List<String> functionNames(PsiFile file) {
        List<String> names = new ArrayList<>();
        for (MQL4FunctionElement f : PsiTreeUtil.findChildrenOfType(file, MQL4FunctionElement.class)) {
            names.add(f.getName());
        }
        return names;
    }
}
