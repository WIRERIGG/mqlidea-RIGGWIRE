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

import java.util.List;

public final class DiffApplier {

    private static final Logger LOG = Logger.getInstance(DiffApplier.class);

    private DiffApplier() {
    }

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

        WriteCommandAction.runWriteCommandAction(project, "Apply AI Fix", "MQL Healing", () -> {
            for (DiffParser.Hunk hunk : hunks) {
                applyHunk(doc, hunk);
            }
        });

        return true;
    }

    private static void applyHunk(@NotNull Document doc, @NotNull DiffParser.Hunk hunk) {
        int lineCount = doc.getLineCount();
        int startLine = hunk.oldStart() - 1; // Convert 1-based to 0-based

        if (startLine < 0 || startLine >= lineCount) {
            LOG.warn("Hunk start line out of range: " + hunk.oldStart());
            return;
        }

        // Verify context lines match (conflict detection)
        if (!verifyContext(doc, hunk)) {
            LOG.warn("Context mismatch at line " + hunk.oldStart() + " — skipping hunk");
            return;
        }

        // Calculate the range to replace
        int replaceStartOffset = doc.getLineStartOffset(startLine);
        int endLine = Math.min(startLine + hunk.oldCount() - 1, lineCount - 1);
        int replaceEndOffset = doc.getLineEndOffset(endLine);

        // Build the replacement text
        StringBuilder replacement = new StringBuilder();
        boolean first = true;
        for (String line : hunk.lines()) {
            if (line.startsWith("-")) continue; // Skip removed lines from output
            String content = line.length() > 1 ? line.substring(1) : "";
            if (!first) replacement.append("\n");
            replacement.append(content);
            first = false;
        }

        doc.replaceString(replaceStartOffset, replaceEndOffset, replacement.toString());
    }

    private static boolean verifyContext(@NotNull Document doc, @NotNull DiffParser.Hunk hunk) {
        int lineCount = doc.getLineCount();
        int currentDocLine = hunk.oldStart() - 1;

        for (String line : hunk.lines()) {
            if (line.startsWith("+")) continue; // Added lines don't need verification

            if (currentDocLine >= lineCount) return false;

            String expectedContent = line.length() > 1 ? line.substring(1) : "";
            int lineStart = doc.getLineStartOffset(currentDocLine);
            int lineEnd = doc.getLineEndOffset(currentDocLine);
            String actualContent = doc.getText().substring(lineStart, lineEnd);

            if (!actualContent.trim().equals(expectedContent.trim())) {
                return false;
            }
            currentDocLine++;
        }
        return true;
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
