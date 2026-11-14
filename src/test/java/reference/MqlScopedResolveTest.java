/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.PsiReference;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

/**
 * Scope rules MetaEditor applies that the resolver used to miss: {@code ::} qualifiers (V-2,
 * OOP-2, namespaces), out-of-line method bodies (OOP-1), array and call receivers (O-1),
 * {@code offsetof}, {@code #define} names and parameters (P-1), typedefs (T-4) and {@code a * b;}.
 */
public class MqlScopedResolveTest extends BasePlatformTestCase {

    /** The declaration the reference at {@code use} resolves to, or null when it resolves to nothing. */
    private PsiElement resolve(String code, String use) {
        myFixture.configureByText("test.mq5", code);
        int offset = code.indexOf(use);
        assertTrue("marker not found: " + use, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at " + use, ref);
        return ref.resolve();
    }

    /** Asserts the reference at {@code use} resolves to the declaration whose name starts at {@code decl}. */
    private void assertResolvesTo(String code, String use, String decl) {
        PsiElement target = resolve(code, use);
        assertNotNull("unresolved: " + use, target);
        PsiElement name = target instanceof PsiNameIdentifierOwner owner && owner.getNameIdentifier() != null
                ? owner.getNameIdentifier() : target;
        assertEquals("wrong target for " + use + ": " + target.getText(), code.indexOf(decl), name.getTextOffset());
    }

    public void testGlobalScopeOperatorSkipsTheLocal() {
        String code = "int g_val = 1;\nvoid OnStart() { int g_val = 2; Print(::g_val, g_val); }\n";
        assertResolvesTo(code, "g_val, g_val)", "g_val = 1");
        assertResolvesTo(code, "g_val); }", "g_val = 2");
    }

    public void testStaticMemberDefinitionResolvesToTheClassField() {
        String code = "class CCounter { public: static int s_total; };\nint CCounter::s_total = 0;\n";
        assertResolvesTo(code, "s_total = 0", "s_total; }");
    }

    public void testBaseClassQualifiedCall() {
        String code = "class CBase { public: void Init() { } };\n"
                + "void Init() { }\n"
                + "class CDerived : public CBase { public: void Init() { CBase::Init(); } };\n";
        assertResolvesTo(code, "Init(); }", "Init() { } };");
    }

    public void testNamespaceQualifiedCall() {
        String code = "namespace A { int Twice(int x) { return 2 * x; } }\n"
                + "namespace B { int Twice(int x) { return 3 * x; } }\n"
                + "void OnStart() { Print(B::Twice(1)); }\n";
        assertResolvesTo(code, "Twice(1)", "Twice(int x) { return 3");
    }

    public void testOutOfLineMethodBodySeesClassMembers() {
        String code = "int m_count = 0;\n"
                + "class CBox { private: int m_count; public: int Get(void); CBox *Self(void); };\n"
                + "int CBox::Get(void) { return m_count + this.m_count; }\n"
                + "CBox *CBox::Self(void) { return GetPointer(this); }\n";
        assertResolvesTo(code, "m_count + this", "m_count; public");
        assertResolvesTo(code, "m_count; }\nCBox", "m_count; public");
    }

    public void testArrayElementAndCallReceivers() {
        String code = "class CItem { public: int id; };\n"
                + "class CList { public: CItem m_items[4]; CItem *First(void) { return GetPointer(m_items[0]); } };\n"
                + "void OnStart() { CList list; CItem items[3]; Print(items[1].id, list.First().id, list.m_items[2].id); }\n";
        assertResolvesTo(code, "id, list", "id; };");
        assertResolvesTo(code, "id, list.m_items", "id; };");
        assertResolvesTo(code, "id); }", "id; };");
    }

    public void testOffsetofMember() {
        String code = "struct SRec { int a; double b; };\nint b = 0;\nvoid OnStart() { Print(offsetof(SRec, b)); }\n";
        assertResolvesTo(code, "b)); }", "b; };");
    }

    public void testDefineNameResolvesAndParametersDoNot() {
        String code = "#define MAX_LOTS 5\n#define SQR(a) ((a)*(a))\nint a = 1;\n"
                + "void OnStart() { Print(MAX_LOTS, SQR(2)); }\n";
        assertResolvesTo(code, "MAX_LOTS, SQR", "MAX_LOTS 5");
        assertResolvesTo(code, "SQR(2)", "SQR(a)");
        assertNull("a macro parameter names no declaration", resolve(code, "a)*(a))"));
    }

    public void testTypedefUse() {
        String code = "typedef int (*TOp)(int, int);\nint Add(int x, int y) { return x + y; }\n"
                + "void OnStart() { TOp op = Add; Print(op(1, 2)); }\n";
        assertResolvesTo(code, "TOp op", "TOp)");
    }

    public void testMultiplicationIsNotADeclaration() {
        String code = "void OnStart() { int a = 2, b = 3; a * b; Print(b); }\n";
        assertResolvesTo(code, "b); }", "b = 3");
    }

    public void testPointerDeclarationOfAClassStillDeclares() {
        String code = "class CObj { };\nvoid OnStart() { CObj * p; Print(p == NULL); }\n";
        assertResolvesTo(code, "p == NULL", "p; Print");
    }
}
