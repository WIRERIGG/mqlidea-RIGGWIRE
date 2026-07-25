/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package structure;

import com.intellij.lang.Language;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.structure.MqlBreadcrumbsProvider;

import java.util.Arrays;

/**
 * Phase 3b breadcrumbs: from a statement inside a method, the provider yields a
 * {@code Class ▸ Method} chain by walking {@link MqlBreadcrumbsProvider#getParent} and labelling
 * each accepted crumb.
 */
public class MqlBreadcrumbsProviderTest extends BasePlatformTestCase {

    private final MqlBreadcrumbsProvider provider = new MqlBreadcrumbsProvider();

    public void testRegisteredForMql4() {
        assertTrue("provider must claim the MQL4 language",
                Arrays.asList(provider.getLanguages()).contains((Language) MQL4Language.INSTANCE));
    }

    public void testClassMethodChain() {
        String code = "class CFoo { void Bar() { int x = 1; } };";
        PsiFile file = myFixture.configureByText("test.mq4", code);

        PsiElement leaf = file.findElementAt(code.indexOf("int x"));
        assertNotNull(leaf);
        assertFalse("a plain statement leaf is not itself a crumb", provider.acceptElement(leaf));

        // first crumb up: the enclosing method
        PsiElement method = provider.getParent(leaf);
        assertTrue("nearest crumb is the method", method instanceof MQL4FunctionElement);
        assertTrue(provider.acceptElement(method));
        assertEquals("Bar", provider.getElementInfo(method));

        // next crumb up: the enclosing class
        PsiElement clazz = provider.getParent(method);
        assertTrue("next crumb is the class", clazz instanceof MQL4ClassElement);
        assertTrue(provider.acceptElement(clazz));
        assertEquals("CFoo", provider.getElementInfo(clazz));

        // top of the chain
        assertNull("no crumb above the top-level class", provider.getParent(clazz));
    }

    public void testTopLevelFunctionInfo() {
        String code = "int OnInit() { return 0; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);

        PsiElement leaf = file.findElementAt(code.indexOf("return"));
        assertNotNull(leaf);
        PsiElement fn = provider.getParent(leaf);
        assertTrue(fn instanceof MQL4FunctionElement);
        assertEquals("OnInit", provider.getElementInfo(fn));
        assertNull("a top-level function has no enclosing crumb", provider.getParent(fn));
    }
}
