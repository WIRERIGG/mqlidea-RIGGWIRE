/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package doc;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

/**
 * Phase 6 (REVAMP_PLAN.md #Phase 6) quick-doc v2 tests: {@code generateDoc}/{@code getQuickNavigateInfo}
 * for a user-defined function, including its preceding doc-comment block.
 */
public class MQL4DocumentationProviderTest extends BasePlatformTestCase {

    public void testGenerateDocForUserFunctionIncludesSignatureAndDocComment() {
        String code = "// Computes the sum of two numbers.\n// Returns the total.\nint Add(int a, int b) { return a + b; }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement function = findFunction(file, "Add");
        assertNotNull(function);

        MQL4DocumentationProvider provider = new MQL4DocumentationProvider();
        String doc = provider.generateDoc(function, function);
        assertNotNull("expected generated doc for a user function", doc);
        assertTrue("expected the function name in the doc: " + doc, doc.contains("Add"));
        assertTrue("expected the signature args in the doc: " + doc, doc.contains("int a") && doc.contains("int b"));
        assertTrue("expected the preceding doc comment to be included: " + doc, doc.contains("Computes the sum"));
        assertTrue("expected the containing file name in the doc: " + doc, doc.contains("test.mq4"));
    }

    public void testQuickNavigateInfoForUserFunction() {
        PsiFile file = myFixture.configureByText("test.mq4", "int Add(int a, int b) { return a + b; }");
        PsiElement function = findFunction(file, "Add");
        assertNotNull(function);

        MQL4DocumentationProvider provider = new MQL4DocumentationProvider();
        String info = provider.getQuickNavigateInfo(function, function);
        assertNotNull(info);
        assertTrue(info.contains("Add"));
        assertTrue(info.contains("test.mq4"));
    }

    /** The built-in doc page for the leaf at {@code marker}, as quick doc asks for it. */
    private String builtinDoc(String fileName, String code, String marker) {
        PsiFile file = myFixture.configureByText(fileName, code);
        PsiElement leaf = file.findElementAt(code.indexOf(marker));
        return new MQL4DocumentationProvider().generateDoc(leaf, leaf);
    }

    // D-1: the bundled language reference is MQL4 text, so MQL5 files don't show it

    public void testLanguagePagesShowInMql4Files() {
        String doc = builtinDoc("test.mq4", "class CFoo { };\n", "class");
        assertNotNull(doc);
        assertFalse(doc.isEmpty());
    }

    public void testLanguagePagesAreHiddenInMql5Files() {
        assertNull(builtinDoc("test.mq5", "class CFoo { };\n", "class"));
        assertNull(builtinDoc("test.mq5", "#property strict\n", "#property"));
        assertNull(builtinDoc("test.mq5", "int OnInit() { return INIT_SUCCEEDED; }\n", "INIT_SUCCEEDED"));
    }

    public void testFunctionPagesStillShowInMql5Files() {
        String doc = builtinDoc("test.mq5", "void OnStart() { ArrayResize(a, 3); }\n", "ArrayResize");
        assertNotNull(doc);
        assertTrue(doc, doc.contains("ArrayResize"));
    }

    private PsiElement findFunction(PsiFile file, String name) {
        for (PsiElement child : file.getChildren()) {
            if (child instanceof MQL4FunctionElement f && name.equals(f.getFunctionName())) {
                return f;
            }
        }
        return null;
    }
}
