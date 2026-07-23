/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Phase 4 (REVAMP_PLAN.md #3b) resolve tests: locals, parameters, same-file function calls,
 * cross-file function calls via #include, and class type references (including a base class
 * name in an inheritance list). Uses BasePlatformTestCase for the same reason
 * MQL5SafetyInspectionTest does: reference resolution needs a real project/module environment
 * (stub indexes, VFS), not just a bare parser.
 */
public class MqlResolveTest extends BasePlatformTestCase {

    private PsiReference referenceAt(String code, String marker) {
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        return myFixture.getReferenceAtCaretPosition();
    }

    public void testResolveLocalVariable() {
        PsiReference ref = referenceAt("void f() { int x = 1; int y = x; }", "x; }");
        assertNotNull("expected a reference at the usage of x", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the local declaration", resolved instanceof MQL4VarDefinitionElement);
        assertEquals("x", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testResolveLocalVariableInNestedBlock() {
        PsiReference ref = referenceAt("void f() { int x = 1; if (true) { int y = x; } }", "x; } }");
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4VarDefinitionElement);
        assertEquals("x", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testResolveParameter() {
        PsiReference ref = referenceAt("void f(int p) { int y = p; }", "p; }");
        assertNotNull("expected a reference at the usage of p", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the parameter", resolved instanceof MQL4FunctionArgElement);
        assertEquals("p", ((MQL4FunctionArgElement) resolved).getName());
    }

    public void testResolveGlobalVariable() {
        PsiReference ref = referenceAt("int g_counter;\nvoid f() { g_counter = 1; }", "g_counter = 1");
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4VarDefinitionElement);
        assertEquals("g_counter", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testResolveSameFileFunctionCall() {
        PsiReference ref = referenceAt("void Helper() { }\nvoid f() { Helper(); }", "Helper();");
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4FunctionElement);
        assertEquals("Helper", ((MQL4FunctionElement) resolved).getFunctionName());
    }

    public void testResolveClassTypeInBaseList() {
        // indexOf would find the declaration's own name first, so this needs lastIndexOf to reach
        // the base-list usage -- configure directly rather than via the referenceAt() helper.
        String code = "class CBase { };\nclass CDerived : CBase { };";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.lastIndexOf("CBase");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference baseRef = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the base class name", baseRef);
        PsiElement resolved = baseRef.resolve();
        assertTrue(resolved instanceof MQL4ClassElement);
        assertEquals("CBase", ((MQL4ClassElement) resolved).getTypeName());
    }

    public void testResolveCrossFileFunctionCallViaInclude() {
        myFixture.addFileToProject("Lib.mqh", "void Shared() { }");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nvoid f() { Shared(); }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        int offset = main.getText().indexOf("Shared();");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference to the cross-file function call", ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4FunctionElement);
        assertEquals("Shared", ((MQL4FunctionElement) resolved).getFunctionName());
        assertEquals("Lib.mqh", resolved.getContainingFile().getName());
    }

    public void testIncludeDirectiveResolvesToFile() {
        PsiFile lib = myFixture.addFileToProject("Lib.mqh", "void Shared() { }");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nvoid f() { Shared(); }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        int offset = main.getText().indexOf("Lib.mqh") + 1;
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a file reference on the include path", ref);
        PsiElement resolved = ref.resolve();
        assertNotNull("expected #include \"Lib.mqh\" to resolve to the file", resolved);
        assertEquals(lib.getVirtualFile(), resolved instanceof PsiFile ? ((PsiFile) resolved).getVirtualFile() : null);
    }

    public void testUnresolvedBuiltinIsSoftNotError() {
        // Print(...) is a documented built-in (mql4-functions.json) that we don't yet resolve to
        // real/synthetic PSI (Phase 6). It must resolve to nothing but be marked "soft" so a
        // future unresolved-reference check never flags it (honesty rule, REVAMP_PLAN.md #3b).
        PsiReference ref = referenceAt("void f() { Print(\"hi\"); }", "Print(");
        assertNotNull(ref);
        assertNull("built-ins aren't resolved to PSI yet", ref.resolve());
        assertTrue("a known built-in must be a soft reference", ref instanceof com.limemojito.oss.mql.reference.MqlReference
                && ((com.limemojito.oss.mql.reference.MqlReference) ref).isSoft());
    }
}
