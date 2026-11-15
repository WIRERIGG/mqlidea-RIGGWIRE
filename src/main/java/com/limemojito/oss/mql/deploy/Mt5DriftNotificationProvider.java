/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.deploy;

import com.intellij.diff.DiffContentFactory;
import com.intellij.diff.DiffManager;
import com.intellij.diff.requests.SimpleDiffRequest;
import com.intellij.openapi.fileEditor.FileEditor;
import com.intellij.openapi.ide.CopyPasteManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.ui.EditorNotificationPanel;
import com.intellij.ui.EditorNotificationProvider;
import com.limemojito.oss.mql.reference.MqlIncludeRoots;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.JComponent;
import java.awt.datatransfer.StringSelection;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.function.Function;

/**
 * A banner on an MQL source whose MetaTrader copy (what MetaTrader compiles and backtests) differs
 * from it, is missing, or matches while other sources of the same EA differ: a partial deploy
 * makes MetaTrader build a mix of old and new files. It only reads both trees; the banner offers a
 * read-only diff and copies the {@code mt5 sync} command for the user to run.
 */
public class Mt5DriftNotificationProvider implements EditorNotificationProvider {

    @Override
    @Nullable
    public Function<? super FileEditor, ? extends JComponent> collectNotificationData(@NotNull Project project, @NotNull VirtualFile file) {
        if (!file.isInLocalFileSystem() || !Mt5Mirror.isSource(Path.of(file.getName()))) {
            return null;
        }
        Path mql5 = mql5Folder(project);
        if (mql5 == null) {
            return null;
        }
        Path path = Path.of(file.getPath());
        String home = System.getProperty("user.home");
        Mt5Mirror mirror = Mt5Mirror.forFile(path, mql5, System.getenv(), home == null ? null : Path.of(home));
        if (mirror == null) {
            return null;
        }
        Report report = Report.of(mirror, path);
        if (report == null) {
            return null;
        }
        return editor -> panel(editor, project, mirror, path, report);
    }

    /** What the banner says, or null when there is nothing to say. */
    record Report(@NotNull Mt5Mirror.State state, @NotNull List<String> others, @NotNull String copy) {

        @Nullable
        static Report of(@NotNull Mt5Mirror mirror, @NotNull Path file) {
            Mt5Mirror.State state = mirror.state(file);
            String self = mirror.source.relativize(file.normalize()).toString();
            List<String> others = mirror.drifted().stream().filter(p -> !p.equals(self)).toList();
            if (state == Mt5Mirror.State.SAME && others.isEmpty()) {
                return null;
            }
            String copy = mirror.mirror.getParent().getParent().relativize(mirror.copyOf(file)).toString();
            return new Report(state, others, copy);
        }

        @NotNull
        String text() {
            String head = switch (state) {
                case DIFFERENT -> "MetaTrader's copy of this file differs (MQL5/" + copy + ").";
                case MISSING -> "This file isn't in MetaTrader yet (MQL5/" + copy + ").";
                case SAME -> "This file matches MetaTrader's copy,";
            };
            if (others.isEmpty()) {
                return head + " MetaTrader compiles and tests its copy.";
            }
            String count = others.size() == 1 ? "1 other source differs" : others.size() + " other sources differ";
            return head + (state == Mt5Mirror.State.SAME ? " but " : " ") + count
                    + ": a partial deploy builds a mix of old and new files.";
        }
    }

    @NotNull
    private static JComponent panel(@NotNull FileEditor editor, @NotNull Project project, @NotNull Mt5Mirror mirror,
                                    @NotNull Path file, @NotNull Report report) {
        EditorNotificationPanel panel = new EditorNotificationPanel(editor, EditorNotificationPanel.Status.Warning);
        panel.setText(report.text());
        if (report.state() == Mt5Mirror.State.DIFFERENT) {
            panel.createActionLabel("Compare with MetaTrader's copy", () -> showDiff(project, mirror, file));
        }
        if (!report.others().isEmpty()) {
            panel.createActionLabel("Copy list of differing files",
                    () -> CopyPasteManager.getInstance().setContents(new StringSelection(String.join("\n", report.others()))));
        }
        panel.createActionLabel("Copy 'mt5 sync push'",
                () -> CopyPasteManager.getInstance().setContents(new StringSelection("mt5 sync push")));
        return panel;
    }

    private static void showDiff(@NotNull Project project, @NotNull Mt5Mirror mirror, @NotNull Path file) {
        try {
            DiffContentFactory contents = DiffContentFactory.getInstance();
            String theirs = decode(Files.readAllBytes(mirror.copyOf(file)));
            String ours = decode(Files.readAllBytes(file));
            DiffManager.getInstance().showDiff(project, new SimpleDiffRequest(file.getFileName() + ": MetaTrader vs repository",
                    contents.create(project, theirs), contents.create(project, ours), "MetaTrader (read-only)", "Repository (read-only)"));
        } catch (IOException ignored) {
            // the copy vanished since the banner was drawn; the next refresh drops the banner
        }
    }

    /** MetaEditor may save UTF-16 with a byte-order mark; everything else is read as UTF-8. */
    @NotNull
    static String decode(@NotNull byte[] bytes) {
        if (bytes.length >= 2 && (bytes[0] & 0xFF) == 0xFF && (bytes[1] & 0xFF) == 0xFE) {
            return new String(bytes, 2, bytes.length - 2, StandardCharsets.UTF_16LE).replace("\r\n", "\n");
        }
        int skip = bytes.length >= 3 && (bytes[0] & 0xFF) == 0xEF && (bytes[1] & 0xFF) == 0xBB && (bytes[2] & 0xFF) == 0xBF ? 3 : 0;
        return new String(bytes, skip, bytes.length - skip, StandardCharsets.UTF_8).replace("\r\n", "\n");
    }

    /** The MQL5 folder holding the Include folder the plugin indexes, or null. */
    @Nullable
    public static Path mql5Folder(@NotNull Project project) {
        for (VirtualFile root : MqlIncludeRoots.candidateIncludeRoots(project)) {
            VirtualFile parent = root.getParent();
            if (parent != null && "Include".equals(root.getName()) && "MQL5".equals(parent.getName())) {
                return Path.of(parent.getPath());
            }
        }
        return null;
    }
}
