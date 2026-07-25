/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.reference.MqlTypeDeclarationProvider;

/**
 * Go To Type Declaration (Ctrl+Shift+B) for MQL: from a variable/parameter (or a use of one) the
 * provider returns the declaration of its class type; primitives/unknowns yield nothing (no wrong
 * jump). Calls the provider directly on the identifier leaf, mirroring MqlRunLineMarkerContributorTest.
 */
public class MqlTypeDeclarationProviderTest extends BasePlatformTestCase {

    private PsiElement leafAt(PsiFile file, String code, String marker) {
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        return file.findElementAt(offset);
    }

    public void testGotoTypeOnLocalVarUsageReturnsClass() {
        String code = "class CFoo { public:\n int value;\n };\n"
                + "void f() { CFoo v; v.value = 1; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement leaf = leafAt(file, code, "v.value"); // the `v` usage
        PsiElement[] types = new MqlTypeDeclarationProvider().getSymbolTypeDeclarations(leaf);
        assertNotNull("expected a type declaration for a CFoo-typed local", types);
        assertEquals(1, types.length);
        assertTrue(types[0] instanceof MQL4ClassElement);
        assertEquals("CFoo", ((MQL4ClassElement) types[0]).getTypeName());
    }

    public void testGotoTypeOnParameterUsageReturnsClass() {
        String code = "class CBar { public:\n int n;\n };\n"
                + "void f(CBar &b) { b.n = 2; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement leaf = leafAt(file, code, "b.n"); // the `b` usage
        PsiElement[] types = new MqlTypeDeclarationProvider().getSymbolTypeDeclarations(leaf);
        assertNotNull("expected a type declaration for a CBar-typed parameter", types);
        assertEquals(1, types.length);
        assertEquals("CBar", ((MQL4ClassElement) types[0]).getTypeName());
    }

    public void testGotoTypeOnPrimitiveVarIsNull() {
        String code = "void f() { int n; n = 1; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement leaf = leafAt(file, code, "n = 1"); // the `n` usage
        PsiElement[] types = new MqlTypeDeclarationProvider().getSymbolTypeDeclarations(leaf);
        assertTrue("a primitive-typed variable has no project-class type",
                types == null || types.length == 0);
    }
}
