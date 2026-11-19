/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiReference;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.intellij.usageView.UsageInfo;
import com.limemojito.oss.mql.psi.impl.MQL4TemplateParameterElement;

import java.util.Collection;

/** Template type parameters are declarations scoped to their template (specs/002-template-parameters). */
public class MqlTemplateParameterTest extends BasePlatformTestCase {

    private PsiElement resolveAt(String code, int offset) {
        myFixture.configureByText("test.mq5", code);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at " + offset, ref);
        return ref.resolve();
    }

    /** The {@code n}-th (0-based) occurrence of {@code text}. */
    private static int nth(String code, String text, int n) {
        int at = -1;
        for (int i = 0; i <= n; i++) {
            at = code.indexOf(text, at + 1);
            assertTrue("occurrence " + n + " of " + text, at >= 0);
        }
        return at;
    }

    private void assertParameterAt(String code, int use, int decl) {
        PsiElement target = resolveAt(code, use);
        assertInstanceOf(target, MQL4TemplateParameterElement.class);
        assertEquals(decl, ((MQL4TemplateParameterElement) target).getNameIdentifier().getTextOffset());
    }

    public void testClassTemplateFieldAndMethodUses() {
        String code = "template<typename T>\nclass CList\n  {\n   T m_data[];\n   T At(int i) { T r = m_data[i]; return r; }\n  };\n";
        int decl = nth(code, "T>", 0);
        assertParameterAt(code, nth(code, "T m_data", 0), decl);
        assertParameterAt(code, nth(code, "T At", 0), decl);
        assertParameterAt(code, nth(code, "T r", 0), decl);
    }

    public void testSeveralParametersEachResolve() {
        String code = "template<typename TKey,typename TValue>\nclass CMap\n  {\n   TValue Get(TKey key);\n  };\n";
        assertParameterAt(code, nth(code, "TValue Get", 0), nth(code, "TValue>", 0));
        assertParameterAt(code, nth(code, "TKey key", 0), nth(code, "TKey,", 0));
    }

    public void testFunctionTemplate() {
        String code = "template <typename T>\nT Max(T a, T b) { T r = a; return r; }\n";
        int decl = nth(code, "T>", 0);
        assertParameterAt(code, nth(code, "T Max", 0), decl);
        assertParameterAt(code, nth(code, "T b", 0), decl);
        assertParameterAt(code, nth(code, "T r", 0), decl);
    }

    public void testOutOfLineDefinitionUsesItsOwnHeader() {
        String code = "template<typename T>\nclass CStack { T Pop(void); };\n"
                + "template<typename T>\nT CStack::Pop(void) { T top; return top; }\n";
        int ownHeader = nth(code, "T>", 1);
        assertParameterAt(code, nth(code, "T CStack::Pop", 0), ownHeader);
        assertParameterAt(code, nth(code, "T top", 0), ownHeader);
    }

    public void testClassKeywordForm() {
        String code = "template<class T>\nvoid Swap(T &a, T &b) { T t = a; a = b; b = t; }\n";
        assertParameterAt(code, nth(code, "T t", 0), nth(code, "T>", 0));
    }

    public void testMemberTemplateHidesTheClassParameter() {
        String code = "template<typename T>\nclass CBox\n  {\n   T m_v;\n   template<typename T>\n   void Put(T x) { }\n  };\n";
        assertParameterAt(code, nth(code, "T m_v", 0), nth(code, "T>", 0));
        assertParameterAt(code, nth(code, "T x", 0), nth(code, "T>", 1));
    }

    public void testModifiersBetweenHeaderAndFunction() {
        String code = "class S\n  {\npublic:\n   template<typename D, typename V>\n   static void Extract(D &d) { V a = (V)NULL; }\n  };\n";
        assertParameterAt(code, nth(code, "V a", 0), nth(code, "V>", 0));
    }

    public void testBodyThatParsedApartFromItsSignatureStillSeesTheHeader() {
        String code = "class S\n  {\npublic:\n   template<typename V>\n   static void Extract(unsigned int f = 0) { V a = (V)NULL; }\n  };\n";
        assertParameterAt(code, nth(code, "V a", 0), nth(code, "V>", 0));
    }

    public void testAnEarlierDeclarationEndsTheHeadersReach() {
        String code = "class S\n  {\npublic:\n   template<typename V>\n   void Put(V v) { }\n   void Other() { V x; }\n  };\n";
        PsiElement target = resolveAt(code, nth(code, "V x", 0));
        assertFalse("leaked into the next member", target instanceof MQL4TemplateParameterElement);
    }

    public void testParameterWinsOverAProjectClassOfTheSameName() {
        String code = "class T { };\ntemplate<typename T>\nT Id(T v) { return v; }\n";
        assertParameterAt(code, nth(code, "T v", 0), nth(code, "T>", 0));
    }

    public void testNotVisibleOutsideItsTemplate() {
        String code = "template<typename T>\nT Id(T v) { return v; }\nvoid OnStart() { T x; }\n";
        PsiElement target = resolveAt(code, nth(code, "T x", 0));
        assertFalse("leaked out of its template", target instanceof MQL4TemplateParameterElement);
    }

    public void testFindUsagesStaysInsideItsTemplate() {
        String code = "template<typename T>\nT First(T v) { return v; }\ntemplate<typename T>\nT Second(T v) { return v; }\n";
        myFixture.configureByText("test.mq5", code);
        myFixture.getEditor().getCaretModel().moveToOffset(nth(code, "T>", 0));
        PsiElement decl = myFixture.getElementAtCaret();
        assertInstanceOf(decl, MQL4TemplateParameterElement.class);
        Collection<UsageInfo> usages = myFixture.findUsages(decl);
        assertEquals(2, usages.size());
        int second = nth(code, "template", 1);
        for (UsageInfo u : usages) {
            assertTrue("usage in the other template", u.getNavigationOffset() < second);
        }
    }

    public void testRenameChangesOnlyItsOwnTemplate() {
        String code = "template<typename T>\nT First(T v) { return v; }\ntemplate<typename T>\nT Second(T v) { return v; }\n";
        myFixture.configureByText("test.mq5", code);
        myFixture.getEditor().getCaretModel().moveToOffset(nth(code, "T First", 0));
        myFixture.renameElementAtCaret("TElement");
        myFixture.checkResult("template<typename TElement>\nTElement First(TElement v) { return v; }\ntemplate<typename T>\nT Second(T v) { return v; }\n");
    }

    public void testIncompleteHeaderLeavesTheRestParsing() {
        myFixture.configureByText("test.mq5", "template<typename\nint Add(int a, int b) { return a + b; }\nvoid OnStart() { Add(1, 2); }\n");
        String text = myFixture.getFile().getText();
        int use = text.indexOf("Add(1");
        myFixture.getEditor().getCaretModel().moveToOffset(use);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull(ref);
        assertNotNull("function after an incomplete header no longer resolves", ref.resolve());
    }
}
