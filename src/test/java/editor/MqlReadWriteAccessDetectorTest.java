/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.highlighting.ReadWriteAccessDetector;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MqlReadWriteAccessDetector;

/**
 * Phase 1 (REVAMP_PLAN.md) test for {@link MqlReadWriteAccessDetector}: assignment LHS and
 * increment/decrement operands are Write, an ordinary usage is Read, and a declaration with an
 * initializer counts as a declaration-write.
 */
public class MqlReadWriteAccessDetectorTest extends BasePlatformTestCase {

    private final ReadWriteAccessDetector detector = new MqlReadWriteAccessDetector();

    private PsiElement elementAt(String code, String marker) {
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        PsiElement element = file.findElementAt(offset);
        assertNotNull("no PSI element at marker offset", element);
        return element;
    }

    public void testWriteAccessOnAssignmentLhs() {
        PsiElement x = elementAt("void f() { int x; x = 1; }", "x = 1");
        assertTrue(detector.isReadWriteAccessible(x));
        assertEquals(ReadWriteAccessDetector.Access.Write, detector.getExpressionAccess(x));
    }

    public void testReadAccessOnUsage() {
        PsiElement x = elementAt("void f() { int x = 1; int y = x; }", "x; }");
        assertTrue(detector.isReadWriteAccessible(x));
        assertEquals(ReadWriteAccessDetector.Access.Read, detector.getExpressionAccess(x));
    }

    public void testDeclarationWithInitializerIsDeclarationWriteAccess() {
        PsiElement x = elementAt("void f() { int x = 1; }", "x = 1");
        assertTrue(detector.isDeclarationWriteAccess(x));
    }

    public void testDeclarationWithoutInitializerIsNotDeclarationWriteAccess() {
        PsiElement x = elementAt("void f() { int x; }", "x; }");
        assertFalse(detector.isDeclarationWriteAccess(x));
    }

    public void testCompoundAssignmentIsWriteAccess() {
        PsiElement x = elementAt("void f() { int x = 1; x += 2; }", "x += 2");
        assertEquals(ReadWriteAccessDetector.Access.Write, detector.getExpressionAccess(x));
    }

    public void testIncrementIsWriteAccess() {
        PsiElement x = elementAt("void f() { int x = 1; x++; }", "x++;");
        assertEquals(ReadWriteAccessDetector.Access.Write, detector.getExpressionAccess(x));
    }
}
