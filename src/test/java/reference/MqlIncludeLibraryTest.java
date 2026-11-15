/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package reference;

import com.intellij.codeInsight.CodeInsightSettings;
import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.codeInsight.lookup.LookupElement;
import com.intellij.codeInsight.lookup.LookupElementPresentation;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.application.WriteAction;
import com.intellij.openapi.roots.ex.ProjectRootManagerEx;
import com.intellij.openapi.util.EmptyRunnable;
import com.intellij.openapi.util.io.FileUtil;
import com.intellij.openapi.vfs.LocalFileSystem;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.newvfs.impl.VfsRootAccess;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import com.intellij.testFramework.IndexingTestUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.intellij.openapi.project.RootsChangeRescanningInfo;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.inspection.UndefinedFunctionCallInspection;
import com.limemojito.oss.mql.reference.MqlIncludeRoots;

import java.io.File;
import java.nio.file.Files;
import java.util.List;

/**
 * The MetaTrader Include folder as a library, with what a real one holds: headers only reached by
 * {@code #include <...>}, stale copies of the project's own headers, MQL4 compatibility shims named
 * like built-ins, and stray .mq5 files. Hermetic: a temp folder stands in for the install.
 */
public class MqlIncludeLibraryTest extends BasePlatformTestCase {

    @Override
    protected void setUp() throws Exception {
        super.setUp();
        File include = FileUtil.createTempDirectory("mql-include", null);
        Files.writeString(new File(include, "Lib.mqh").toPath(), "class CLibOnly { public: int m_size; };\nenum ELib { LIB_A, LIB_B };\n");
        Files.writeString(new File(include, "Stale.mqh").toPath(), "struct Snapshot { int old_field; };\nbool g_bullish = true;\n");
        Files.writeString(new File(include, "Compat.mqh").toPath(), "double OrderLots() { return 0; }\nbool OrderSend(int x) { return true; }\n");
        Files.writeString(new File(include, "Stray.mq5").toPath(), "void OnStart() { }\n");
        VfsRootAccess.allowRootAccess(getTestRootDisposable(), include.getPath());
        VirtualFile root = LocalFileSystem.getInstance().refreshAndFindFileByIoFile(include);
        assertNotNull(root);
        setRoots(List.of(root));
    }

    @Override
    protected void tearDown() throws Exception {
        try {
            setRoots(null);
        } catch (Throwable t) {
            addSuppressedException(t);
        } finally {
            super.tearDown();
        }
    }

    private void setRoots(List<VirtualFile> roots) {
        MqlIncludeRoots.setTestRoots(roots);
        WriteAction.run(() -> ProjectRootManagerEx.getInstanceEx(getProject())
                .makeRootsChange(EmptyRunnable.getInstance(), RootsChangeRescanningInfo.TOTAL_RESCAN));
        IndexingTestUtil.waitUntilIndexesAreReady(getProject());
    }

    private PsiElement resolveIn(PsiFile f, String text) {
        PsiReference ref = f.findReferenceAt(f.getText().indexOf(text) + 1);
        assertNotNull("no reference at '" + text + "'", ref);
        return ref.resolve();
    }

    public void testAngleIncludeResolvesNamesDeclaredInTheLibrary() {
        PsiFile f = myFixture.configureByText("Main.mq5", """
                #include <Lib.mqh>
                void OnStart() { CLibOnly c; ELib e = LIB_B; Print(c.m_size, e); }
                """);
        for (String use : new String[]{"CLibOnly c", "ELib e", "LIB_B;", "m_size, e"}) {
            PsiElement target = resolveIn(f, use);
            assertNotNull(use + " should resolve", target);
            assertEquals(use, "Lib.mqh", target.getContainingFile().getName());
        }
    }

    public void testProjectDeclarationWinsOverStaleLibraryCopy() {
        myFixture.addFileToProject("Trend.mqh", "struct Snapshot { bool active; };\nbool g_bullish = false;\n");
        myFixture.addFileToProject("Analyzer.mqh", "void Record() { Snapshot s; s.active = g_bullish; }\n");
        myFixture.addFileToProject("EA.mq5", "#include \"Trend.mqh\"\n#include \"Analyzer.mqh\"\n");
        PsiFile analyzer = myFixture.configureFromTempProjectFile("Analyzer.mqh");
        for (String use : new String[]{"Snapshot s", "g_bullish;", "active ="}) {
            PsiElement target = resolveIn(analyzer, use);
            assertNotNull(use + " should resolve", target);
            assertEquals(use, "Trend.mqh", target.getContainingFile().getName());
        }
        // No includer at all: the project-wide fallback still prefers the project's struct.
        PsiFile loose = myFixture.addFileToProject("Loose.mqh", "void F() { Snapshot t; t.active = true; }\n");
        assertEquals("Trend.mqh", resolveIn(loose, "Snapshot t").getContainingFile().getName());
        PsiElement member = resolveIn(loose, "active = true");
        assertNotNull("t.active should resolve through the project's Snapshot", member);
        assertEquals("Trend.mqh", member.getContainingFile().getName());
    }

    public void testLibraryShimNeverStandsInForABuiltin() {
        PsiFile f = myFixture.configureByText("Main.mq5", "void OnStart() { MqlTradeRequest r; MqlTradeResult s; OrderSend(r, s); }\n");
        assertNull("OrderSend is the built-in, not Compat.mqh's shim", resolveIn(f, "OrderSend("));
    }

    public void testMql4OnlyCallIsFlaggedEvenIfTheLibraryDefinesIt() {
        myFixture.configureByText("Main.mq5", "void OnStart() { double l = OrderLots(); }\n");
        myFixture.enableInspections(new UndefinedFunctionCallInspection());
        List<String> errors = myFixture.doHighlighting(HighlightSeverity.ERROR).stream()
                .map(HighlightInfo::getDescription).filter(d -> d != null && d.contains("OrderLots")).toList();
        assertEquals(1, errors.size());
    }

    public void testLibraryMq5FilesDoNotChangeTheProjectDialect() {
        myFixture.addFileToProject("Old.mq4", "void OnStart() { }\n");
        PsiFile header = myFixture.addFileToProject("Shared.mqh", "int x;\n");
        assertEquals(MqlDialect.Kind.MQL4, MqlDialect.kind(header));
    }

    private List<String> completionTypeTexts(String fileName, String code, String lookup) {
        myFixture.configureByText(fileName, code);
        CodeInsightSettings settings = CodeInsightSettings.getInstance();
        boolean auto = settings.AUTOCOMPLETE_ON_CODE_COMPLETION;
        settings.AUTOCOMPLETE_ON_CODE_COMPLETION = false;
        LookupElement[] items;
        try {
            items = myFixture.completeBasic();
        } finally {
            settings.AUTOCOMPLETE_ON_CODE_COMPLETION = auto;
        }
        List<String> out = new java.util.ArrayList<>();
        for (LookupElement item : items == null ? new LookupElement[0] : items) {
            if (item.getLookupString().equals(lookup)) {
                LookupElementPresentation p = new LookupElementPresentation();
                item.renderElement(p);
                out.add(String.valueOf(p.getTypeText()));
            }
        }
        return out;
    }

    public void testCompletionOffersTheProjectStructNotTheStaleCopy() {
        myFixture.addFileToProject("Trend.mqh", "struct Snapshot { bool active; };\n");
        List<String> offered = completionTypeTexts("Main.mq5", "void F() { Snapsh<caret> }", "Snapshot");
        assertEquals(List.of("Trend.mqh"), offered);
    }

    public void testCompletionNeverOffersTheShimForABuiltin() {
        List<String> offered = completionTypeTexts("Main.mq5", "void F() { OrderSe<caret> }", "OrderSend");
        assertFalse("Compat.mqh's OrderSend shim was offered: " + offered, offered.contains("Compat.mqh"));
    }

    public void testCompletionOffersLibraryNamesTheProjectLacks() {
        List<String> offered = completionTypeTexts("Main.mq5", "void F() { CLibOn<caret> }", "CLibOnly");
        assertEquals(List.of("Lib.mqh"), offered);
    }
}
