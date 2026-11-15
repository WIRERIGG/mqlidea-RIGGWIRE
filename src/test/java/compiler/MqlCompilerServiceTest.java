/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.intellij.openapi.vfs.LocalFileSystem;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.compiler.MqlCompilerLauncher;
import com.limemojito.oss.mql.compiler.MqlCompilerService;

import java.io.File;
import java.nio.file.Files;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Exercises {@link MqlCompilerService}'s launcher-selection strategy and the cache/recompile path
 * (REVAMP_PLAN.md Phase 1) against fake {@link MqlCompilerLauncher}s, so the tests never depend on
 * a real {@code mt5}/MetaEditor/Wine install being present on the machine running the suite. The
 * one real subprocess spawned is {@code java -version} (always present in a running JVM) &mdash;
 * its output is irrelevant because a compile-log fixture is written next to the source file
 * <em>before</em> the "compile" runs, exactly where {@link MqlCompilerService} looks for it.
 *
 * <p>Uses {@link BasePlatformTestCase} purely to get the platform's {@link LocalFileSystem}
 * bootstrapped; {@link MqlCompilerService} itself needs no {@code Project}.</p>
 */
public class MqlCompilerServiceTest extends BasePlatformTestCase {

    private File sourceFile;
    private File logFile;
    private VirtualFile virtualFile;

    @Override
    protected void setUp() throws Exception {
        super.setUp();
        sourceFile = File.createTempFile("MqlCompilerServiceTest", ".mq5");
        Files.writeString(sourceFile.toPath(), "void OnInit() {}\n");
        String name = sourceFile.getName();
        logFile = new File(sourceFile.getParentFile(), name.substring(0, name.lastIndexOf('.')) + ".log");
        // No pre-planted log fixture: the service now deletes any stale log before running, so the
        // fake compiler (CompileLogWriterMain) writes the log DURING its run, exactly like the real one.
        virtualFile = LocalFileSystem.getInstance().refreshAndFindFileByIoFile(sourceFile);
        assertNotNull("expected a VirtualFile for " + sourceFile, virtualFile);
    }

    @Override
    protected void tearDown() throws Exception {
        try {
            Files.deleteIfExists(sourceFile.toPath());
            Files.deleteIfExists(logFile.toPath());
        } finally {
            super.tearDown();
        }
    }


    public void testUnavailableWhenNoLauncherIsAvailable() {
        MqlCompilerService service = new MqlCompilerService(List.of(unavailable(), unavailable()));

        MqlCompilerService.CompileResult result = service.compile(virtualFile);

        assertFalse(result.compilerAvailable());
        assertTrue(result.diagnostics().isEmpty());
        assertSame(result, service.getLastResult(virtualFile));
    }

    public void testFirstAvailableLauncherWinsAndResultIsMemoised() {
        AtomicInteger skippedCalls = new AtomicInteger();
        AtomicInteger usedCalls = new AtomicInteger();
        MqlCompilerLauncher skipped = counting(skippedCalls, null);
        MqlCompilerLauncher used = counting(usedCalls, logWritingCommand());
        MqlCompilerService service = new MqlCompilerService(List.of(skipped, used));

        MqlCompilerService.CompileResult first = service.compile(virtualFile);
        assertTrue(first.compilerAvailable());
        assertEquals(1, first.errors());
        assertEquals(0, first.warnings());
        assertEquals(1, skippedCalls.get());
        assertEquals(1, usedCalls.get());

        // Unchanged content -> memoised by modification stamp; neither launcher is probed again.
        MqlCompilerService.CompileResult second = service.compile(virtualFile);
        assertSame(first, second);
        assertEquals(1, skippedCalls.get());
        assertEquals(1, usedCalls.get());
    }

    public void testRecompileBypassesTheCache() {
        AtomicInteger calls = new AtomicInteger();
        MqlCompilerLauncher launcher = counting(calls, logWritingCommand());
        MqlCompilerService service = new MqlCompilerService(List.of(launcher));

        service.compile(virtualFile);
        assertEquals(1, calls.get());

        service.compile(virtualFile);
        assertEquals(1, calls.get()); // still memoised, unchanged content

        service.recompile(virtualFile);
        assertEquals(2, calls.get()); // cache explicitly invalidated -> launcher probed again
    }

    /** A program's result is memoised by its closure stamp: a saved header changes it and forces a compile. */
    public void testClosureStampChangeRecompiles() {
        AtomicInteger calls = new AtomicInteger();
        MqlCompilerService service = new MqlCompilerService(List.of(counting(calls, logWritingCommand())));
        service.compile(virtualFile, 1L);
        service.compile(virtualFile, 1L);
        assertEquals(1, calls.get());
        service.compile(virtualFile, 2L);
        assertEquals(2, calls.get());
    }

    public void testClosureStampFollowsEveryFile() throws Exception {
        File header = File.createTempFile("MqlCompilerServiceTest", ".mqh");
        try {
            VirtualFile h = LocalFileSystem.getInstance().refreshAndFindFileByIoFile(header);
            assertNotNull(h);
            long before = MqlCompilerService.closureStamp(List.of(virtualFile, h));
            assertEquals(before, MqlCompilerService.closureStamp(List.of(virtualFile, h)));
            com.intellij.openapi.application.WriteAction.runAndWait(() -> h.setBinaryContent("int x;\n".getBytes()));
            assertFalse(before == MqlCompilerService.closureStamp(List.of(virtualFile, h)));
        } finally {
            Files.deleteIfExists(header.toPath());
        }
    }

    /** A header compiles through the program nearest it; a header nothing includes has none. */
    public void testHeaderCompilesThroughTheNearestIncluder() {
        myFixture.addFileToProject("Experts/EA/Main.mq5", "#include \"Lib/Part.mqh\"\n");
        myFixture.addFileToProject("Experts/Other.mq5", "#include \"EA/Lib/Part.mqh\"\n");
        com.intellij.psi.PsiFile part = myFixture.addFileToProject("Experts/EA/Lib/Part.mqh", "int g_part;\n");
        com.intellij.psi.PsiFile program = com.limemojito.oss.mql.compiler.MqlCompilerExternalAnnotator.programFor(part);
        assertNotNull(program);
        assertEquals("Main.mq5", program.getName());
        com.intellij.psi.PsiFile orphan = myFixture.addFileToProject("Experts/EA/Lib/Orphan.mqh", "int g_orphan;\n");
        assertNull(com.limemojito.oss.mql.compiler.MqlCompilerExternalAnnotator.programFor(orphan));
    }

    public void testGetLastResultIsNullBeforeAnyCompile() {
        MqlCompilerService service = new MqlCompilerService(List.of(unavailable()));

        assertNull(service.getLastResult(virtualFile));
    }

    private static MqlCompilerLauncher unavailable() {
        return counting(new AtomicInteger(), null);
    }

    private static MqlCompilerLauncher counting(AtomicInteger counter, GeneralCommandLine command) {
        return new MqlCompilerLauncher() {
            @Override
            public String name() {
                return "fake";
            }

            @Override
            public GeneralCommandLine commandFor(File source) {
                counter.incrementAndGet();
                return command;
            }
        };
    }

    /**
     * A real subprocess that writes the compile log to {@link #logFile} during its run (via
     * {@link CompileLogWriterMain} on the test classpath), so the service — which deletes any stale
     * log before launching — finds a genuinely fresh log afterwards. Also exercises the LE-no-BOM
     * decode path end-to-end.
     */
    private GeneralCommandLine logWritingCommand() {
        String javaBin = System.getProperty("java.home") + File.separator + "bin" + File.separator + "java";
        String classpath = System.getProperty("java.class.path");
        return new GeneralCommandLine(javaBin, "-cp", classpath,
                CompileLogWriterMain.class.getName(), logFile.getAbsolutePath());
    }
}
