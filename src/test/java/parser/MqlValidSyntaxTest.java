/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

import java.util.ArrayList;
import java.util.List;

/**
 * Valid MQL5 that used to get a false parse error (which also switches off the compiler annotator
 * for the file). Every snippet compiles in MetaEditor with 0 errors and 0 warnings.
 */
public class MqlValidSyntaxTest extends BasePlatformTestCase {

    private PsiFile parse(String code) {
        PsiFile file = myFixture.configureByText("test.mq5", code);
        PsiErrorElement error = PsiTreeUtil.findChildOfType(file, PsiErrorElement.class);
        assertNull("unexpected parse error: " + (error == null ? "" : error.getErrorDescription()
                + " at '" + error.getParent().getText() + "'"), error);
        List<String> bad = new ArrayList<>();
        PsiTreeUtil.processElements(file, e -> {
            if (e.getNode().getElementType() == MQL4Elements.BAD_CHARACTER) bad.add(e.getText());
            return true;
        });
        assertEquals("bad characters", List.of(), bad);
        return file;
    }

    private static List<String> classNames(PsiFile file) {
        List<String> names = new ArrayList<>();
        for (MQL4ClassElement c : PsiTreeUtil.findChildrenOfType(file, MQL4ClassElement.class)) {
            names.add(c.getName());
        }
        return names;
    }

    private PsiElement resolveAt(String code, String marker) {
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        PsiReference ref = myFixture.getReferenceAtCaretPosition();
        assertNotNull("expected a reference at " + marker, ref);
        return ref.resolve();
    }

    // S-1: pack(n) alignment on class / struct, either side of final, before a base list

    public void testPackSpecifier() {
        PsiFile file = parse("class CP pack(8) { public: int a; double b; };\n"
                + "struct SA { int q; };\n"
                + "struct SB pack(2) : SA { char z; };\n"
                + "struct SN pack(1) { char c; };\n"
                + "class C1 pack(4) final { public: int a; };\n"
                + "class C2 final pack(4) { public: int a; };\n"
                + "void OnStart() { CP p; Print(sizeof(p), sizeof(SN)); }\n");
        assertEquals(List.of("CP", "SA", "SB", "SN", "C1", "C2"), classNames(file));
    }

    public void testPackStaysAnOrdinaryName() {
        // pack is not reserved in MQL5: int pack=1; compiles
        String code = "void OnStart()\n  {\n   int pack=1;\n   Print(pack);\n  }\n";
        parse(code);
        assertNotNull(resolveAt(code, "pack);"));
    }

    // F-2: export on library function definitions and prototypes

    public void testExportedFunctions() {
        String code = "#property library\nint Ex(int v) export;\nint Twice(int v) export\n  {\n   return v*2;\n  }\n"
                + "int Ex(int v) export { return v; }\n";
        PsiFile file = parse(code);
        List<String> functions = new ArrayList<>();
        for (MQL4FunctionElement f : PsiTreeUtil.findChildrenOfType(file, MQL4FunctionElement.class)) {
            functions.add(f.getFunctionName() + (f.isDeclaration() ? ";" : "{}"));
        }
        assertEquals(List.of("Ex;", "Twice{}", "Ex{}"), functions);
        assertNotNull("parameter v resolves inside an exported body", resolveAt(code, "v*2"));
    }

    // P-2: stringize # and token-paste ## in macro bodies

    public void testMacroStringizeAndPaste() {
        parse("#define STR(x)   #x\n#define CAT(a,b) a##b\n"
                + "void OnStart() { Print(STR(hello)); }\n");
    }

    public void testStrayHashOutsideAMacroIsStillAnError() {
        myFixture.configureByText("test.mq5", "void OnStart() { int a = 1 # 2; int b = a ## 3; }\n");
        List<String> errors = new ArrayList<>();
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            errors.add(h.getDescription());
        }
        assertTrue(errors.toString(), errors.contains("'#' is only valid in a #define body"));
        assertTrue(errors.toString(), errors.contains("'##' is only valid in a #define body"));
    }

    public void testUnknownDirectiveIsAnError() {
        // MetaEditor: error 109 "invalid preprocessor command"
        myFixture.configureByText("test.mq5", "#region Helpers\nvoid OnStart() { }\n#endregion\n");
        List<String> errors = new ArrayList<>();
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            errors.add(h.getDescription());
        }
        assertTrue(errors.toString(), errors.contains("Invalid preprocessor command '#region'"));
        assertTrue(errors.toString(), errors.contains("Invalid preprocessor command '#endregion'"));
    }

    public void testMacroOperatorsInsideADefineAreNotErrors() {
        myFixture.configureByText("test.mq5", "#define STR(x)   #x\n#define CAT(a,b) \\\n   a##b\nvoid OnStart() { }\n");
        for (var h : myFixture.doHighlighting(com.intellij.lang.annotation.HighlightSeverity.ERROR)) {
            fail("unexpected error: " + h.getDescription());
        }
    }
}
