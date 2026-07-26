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

    public void testIncludeChainEdgeCacheSurvivesUnrelatedEditToRootBody() {
        // B-Stage-1 per-file include-edge cache: A includes B includes C, and a call in A resolves
        // to a function declared in C (a 2-level #include chain). Editing A's *body* (not its
        // #include line) must leave the closure and the resolution byte-identical — B's and C's
        // cached edge lists stay valid; only A's own edges are re-derived (and they are unchanged).
        myFixture.addFileToProject("C.mqh", "void Deep() { }");
        myFixture.addFileToProject("B.mqh", "#include \"C.mqh\"\n");
        PsiFile main = myFixture.addFileToProject("A.mq4",
                "#include \"B.mqh\"\nvoid f() { Deep(); }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());

        int offset = main.getText().indexOf("Deep();");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference to the chained cross-file call", ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4FunctionElement);
        assertEquals("Deep", ((MQL4FunctionElement) resolved).getFunctionName());
        assertEquals("C.mqh", resolved.getContainingFile().getName());

        // Edit only A's body (append a statement inside f()): invalidates A's PSI, not its includes.
        com.intellij.openapi.command.WriteCommandAction.runWriteCommandAction(getProject(), () -> {
            com.intellij.openapi.editor.Document doc = myFixture.getEditor().getDocument();
            int insertAt = doc.getText().indexOf("Deep();") + "Deep();".length();
            doc.insertString(insertAt, " int z = 0;");
            com.intellij.psi.PsiDocumentManager.getInstance(getProject()).commitAllDocuments();
        });

        int offset2 = myFixture.getFile().getText().indexOf("Deep();");
        myFixture.getEditor().getCaretModel().moveToOffset(offset2);
        PsiReference ref2 = myFixture.getReferenceAtCaretPosition();
        assertNotNull("reference still present after the unrelated body edit", ref2);
        PsiElement resolved2 = ref2.resolve();
        assertTrue("resolution unchanged after the unrelated body edit", resolved2 instanceof MQL4FunctionElement);
        assertEquals("Deep", ((MQL4FunctionElement) resolved2).getFunctionName());
        assertEquals("C.mqh", resolved2.getContainingFile().getName());
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

    // ---- Phase 5: member-access resolution -------------------------------------------------

    public void testResolveMemberFieldOnLocalVar() {
        // `CFoo v;` local of a project class -> `v.value` resolves to the field declaration.
        String code = "class CFoo { public:\n int value;\n };\n"
                + "void f() { CFoo v; int y = v.value; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("value; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the member access v.value", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the field declaration", resolved instanceof MQL4VarDefinitionElement);
        assertEquals("value", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testResolveMemberMethodOnLocalVar() {
        String code = "class CFoo { public:\n int GetValue() { return 1; }\n };\n"
                + "void f() { CFoo v; v.GetValue(); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("GetValue();");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the member call v.GetValue()", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the method declaration", resolved instanceof MQL4FunctionElement);
        assertEquals("GetValue", ((MQL4FunctionElement) resolved).getFunctionName());
    }

    public void testResolveMemberFieldOnParameter() {
        String code = "class CFoo { public:\n int value;\n };\n"
                + "void f(CFoo &v) { int y = v.value; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("value; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on parameter member access", ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4VarDefinitionElement);
        assertEquals("value", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testResolveMemberThroughBaseClass() {
        // Stage B: member declared on the base class resolves through inheritance.
        String code = "class CBase { public:\n int baseField;\n };\n"
                + "class CDerived : public CBase { public:\n int derivedField;\n };\n"
                + "void f() { CDerived d; int y = d.baseField; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("baseField; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on inherited member access", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution through the base class", resolved instanceof MQL4VarDefinitionElement);
        assertEquals("baseField", ((MQL4VarDefinitionElement) resolved).getName());
        MQL4ClassElement owner = com.intellij.psi.util.PsiTreeUtil.getParentOfType(resolved, MQL4ClassElement.class);
        assertNotNull(owner);
        assertEquals("resolved field must belong to the base class", "CBase", owner.getTypeName());
    }

    public void testResolveThisMemberInsideMethod() {
        // Stage C: `this.value` inside a method resolves to the class's own field.
        String code = "class CFoo { public:\n int value;\n int GetValue() { return this.value; }\n };";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("value; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on this.value", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the own field", resolved instanceof MQL4VarDefinitionElement);
        assertEquals("value", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testUnresolvedReceiverMemberIsEmptyNoException() {
        // NON-REGRESSION: an unknown receiver leaves the member unresolved (EMPTY), never crashes.
        PsiReference ref = referenceAt("void f() { unknownVar.someField = 1; }", "someField");
        assertNotNull("a reference is still attached to the member leaf", ref);
        assertNull("an unresolvable receiver's member must resolve to nothing", ref.resolve());
    }

    public void testEnumConstantIsNotTreatedAsMemberAccess() {
        // `EnumType::CONST` uses COLON_COLON, not DOT -> must NOT be routed through member access;
        // existing (free-identifier) behavior is unchanged and must not throw.
        String code = "enum Color { RED, GREEN };\nvoid f() { Color c = Color::RED; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("RED; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        // The reference exists (RED is a usage identifier); the point of the test is that resolving
        // it doesn't crash and isn't hijacked by member-access logic. (RED after `::` is not a DOT
        // member, so MqlTypeResolver is never consulted.)
        if (ref != null) {
            ref.resolve();
        }
    }

    public void testFindUsagesOfMethodFindsMemberCallSite() {
        String code = "class CFoo { public:\n int GetValue() { return 1; }\n };\n"
                + "void f() { CFoo v; v.GetValue(); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int declOffset = code.indexOf("GetValue() {");
        PsiElement leaf = file.findElementAt(declOffset);
        MQL4FunctionElement method = com.intellij.psi.util.PsiTreeUtil.getParentOfType(leaf, MQL4FunctionElement.class);
        assertNotNull("expected the method declaration element", method);
        java.util.Collection<com.intellij.psi.PsiReference> refs =
                com.intellij.psi.search.searches.ReferencesSearch.search(method).findAll();
        assertFalse("expected Find Usages to locate the v.GetValue() call site", refs.isEmpty());
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

    // ---- Phase 5 hardening (keystone review fixes) -----------------------------------------

    public void testMemberPrefersNearerLocalShadowingParam() {
        // Fix #2: a nearer custom-typed local shadows an outer same-name parameter — v.x must
        // resolve to the LOCAL's class (CFoo), not the parameter's (CBar); else rename corrupts.
        String code = "class CFoo { public:\n int x;\n };\n"
                + "class CBar { public:\n int x;\n };\n"
                + "void f(CBar &v) { CFoo v; v.x = 1; }";
        myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("x = 1"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4VarDefinitionElement);
        MQL4ClassElement owner = com.intellij.psi.util.PsiTreeUtil.getParentOfType(resolved, MQL4ClassElement.class);
        assertNotNull(owner);
        assertEquals("nearer local CFoo must win over outer param CBar", "CFoo", owner.getTypeName());
    }

    public void testMemberDoesNotMistypeFromMidExpression() {
        // Fix #4: `total = Count * n;` must NOT type `n` as class Count (type token must be at
        // statement start). `n` is an int, so `n.v` resolves to nothing.
        String code = "class Count { public:\n int v;\n };\n"
                + "void f() { int total; int n; total = Count * n; int y = n.v; }";
        myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("v; }"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertTrue("n.v must not mistype n as class Count", ref == null || ref.resolve() == null);
    }

    public void testMemberPrefersIncludedClassOverDuplicate() {
        // Fix #1: with a duplicate class name in an unrelated file, the receiver type resolves to
        // the class reachable via #include, not an arbitrary stub-index pick.
        myFixture.addFileToProject("Good.mqh", "class CPos { public:\n double lots;\n };");
        myFixture.addFileToProject("Backup/Old.mqh", "class CPos { public:\n double lots;\n };");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Good.mqh\"\nvoid f() { CPos p; p.lots = 0.1; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        myFixture.getEditor().getCaretModel().moveToOffset(main.getText().indexOf("lots = 0.1"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertNotNull("expected resolution to the #included CPos.lots", resolved);
        assertEquals("must resolve into the #included file, not the backup",
                "Good.mqh", resolved.getContainingFile().getName());
    }

    public void testResolveBareFieldInsideMethod() {
        // Fix #3: a bare in-method field use (`return value;`) resolves to the class field, so a
        // field rename updates it (previously silently missed → broken code).
        String code = "class CFoo { public:\n int value;\n int Get() { return value; }\n };";
        myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("value; }"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue("bare in-method use must resolve to the field", resolved instanceof MQL4VarDefinitionElement);
        assertEquals("value", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testMemberAmbiguousDuplicateClassGivesNoTarget() {
        // Fix #1: two same-named classes, neither #included → ambiguous → no (mis)resolution
        // (safe: a missed target beats a wrong one, which would drive a corrupting rename).
        myFixture.addFileToProject("A.mqh", "class CPos { public:\n double lots;\n };");
        myFixture.addFileToProject("B.mqh", "class CPos { public:\n double lots;\n };");
        PsiFile main = myFixture.addFileToProject("Main.mq4", "void f() { CPos p; p.lots = 0.1; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        myFixture.getEditor().getCaretModel().moveToOffset(main.getText().indexOf("lots = 0.1"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertTrue("ambiguous duplicate class must not resolve to an arbitrary pick",
                ref == null || ref.resolve() == null);
    }
}
