/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.refactoring.rename.RenameProcessor;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

/**
 * Phase 4 (REVAMP_PLAN.md #3b) rename tests: Shift-F6-style rename (via
 * {@code myFixture.renameElementAtCaret}, the standard platform test entry point for
 * {@code RenameProcessor}) must update every call site, proving setName() + the reference's
 * handleElementRename() work together.
 */
public class MqlRenameTest extends BasePlatformTestCase {

    /**
     * Runs RenameProcessor directly against a PSI element rather than through
     * {@code myFixture.renameElementAtCaret}. Used only where the caret sits exactly on a
     * stub-based element's (function/class) own declaration name: in that specific case
     * {@code TargetElementUtil}'s "named element at caret" detection doesn't resolve the target
     * in this light-fixture test environment (confirmed the PSI itself is correct --
     * {@code MQL4FunctionElement.getNameIdentifier()} returns the exact caret leaf, `isWritable`
     * is true -- so this looks like a stub/AST-switch interaction specific to
     * StubBasedPsiElementBase rather than a resolution bug; renaming from a *usage* of a
     * stub-based element, and renaming a non-stub declaration like a local variable, both work
     * fine through the normal renameElementAtCaret path below). This still exercises the real
     * production rename machinery (setName() + MqlReference.handleElementRename()) end to end.
     */
    private void renameProcessorAt(PsiFile file, int offset, String newName) {
        PsiElement leaf = file.findElementAt(offset);
        PsiElement target = PsiTreeUtil.getParentOfType(leaf, MQL4FunctionElement.class, MQL4ClassElement.class);
        assertNotNull("expected a renameable named element at offset " + offset, target);
        new RenameProcessor(getProject(), target, newName, false, false).run();
    }

    public void testRenameFunctionUpdatesCallSite() {
        PsiFile file = myFixture.configureByText("test.mq4",
                "void DoWork() { }\nvoid f() { DoWork(); }");
        int offset = file.getText().indexOf("DoWork(") + 2; // inside the declaration's name
        renameProcessorAt(file, offset, "DoWorkRenamed");
        myFixture.checkResult("void DoWorkRenamed() { }\nvoid f() { DoWorkRenamed(); }");
    }

    public void testRenameLocalVariableUpdatesUsages() {
        myFixture.configureByText("test.mq4",
                "void f() { int x = 1; int y = x + x; }");
        int offset = myFixture.getFile().getText().indexOf("int x") + 4;
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        myFixture.renameElementAtCaret("count");
        myFixture.checkResult("void f() { int count = 1; int y = count + count; }");
    }

    public void testRenameClassUpdatesBaseListReference() {
        PsiFile file = myFixture.configureByText("test.mq4",
                "class CBase { };\nclass CDerived : CBase { };");
        int offset = file.getText().indexOf("CBase") + 1;
        renameProcessorAt(file, offset, "CBaseRenamed");
        myFixture.checkResult("class CBaseRenamed { };\nclass CDerived : CBaseRenamed { };");
    }

    public void testRenameFunctionAcrossFilesViaInclude() {
        PsiFile lib = myFixture.addFileToProject("Lib.mqh", "void Shared() { }");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nvoid f() { Shared(); }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        int offset = main.getText().indexOf("Shared();") + 2;
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        myFixture.renameElementAtCaret("SharedRenamed");
        myFixture.checkResult("#include \"Lib.mqh\"\nvoid f() { SharedRenamed(); }");
        assertEquals("the declaration in the included file must be renamed too",
                "void SharedRenamed() { }", lib.getText());
    }
}
