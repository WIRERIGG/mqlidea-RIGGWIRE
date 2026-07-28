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
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
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
        // `EnumType::CONST` uses COLON_COLON, not DOT -> must NOT be routed through member access.
        // RED after `::` is a free usage identifier: it resolves to the enum-field declaration via the
        // closure enum-constant tier (NOT via MqlTypeResolver, which only handles DOT member access).
        String code = "enum Color { RED, GREEN };\nvoid f() { Color c = Color::RED; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf("RED; }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the scoped enum constant Color::RED", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("scoped enum constant must resolve to the enum-field declaration",
                resolved instanceof MQL4EnumFieldElement);
        assertEquals("RED", ((MQL4EnumFieldElement) resolved).getName());
    }

    // ---- v23: enum-constant resolution (bare + scoped) -----------------------------------------

    public void testResolveEnumConstantBareUsage() {
        // A bare use of an enum constant resolves to its MQL4EnumFieldElement declaration.
        String code = "enum Color { RED, GREEN };\nvoid f() { Color c = RED; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        // "RED;" is unique to the usage; the declaration is "RED," in the enum body.
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("RED;"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at the bare usage of RED", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("expected resolution to the enum-field declaration", resolved instanceof MQL4EnumFieldElement);
        assertEquals("RED", ((MQL4EnumFieldElement) resolved).getName());
    }

    public void testResolveEnumConstantCrossFileViaInclude() {
        // Constant declared in a .mqh, used in the .mq4 -> resolves across the #include closure.
        myFixture.addFileToProject("Colors.mqh", "enum Color { RED, GREEN };");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Colors.mqh\"\nvoid f() { int c = RED; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        myFixture.getEditor().getCaretModel().moveToOffset(main.getText().indexOf("RED;"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the cross-file enum constant", ref);
        PsiElement resolved = ref.resolve();
        assertTrue(resolved instanceof MQL4EnumFieldElement);
        assertEquals("RED", ((MQL4EnumFieldElement) resolved).getName());
        assertEquals("Colors.mqh", resolved.getContainingFile().getName());
    }

    public void testLocalVariableShadowsEnumConstant() {
        // A local named the same as an enum constant must still resolve to the LOCAL: the enum-constant
        // tier runs after resolveLocal and never shadows a local.
        String code = "enum Color { RED, GREEN };\nvoid f() { int RED = 1; int y = RED; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        // "RED;" is the usage (`int y = RED;`); "RED," is the enum decl, "RED = 1" is the local decl.
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("RED;"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        PsiElement resolved = ref.resolve();
        assertTrue("local must win over the enum constant of the same name",
                resolved instanceof MQL4VarDefinitionElement);
        assertEquals("RED", ((MQL4VarDefinitionElement) resolved).getName());
    }

    public void testEnumConstantReferenceIsReferenceToDeclaration() {
        // isReferenceTo: from a usage, the reference points back to the declaration (so rename updates
        // usages and safe-delete's ReferencesSearch finds them).
        String code = "enum Color { RED, GREEN };\nvoid f() { Color c = RED; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        // The first "RED" is the declaration identifier inside the enum body.
        PsiElement declLeaf = file.findElementAt(code.indexOf("RED"));
        MQL4EnumFieldElement decl = com.intellij.psi.util.PsiTreeUtil.getParentOfType(declLeaf, MQL4EnumFieldElement.class);
        assertNotNull("expected the enum-field declaration element", decl);
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("RED;"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        assertTrue("the usage reference must recognise the enum-field declaration as its target",
                ref.isReferenceTo(decl));
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

    // ---- v22: enum / global-var stub indexes (stub-vs-AST consistency + cross-file) -----------

    public void testEnumAndGlobalStubIndexesAreConsistentWithAst() {
        // Guard against stub-creation-predicate divergence from the real parser tree shapes.
        // Fixture: a top-level enum, an enum nested in a class, a top-level global var, and a class
        // field of the SAME name as the global.
        String code = "enum EColor { RED, GREEN };\n"
                + "int shared;\n"
                + "class CBox {\n"
                + "   enum EMode { ON, OFF };\n"
                + "   int shared;\n"
                + "   void set() { shared = 1; }\n"
                + "};\n"
                + "void f() { EColor c; shared = 2; }";
        myFixture.addFileToProject("Idx.mq4", code);
        com.intellij.psi.search.GlobalSearchScope all = com.intellij.psi.search.GlobalSearchScope.allScope(getProject());

        // (a) BOTH enums are indexed -- the top-level one and the class-nested one.
        assertFalse("top-level enum EColor must be in the enum index",
                com.limemojito.oss.mql.index.MQL4EnumNameIndex.getInstance().get("EColor", getProject(), all).isEmpty());
        assertFalse("class-nested enum EMode must be in the enum index",
                com.limemojito.oss.mql.index.MQL4EnumNameIndex.getInstance().get("EMode", getProject(), all).isEmpty());

        // (b) the global-var index finds the GLOBAL but NOT the class field of the same name.
        java.util.Collection<MQL4VarDefinitionElement> shared =
                com.limemojito.oss.mql.index.MQL4GlobalVarNameIndex.getInstance().get("shared", getProject(), all);
        assertEquals("exactly one 'shared' (the global) must be indexed -- never the class field",
                1, shared.size());
        MQL4VarDefinitionElement indexed = shared.iterator().next();
        assertNull("the indexed 'shared' must be a file-level global, not a class field",
                com.intellij.psi.util.PsiTreeUtil.getParentOfType(indexed, MQL4ClassElement.class));

        // (c) resolving each usage still lands on the correct element.
        PsiFile main = myFixture.configureByText("Use.mq4", code);
        // global 'shared = 2' inside f() -> the top-level global (not the class field)
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("shared = 2"));
        PsiReference gRef = myFixture.getReferenceAtCaretPosition();
        assertNotNull(gRef);
        PsiElement g = gRef.resolve();
        assertTrue(g instanceof MQL4VarDefinitionElement);
        assertNull("global use must resolve to the file-level global, not a class field",
                com.intellij.psi.util.PsiTreeUtil.getParentOfType(g, MQL4ClassElement.class));
        // enum type 'EColor c' -> the enum element
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("EColor c"));
        PsiReference eRef = myFixture.getReferenceAtCaretPosition();
        assertNotNull(eRef);
        PsiElement e = eRef.resolve();
        assertTrue("enum type use must resolve to the enum element",
                e instanceof com.limemojito.oss.mql.psi.impl.MQL4EnumElement);
        assertEquals("EColor", ((com.limemojito.oss.mql.psi.impl.MQL4EnumElement) e).getTypeName());
    }

    public void testEnumTypeAndGlobalResolveCrossFileViaInclude() {
        // The index + #include-closure path must resolve an enum type and a global variable that
        // are declared in an #included header from the main file.
        myFixture.addFileToProject("Lib.mqh", "enum ELib { X, Y };\nint gLib;");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nvoid f() { ELib e; gLib = 1; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());

        myFixture.getEditor().getCaretModel().moveToOffset(main.getText().indexOf("ELib e"));
        PsiReference enumRef = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the cross-file enum type", enumRef);
        PsiElement enumResolved = enumRef.resolve();
        assertTrue(enumResolved instanceof com.limemojito.oss.mql.psi.impl.MQL4EnumElement);
        assertEquals("ELib", ((com.limemojito.oss.mql.psi.impl.MQL4EnumElement) enumResolved).getTypeName());
        assertEquals("Lib.mqh", enumResolved.getContainingFile().getName());

        myFixture.getEditor().getCaretModel().moveToOffset(main.getText().indexOf("gLib = 1"));
        PsiReference varRef = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the cross-file global variable", varRef);
        PsiElement varResolved = varRef.resolve();
        assertTrue(varResolved instanceof MQL4VarDefinitionElement);
        assertEquals("gLib", ((MQL4VarDefinitionElement) varResolved).getName());
        assertEquals("Lib.mqh", varResolved.getContainingFile().getName());
    }

    public void testIfdefDuplicateGlobalSingleResolvesToFirst() {
        // A cross-platform #ifdef/#else pair declares the SAME global twice. Preprocessor parsing is
        // line-based, so BOTH declarations are direct file children and both land in the global stub
        // index. resolveNonLocal must collapse them to the document-first one (one per file) so a
        // usage still has a single navigable target -- not a poly-resolve chooser (regression guard
        // for the stub-index global path replacing the old per-file putIfAbsent map).
        String code = "#ifdef __MQL5__\n"
                + "int gMode = 1;\n"
                + "#else\n"
                + "int gMode = 2;\n"
                + "#endif\n"
                + "void f() { gMode = 3; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(code.indexOf("gMode = 3"));
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference on the #ifdef-duplicated global", ref);
        PsiElement resolved = ref.resolve();
        assertTrue("duplicate same-file global must single-resolve, not poly-resolve",
                resolved instanceof MQL4VarDefinitionElement);
        assertEquals("gMode", ((MQL4VarDefinitionElement) resolved).getName());
        // The document-first declaration (the #ifdef branch, `gMode = 1`) wins.
        assertTrue("expected the first (document-order) declaration to win",
                resolved.getTextOffset() < code.indexOf("gMode = 2"));
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
