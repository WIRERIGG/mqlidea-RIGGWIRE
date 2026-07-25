/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.psi.PsiFile;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.global.UnusedGlobalFunctionInspection;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

/**
 * Phase 4a: the cross-file "unused global function" inspection. Rather than driving the whole
 * {@link com.intellij.codeInspection.GlobalInspectionTool} pipeline (a project-wide analysis run),
 * these tests exercise the inspection's extracted, pure decision core
 * ({@link UnusedGlobalFunctionInspection#isUnusedGlobalFunction}) directly against a multi-file
 * {@code myFixture} project — the same project/index/VFS environment the inspection itself runs in,
 * so the project-wide {@link com.intellij.psi.search.searches.ReferencesSearch} usage search and the
 * {@code #include}-closure reachability it depends on are real.
 */
public class UnusedGlobalFunctionInspectionTest extends BasePlatformTestCase {

    /** The (first) top-level function definition named {@code name} in {@code file}, or null. */
    private static MQL4FunctionElement functionNamed(PsiFile file, String name) {
        for (MQL4FunctionElement fn : PsiTreeUtil.findChildrenOfType(file, MQL4FunctionElement.class)) {
            if (name.equals(fn.getFunctionName())) {
                return fn;
            }
        }
        return null;
    }

    public void testUnreferencedHelperIsFlagged() {
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "int OnInit() { return 0; }\nvoid Helper() { }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement helper = functionNamed(main, "Helper");
        assertNotNull(helper);
        assertTrue("an unreferenced top-level helper is dead code",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(helper));
    }

    public void testReferencedHelperIsNotFlagged() {
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "int OnInit() { Helper(); return 0; }\nvoid Helper() { }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement helper = functionNamed(main, "Helper");
        assertNotNull(helper);
        assertFalse("Helper() is called from OnInit()",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(helper));
    }

    public void testCrossFileReferenceViaIncludeIsNotFlagged() {
        PsiFile lib = myFixture.addFileToProject("Lib.mqh", "void Shared() { }");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nint OnInit() { Shared(); return 0; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement shared = functionNamed(lib, "Shared");
        assertNotNull(shared);
        assertFalse("Shared() is called across the #include closure",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(shared));
    }

    public void testUnreferencedFunctionInIncludedHeaderIsFlagged() {
        PsiFile lib = myFixture.addFileToProject("Lib.mqh", "void NeverCalled() { }");
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#include \"Lib.mqh\"\nint OnInit() { return 0; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement dead = functionNamed(lib, "NeverCalled");
        assertNotNull(dead);
        assertTrue("NeverCalled() is nowhere referenced across the project",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(dead));
    }

    public void testEventHandlerIsWhitelisted() {
        PsiFile main = myFixture.addFileToProject("Main.mq4", "void OnTick() { }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement onTick = functionNamed(main, "OnTick");
        assertNotNull(onTick);
        assertTrue("OnTick is a terminal-invoked entry point",
                UnusedGlobalFunctionInspection.isWhitelisted(onTick));
        assertFalse("a whitelisted event handler is never flagged even when uncalled",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(onTick));
    }

    public void testImportedBoundaryFunctionIsWhitelisted() {
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "#import \"lib.ex5\"\n   int Exported();\n#import\n"
                        + "int Exported() { return 0; }\nint OnInit() { return 0; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement exported = functionNamed(main, "Exported");
        assertNotNull(exported);
        assertTrue("a function named in an #import block is a library boundary symbol",
                UnusedGlobalFunctionInspection.isWhitelisted(exported));
        assertFalse("an #import-boundary function is never flagged",
                UnusedGlobalFunctionInspection.isUnusedGlobalFunction(exported));
    }

    public void testClassMethodIsNotACandidate() {
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "class CFoo { void Bar() { } };\nint OnInit() { return 0; }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        MQL4FunctionElement bar = functionNamed(main, "Bar");
        assertNotNull(bar);
        assertFalse("a class method is not a top-level global function",
                UnusedGlobalFunctionInspection.isCandidate(bar));
    }

    public void testForwardDeclarationIsNotACandidate() {
        // The forward declaration `void Impl();` must not itself be treated as the flaggable unit —
        // only the definition can be. Here the definition IS referenced, so nothing is dead.
        PsiFile main = myFixture.addFileToProject("Main.mq4",
                "void Impl();\nint OnInit() { Impl(); return 0; }\nvoid Impl() { }");
        myFixture.configureFromExistingVirtualFile(main.getVirtualFile());
        for (MQL4FunctionElement fn : PsiTreeUtil.findChildrenOfType(main, MQL4FunctionElement.class)) {
            if ("Impl".equals(fn.getFunctionName()) && fn.isDeclaration()) {
                assertFalse("a forward declaration is never a candidate",
                        UnusedGlobalFunctionInspection.isCandidate(fn));
            }
        }
    }
}
