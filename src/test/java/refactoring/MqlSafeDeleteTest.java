/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package refactoring;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.searches.ReferencesSearch;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.refactoring.MqlRefactoringSupportProvider;

/**
 * Phase 6c: Safe Delete availability + the usages the platform's SafeDeleteProcessor relies on to
 * block deletion. We assert {@code isSafeDeleteAvailable} for functions/classes/fields, and that
 * Find Usages (the member-aware Phase-5 search) reports a call site for a used function but nothing
 * for an unused one -- exactly the signal that makes deletion blocked-vs-allowed.
 */
public class MqlSafeDeleteTest extends BasePlatformTestCase {

    private final MqlRefactoringSupportProvider provider = new MqlRefactoringSupportProvider();

    private MQL4FunctionElement functionNamed(PsiFile file, String name) {
        for (MQL4FunctionElement fn : PsiTreeUtil.findChildrenOfType(file, MQL4FunctionElement.class)) {
            if (name.equals(fn.getFunctionName())) {
                return fn;
            }
        }
        return null;
    }

    public void testSafeDeleteAvailableForTopLevelFunction() {
        PsiFile file = myFixture.configureByText("test.mq4", "void Helper() { }");
        MQL4FunctionElement helper = functionNamed(file, "Helper");
        assertNotNull(helper);
        assertTrue("safe delete must be offered for a top-level function",
                provider.isSafeDeleteAvailable(helper));
    }

    public void testSafeDeleteAvailableForClassAndMember() {
        PsiFile file = myFixture.configureByText("test.mq4",
                "class CFoo { public:\n int value;\n int GetValue() { return value; }\n };");
        MQL4ClassElement cls = PsiTreeUtil.findChildOfType(file, MQL4ClassElement.class);
        MQL4VarDefinitionElement field = PsiTreeUtil.findChildOfType(file, MQL4VarDefinitionElement.class);
        MQL4FunctionElement method = functionNamed(file, "GetValue");
        assertNotNull(cls);
        assertNotNull(field);
        assertNotNull(method);
        assertTrue(provider.isSafeDeleteAvailable(cls));
        assertTrue("class field is a safe-delete target", provider.isSafeDeleteAvailable(field));
        assertTrue("class method is a safe-delete target", provider.isSafeDeleteAvailable(method));
    }

    public void testUsedFunctionReportsUsageSoDeleteWouldBeBlocked() {
        PsiFile file = myFixture.configureByText("test.mq4",
                "void Helper() { }\nvoid f() { Helper(); }");
        MQL4FunctionElement helper = functionNamed(file, "Helper");
        assertNotNull(helper);
        assertTrue("safe delete is available for the function", provider.isSafeDeleteAvailable(helper));
        java.util.Collection<com.intellij.psi.PsiReference> refs = ReferencesSearch.search(helper).findAll();
        assertFalse("a used function must report its call site (SafeDelete would block)", refs.isEmpty());
    }

    public void testUnusedFunctionReportsNoUsageSoDeleteWouldProceed() {
        PsiFile file = myFixture.configureByText("test.mq4",
                "void Unused() { }\nvoid f() { }");
        MQL4FunctionElement unused = functionNamed(file, "Unused");
        assertNotNull(unused);
        assertTrue(provider.isSafeDeleteAvailable(unused));
        java.util.Collection<com.intellij.psi.PsiReference> refs = ReferencesSearch.search(unused).findAll();
        assertTrue("an unused function must report no usages (SafeDelete would proceed)", refs.isEmpty());
    }

    public void testSafeDeleteNotOfferedForArbitraryLeaf() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() { }");
        PsiElement leaf = file.findElementAt(0);
        assertNotNull(leaf);
        assertFalse("a bare token is not a safe-delete target", provider.isSafeDeleteAvailable(leaf));
    }
}
