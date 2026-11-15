/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.lang.annotation.AnnotationHolder;
import com.intellij.lang.annotation.ExternalAnnotator;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.TextRange;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.wm.StatusBar;
import com.intellij.openapi.wm.WindowManager;
import com.intellij.psi.PsiFile;
import com.limemojito.oss.mql.reference.MqlVisibleNames;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * Surfaces the real MetaEditor compiler's errors and warnings as inline editor annotations. This is the
 * flagship "detect syntactic/semantic errors early" capability (docs/REVAMP_PLAN.md, Phase 1).
 *
 * <p>Layering rules (plan §3a) to avoid duplicate/wasteful work:</p>
 * <ul>
 *   <li>Skip when the file already has parse errors — the live parser owns those squiggles; there is no
 *       point spawning the compiler on code that doesn't lex/parse.</li>
 *   <li>Only compile saved files — the compiler reads disk, so unsaved edits would produce stale
 *       diagnostics; the annotator re-runs after save (and {@link MqlCompilerService} memoises by stamp,
 *       so unchanged content never re-compiles).</li>
 *   <li>A {@code .mqh} header can't compile alone: compile the program that includes it (the one
 *       nearest it by folder, then by path) and keep the diagnostics MetaEditor attributes to the
 *       header. A header no program includes isn't compiled.</li>
 *   <li>Results are memoised by a stamp over the whole include closure, so saving a header
 *       recompiles the programs that include it.</li>
 *   <li>Skip while MetaTrader's Strategy Tester runs: a compile beside a running backtest competes
 *       for the same terminal folder. The next pass after it finishes compiles.</li>
 * </ul>
 */
public class MqlCompilerExternalAnnotator
        extends ExternalAnnotator<MqlCompilerExternalAnnotator.Request, MqlCompilerService.CompileResult> {

    /** {@code program} is what gets compiled: the file itself, or for a header the program including it. */
    public record Request(@NotNull Project project, @NotNull VirtualFile program, long stamp) {
    }

    @Override
    @Nullable
    public Request collectInformation(@NotNull PsiFile file, @NotNull Editor editor, boolean hasErrors) {
        if (hasErrors) {
            return null; // parser already flags these; don't compile un-parseable code
        }
        VirtualFile vFile = file.getVirtualFile();
        if (vFile == null || !vFile.isInLocalFileSystem()) {
            return null; // MetaEditor compiles files on disk only (not light-test or remote files)
        }
        PsiFile program = isCompilableProgram(vFile.getName()) ? file
                : isHeader(vFile.getName()) ? programFor(file) : null;
        if (isHeader(vFile.getName())) {
            file.getProject().getService(MqlCompilerService.class)
                    .rememberHeaderProgram(vFile, program == null ? null : program.getVirtualFile());
        }
        if (program == null || program.getVirtualFile() == null || !program.getVirtualFile().isInLocalFileSystem()) {
            return null;
        }
        List<VirtualFile> closure = new ArrayList<>();
        FileDocumentManager documents = FileDocumentManager.getInstance();
        for (PsiFile f : MqlVisibleNames.includeClosure(program)) {
            VirtualFile vf = f.getVirtualFile();
            if (vf == null) {
                continue;
            }
            if (documents.isFileModified(vf)) {
                return null; // compile only what's on disk; re-runs after save
            }
            closure.add(vf);
        }
        return new Request(file.getProject(), program.getVirtualFile(), MqlCompilerService.closureStamp(closure));
    }

    static boolean isHeader(@NotNull String name) {
        return name.toLowerCase().endsWith(".mqh");
    }

    /** The program to compile for {@code header}: the includer sharing the longest folder path, ties broken by path. */
    @Nullable
    public static PsiFile programFor(@NotNull PsiFile header) {
        VirtualFile vf = header.getVirtualFile();
        if (vf == null) {
            return null;
        }
        String[] headerPath = vf.getPath().split("/");
        PsiFile best = null;
        int bestShared = -1;
        String bestPath = null;
        for (PsiFile program : MqlVisibleNames.programsIncluding(header)) {
            VirtualFile p = program.getVirtualFile();
            if (p == null) {
                continue;
            }
            String[] path = p.getPath().split("/");
            int shared = 0;
            while (shared < headerPath.length - 1 && shared < path.length - 1 && headerPath[shared].equals(path[shared])) {
                shared++;
            }
            if (shared > bestShared || shared == bestShared && p.getPath().compareTo(bestPath) < 0) {
                best = program;
                bestShared = shared;
                bestPath = p.getPath();
            }
        }
        return best;
    }

    @Override
    @Nullable
    public MqlCompilerService.CompileResult doAnnotate(@Nullable Request request) {
        if (request == null || StrategyTester.isRunning()) {
            return null;
        }
        return request.project().getService(MqlCompilerService.class).compile(request.program(), request.stamp());
    }

    @Override
    public void apply(@NotNull PsiFile file,
                      @Nullable MqlCompilerService.CompileResult result,
                      @NotNull AnnotationHolder holder) {
        if (result == null) {
            return; // no compile attempt happened this pass (see collectInformation's skip rules)
        }
        refreshStatusBarWidget(file.getProject());
        if (!result.compilerAvailable()) {
            return;
        }
        Document doc = file.getViewProvider().getDocument();
        if (doc == null) {
            return;
        }
        VirtualFile vFile = file.getVirtualFile();
        if (vFile == null) {
            return;
        }
        boolean program = isCompilableProgram(vFile.getName());
        List<CompilerDiagnostic> own = diagnosticsFor(result, vFile, program);
        for (CompilerDiagnostic d : own) {
            if (d.severity() == CompilerDiagnostic.Severity.INFORMATION || !d.hasLocation()) {
                continue;
            }
            TextRange range = rangeFor(doc, d.line(), d.column());
            if (range == null) {
                continue;
            }
            HighlightSeverity severity = d.severity() == CompilerDiagnostic.Severity.ERROR
                    ? HighlightSeverity.ERROR : HighlightSeverity.WARNING;
            String tag = d.code() != null ? " [metaeditor " + d.code() + "]" : " [metaeditor]";
            holder.newAnnotation(severity, d.message() + tag).range(range).create();
        }
        if (program) {
            String failed = includedFailures(result, own);
            if (failed != null) {
                holder.newAnnotation(HighlightSeverity.WARNING, "Included files fail to compile: " + failed).fileLevel().create();
            }
        }
    }

    /**
     * The diagnostics MetaEditor attributed to {@code file}, matched by the path it printed
     * ({@link DiagnosticFileMatcher}): two headers with one name in different folders never trade
     * errors. Only the compiled program may fall back to its bare name.
     */
    @NotNull
    static List<CompilerDiagnostic> diagnosticsFor(@NotNull MqlCompilerService.CompileResult result,
                                                   @NotNull VirtualFile file, boolean compiledProgram) {
        List<String> paths = new ArrayList<>();
        paths.add(file.getPath());
        String canonical = file.getCanonicalPath();
        if (canonical != null && !canonical.equals(file.getPath())) {
            paths.add(canonical);
        }
        return DiagnosticFileMatcher.forFile(result.diagnostics(), paths, compiledProgram);
    }

    /** {errors, warnings} MetaEditor reported in {@code header} when it compiled the program including it. */
    @NotNull
    public static int[] headerCounts(@NotNull MqlCompilerService.CompileResult result, @NotNull VirtualFile header) {
        int[] counts = new int[2];
        for (CompilerDiagnostic d : diagnosticsFor(result, header, false)) {
            if (d.severity() == CompilerDiagnostic.Severity.ERROR) {
                counts[0]++;
            } else if (d.severity() == CompilerDiagnostic.Severity.WARNING) {
                counts[1]++;
            }
        }
        return counts;
    }

    /**
     * The included files with errors ({@code "RiskManager.mqh (2), Clock.mqh (1)"}), or null: a
     * program whose own lines are clean still fails to build when a header doesn't compile.
     */
    @Nullable
    static String includedFailures(@NotNull MqlCompilerService.CompileResult result, @NotNull List<CompilerDiagnostic> own) {
        java.util.Map<String, Integer> byFile = new java.util.LinkedHashMap<>();
        for (CompilerDiagnostic d : result.diagnostics()) {
            if (d.severity() == CompilerDiagnostic.Severity.ERROR && !own.contains(d)) {
                byFile.merge(d.fileName(), 1, Integer::sum);
            }
        }
        if (byFile.isEmpty()) {
            return null;
        }
        StringBuilder text = new StringBuilder();
        byFile.forEach((name, n) -> text.append(text.isEmpty() ? "" : ", ").append(name).append(" (").append(n).append(')'));
        return text.toString();
    }

    /** Package-visible so {@link CompileCheckNowAction} shares the same "is this compilable" rule. */
    static boolean isCompilableProgram(@NotNull String name) {
        String n = name.toLowerCase();
        return n.endsWith(".mq5") || n.endsWith(".mq4") || n.endsWith(".mql5") || n.endsWith(".mql4");
    }

    /** Nudges the status-bar widget (if present) to re-read the latest {@link MqlCompilerService} result. */
    private static void refreshStatusBarWidget(@NotNull Project project) {
        StatusBar bar = WindowManager.getInstance().getStatusBar(project);
        if (bar != null) {
            bar.updateWidget(MqlCompileStatusBarWidgetFactory.WIDGET_ID);
        }
    }

    /** Maps a 1-based (line, column) to a highlight range: the token at that column, else the line. */
    @Nullable
    private static TextRange rangeFor(@NotNull Document doc, int line1, int col1) {
        int lineIdx = line1 - 1;
        if (lineIdx < 0 || lineIdx >= doc.getLineCount()) {
            return null;
        }
        int lineStart = doc.getLineStartOffset(lineIdx);
        int lineEnd = doc.getLineEndOffset(lineIdx);
        int start = Math.min(lineStart + Math.max(0, col1 - 1), lineEnd);
        CharSequence text = doc.getCharsSequence();
        int end = start;
        while (end < lineEnd && isWordChar(text.charAt(end))) {
            end++;
        }
        if (end == start) {
            // not on an identifier — highlight the whole line (or a single char at EOL)
            return lineEnd > lineStart ? new TextRange(lineStart, lineEnd)
                    : new TextRange(lineStart, Math.min(lineStart + 1, doc.getTextLength()));
        }
        return new TextRange(start, end);
    }

    private static boolean isWordChar(char c) {
        return Character.isLetterOrDigit(c) || c == '_';
    }
}
