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
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

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
 *   <li>Only compile a program ({@code .mq4}/{@code .mq5}); a bare {@code .mqh} header can't compile alone.</li>
 * </ul>
 */
public class MqlCompilerExternalAnnotator
        extends ExternalAnnotator<MqlCompilerExternalAnnotator.Request, MqlCompilerService.CompileResult> {

    public record Request(@NotNull Project project, @NotNull VirtualFile file) {
    }

    @Override
    @Nullable
    public Request collectInformation(@NotNull PsiFile file, @NotNull Editor editor, boolean hasErrors) {
        if (hasErrors) {
            return null; // parser already flags these; don't compile un-parseable code
        }
        VirtualFile vFile = file.getVirtualFile();
        if (vFile == null || !isCompilableProgram(vFile.getName())) {
            return null;
        }
        if (FileDocumentManager.getInstance().isFileModified(vFile)) {
            return null; // compile only what's on disk; re-runs after save
        }
        return new Request(file.getProject(), vFile);
    }

    @Override
    @Nullable
    public MqlCompilerService.CompileResult doAnnotate(@Nullable Request request) {
        if (request == null) {
            return null;
        }
        return request.project().getService(MqlCompilerService.class).compile(request.file());
    }

    @Override
    public void apply(@NotNull PsiFile file,
                      @Nullable MqlCompilerService.CompileResult result,
                      @NotNull AnnotationHolder holder) {
        if (result == null || !result.compilerAvailable()) {
            return;
        }
        Document doc = file.getViewProvider().getDocument();
        if (doc == null) {
            return;
        }
        String thisFile = file.getName();
        for (CompilerDiagnostic d : result.diagnostics()) {
            if (d.severity() == CompilerDiagnostic.Severity.INFORMATION || !d.hasLocation()) {
                continue;
            }
            // Diagnostics attributed to an #include'd header belong to that file, not this one.
            if (!thisFile.equalsIgnoreCase(d.fileName())) {
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
    }

    private static boolean isCompilableProgram(@NotNull String name) {
        String n = name.toLowerCase();
        return n.endsWith(".mq5") || n.endsWith(".mq4") || n.endsWith(".mql5") || n.endsWith(".mql4");
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
