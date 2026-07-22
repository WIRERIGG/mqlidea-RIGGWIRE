/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.actions;

import com.intellij.openapi.command.WriteCommandAction;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.VirtualFileManager;
import com.limemojito.oss.mql.healing.ai.DiffParser;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

public final class DiffApplier {

    private static final Logger LOG = Logger.getInstance(DiffApplier.class);

    private DiffApplier() {
    }

    /**
     * Applies the patch to the document. Hunk headers from the AI are treated as a starting
     * hint only: each hunk is located by matching its context/removed lines against the
     * document (trimmed comparison), searching outward from the claimed position.
     *
     * @return {@code true} only if every hunk was located and applied (and at least one was).
     */
    public static boolean apply(@NotNull Project project, @NotNull DiffParser.DiffPatch patch) {
        VirtualFile vf = findFile(project, patch.filePath());
        if (vf == null) {
            LOG.warn("Cannot find file for diff: " + patch.filePath());
            return false;
        }

        Document doc = FileDocumentManager.getInstance().getDocument(vf);
        if (doc == null) {
            LOG.warn("Cannot get document for: " + patch.filePath());
            return false;
        }

        // Apply hunks bottom-up to avoid offset shifts
        List<DiffParser.Hunk> hunks = patch.hunks().stream()
                .sorted((a, b) -> Integer.compare(b.oldStart(), a.oldStart()))
                .toList();

        boolean[] anyApplied = {false};
        boolean[] anyFailed = {false};
        WriteCommandAction.runWriteCommandAction(project, "Apply AI Fix", "MQL Healing", () -> {
            for (DiffParser.Hunk hunk : hunks) {
                if (applyHunk(doc, hunk)) {
                    anyApplied[0] = true;
                } else {
                    anyFailed[0] = true;
                }
            }
        });

        return anyApplied[0] && !anyFailed[0];
    }

    private static boolean applyHunk(@NotNull Document doc, @NotNull DiffParser.Hunk hunk) {
        // The "old block" is the context (' ') and removed ('-') lines in hunk order.
        List<String> oldTrimmed = new ArrayList<>();
        for (String line : hunk.lines()) {
            if (line.startsWith("+") || line.startsWith("\\")) continue;
            oldTrimmed.add(content(line).trim());
        }

        if (oldTrimmed.isEmpty()) {
            return applyPureInsertion(doc, hunk);
        }

        int docStart = locateOldBlock(doc, oldTrimmed, hunk.oldStart() - 1);
        if (docStart < 0) {
            LOG.warn("Cannot locate hunk context near line " + hunk.oldStart() + " — skipping hunk");
            return false;
        }

        // Rebuild the located block: context lines keep the ORIGINAL document text verbatim,
        // '-' lines are dropped, '+' lines take the AI's text.
        StringBuilder replacement = new StringBuilder();
        int docLine = docStart;
        boolean first = true;
        for (String line : hunk.lines()) {
            if (line.startsWith("\\")) continue; // "\ No newline at end of file"
            String text;
            if (line.startsWith("+")) {
                text = content(line);
            } else if (line.startsWith("-")) {
                docLine++;
                continue;
            } else {
                text = lineText(doc, docLine);
                docLine++;
            }
            if (!first) replacement.append('\n');
            replacement.append(text);
            first = false;
        }

        int replaceStart = doc.getLineStartOffset(docStart);
        int replaceEnd = doc.getLineEndOffset(docStart + oldTrimmed.size() - 1);
        if (replacement.isEmpty()) {
            // Pure deletion: consume a line separator so no empty line is left behind
            if (replaceEnd < doc.getTextLength()) {
                replaceEnd++;
            } else if (replaceStart > 0) {
                replaceStart--;
            }
        }
        doc.replaceString(replaceStart, replaceEnd, replacement.toString());
        return true;
    }

    /**
     * Handles a hunk with no context or removed lines. Per unified diff convention,
     * {@code @@ -N,0 ... @@} means the added lines are inserted after line N (1-based),
     * i.e. before the 0-based line index N.
     */
    private static boolean applyPureInsertion(@NotNull Document doc, @NotNull DiffParser.Hunk hunk) {
        List<String> added = hunk.getAddedLines();
        if (added.isEmpty()) {
            LOG.warn("Hunk at line " + hunk.oldStart() + " has no content — skipping hunk");
            return false;
        }

        int lineCount = doc.getLineCount();
        int insertLine = Math.max(0, Math.min(hunk.oldStart(), lineCount));
        String text = String.join("\n", added);
        if (insertLine >= lineCount) {
            int offset = doc.getTextLength();
            String prefix = offset > 0 && doc.getCharsSequence().charAt(offset - 1) != '\n' ? "\n" : "";
            doc.insertString(offset, prefix + text);
        } else {
            doc.insertString(doc.getLineStartOffset(insertLine), text + "\n");
        }
        return true;
    }

    /**
     * Finds the 0-based document line where the hunk's old lines actually appear,
     * searching nearest-first around the claimed start and widening to the whole document.
     * Returns -1 if the block cannot be located.
     */
    private static int locateOldBlock(@NotNull Document doc, @NotNull List<String> oldTrimmed,
                                      int claimedStart) {
        int maxStart = doc.getLineCount() - oldTrimmed.size();
        if (maxStart < 0) return -1;

        int base = Math.max(0, Math.min(claimedStart, maxStart));
        int maxDelta = Math.max(base, maxStart - base);
        for (int delta = 0; delta <= maxDelta; delta++) {
            int below = base + delta;
            if (below <= maxStart && matchesAt(doc, oldTrimmed, below)) return below;
            int above = base - delta;
            if (delta > 0 && above >= 0 && matchesAt(doc, oldTrimmed, above)) return above;
        }
        return -1;
    }

    private static boolean matchesAt(@NotNull Document doc, @NotNull List<String> oldTrimmed,
                                     int startLine) {
        for (int i = 0; i < oldTrimmed.size(); i++) {
            if (!lineText(doc, startLine + i).trim().equals(oldTrimmed.get(i))) {
                return false;
            }
        }
        return true;
    }

    @NotNull
    private static String lineText(@NotNull Document doc, int line) {
        return doc.getCharsSequence()
                .subSequence(doc.getLineStartOffset(line), doc.getLineEndOffset(line))
                .toString();
    }

    @NotNull
    private static String content(@NotNull String diffLine) {
        return diffLine.isEmpty() ? "" : diffLine.substring(1);
    }

    @Nullable
    private static VirtualFile findFile(@NotNull Project project, @NotNull String filePath) {
        String basePath = project.getBasePath();
        if (basePath == null) return null;

        // Try as project-relative path
        String fullPath = basePath + "/" + filePath;
        VirtualFile vf = VirtualFileManager.getInstance().findFileByUrl("file://" + fullPath);
        if (vf != null) return vf;

        // Try as absolute path
        return VirtualFileManager.getInstance().findFileByUrl("file://" + filePath);
    }
}
