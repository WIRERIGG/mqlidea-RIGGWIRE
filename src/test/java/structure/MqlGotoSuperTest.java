/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package structure;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.structure.MqlGotoSuperHandler;

/**
 * Phase 6a: Go to Super. Asserts {@link MqlGotoSuperHandler#findSuperTarget} lands on the base
 * class (caret in a derived class) and on the overridden base method (caret on an override), reusing
 * the Phase-5 CLASS_INHERITANCE_LIST base-class resolution. Uses BasePlatformTestCase for the same
 * reason MqlResolveTest does: the class index needs a real project environment.
 */
public class MqlGotoSuperTest extends BasePlatformTestCase {

    private PsiElement superTargetAt(String code, String marker) {
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        return MqlGotoSuperHandler.findSuperTarget(myFixture.getEditor(), file);
    }

    public void testGotoSuperFromDerivedClassBodyGoesToBaseClass() {
        String code = "class CBase { };\n"
                + "class CDerived : public CBase { int field; };";
        PsiElement target = superTargetAt(code, "field;");
        assertTrue("expected navigation to the base class", target instanceof MQL4ClassElement);
        assertEquals("CBase", ((MQL4ClassElement) target).getTypeName());
    }

    public void testGotoSuperFromOverridingMethodGoesToBaseMethod() {
        String code = "class CBase { public:\n virtual void Run() { } };\n"
                + "class CDerived : public CBase { public:\n virtual void Run() { } };";
        // The second `Run` is the override (lastIndexOf reaches the derived-class method body).
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.lastIndexOf("Run() { }");
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiElement target = MqlGotoSuperHandler.findSuperTarget(myFixture.getEditor(), file);
        assertTrue("expected navigation to the overridden base method", target instanceof MQL4FunctionElement);
        assertEquals("Run", ((MQL4FunctionElement) target).getFunctionName());
        MQL4ClassElement owner = com.intellij.psi.util.PsiTreeUtil.getParentOfType(target, MQL4ClassElement.class);
        assertNotNull(owner);
        assertEquals("the base method must belong to CBase", "CBase", owner.getTypeName());
    }

    public void testNoSuperWhenNoBaseClass() {
        assertNull("a class with no base has no super target",
                superTargetAt("class CStandalone { int f; };", "f;"));
    }
}
