/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import com.intellij.openapi.fileEditor.FileEditor;
import com.intellij.openapi.fileEditor.OpenFileDescriptor;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.search.FileTypeIndex;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.ui.EditorNotificationPanel;
import com.intellij.ui.EditorNotificationProvider;
import com.limemojito.oss.mql.MQL5FileType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.JComponent;
import java.io.IOException;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

/** A banner on a {@code .set} file naming inputs its EA doesn't declare and values that don't fit their type. */
public class SetFileNotificationProvider implements EditorNotificationProvider {

    @Override
    @Nullable
    public Function<? super FileEditor, ? extends JComponent> collectNotificationData(@NotNull Project project, @NotNull VirtualFile file) {
        if (!"set".equalsIgnoreCase(file.getExtension())) {
            return null;
        }
        Finding finding = find(project, file);
        if (finding == null) {
            return null;
        }
        return editor -> {
            EditorNotificationPanel panel = new EditorNotificationPanel(editor, EditorNotificationPanel.Status.Warning);
            panel.setText(finding.text());
            panel.createActionLabel("Open " + finding.ea().getName(),
                    () -> new OpenFileDescriptor(project, finding.ea()).navigate(true));
            return panel;
        };
    }

    record Finding(@NotNull VirtualFile ea, @NotNull SetFileCheck.Result result) {
        @NotNull
        String text() {
            StringBuilder out = new StringBuilder();
            List<String> unknown = result.unknown();
            if (!unknown.isEmpty()) {
                out.append(unknown.size() == 1 ? "1 input isn't" : unknown.size() + " inputs aren't")
                        .append(" declared by ").append(ea.getName())
                        .append(", so MetaTrader ignores ").append(unknown.size() == 1 ? "it" : "them")
                        .append(" and tests the default: ").append(String.join(", ", unknown)).append(". ");
            }
            if (!result.badValues().isEmpty()) {
                out.append("Values that don't fit: ").append(String.join(", ", result.badValues())).append('.');
            }
            return out.toString().trim();
        }
    }

    /**
     * Which copy of an EA a {@code .set} means when the project holds several (worktrees, backups):
     * one whose whole source folder matches what MetaTrader holds (what it builds), else the only
     * copy the mt5 bridge maps, else the one nearest the {@code .set} by folder; null on a tie.
     */
    @Nullable
    static VirtualFile pick(@NotNull Project project, @NotNull VirtualFile set, @NotNull List<VirtualFile> copies) {
        if (copies.size() == 1) {
            return copies.get(0);
        }
        java.nio.file.Path mql5 = com.limemojito.oss.mql.deploy.Mt5DriftNotificationProvider.mql5Folder(project);
        if (mql5 != null) {
            String home = System.getProperty("user.home");
            List<VirtualFile> deployed = new java.util.ArrayList<>();
            List<VirtualFile> mapped = new java.util.ArrayList<>();
            for (VirtualFile c : copies) {
                if (!c.isInLocalFileSystem()) {
                    continue;
                }
                java.nio.file.Path path = java.nio.file.Path.of(c.getPath());
                com.limemojito.oss.mql.deploy.Mt5Mirror mirror = com.limemojito.oss.mql.deploy.Mt5Mirror.forFile(path, mql5,
                        System.getenv(), home == null ? null : java.nio.file.Path.of(home));
                if (mirror == null) {
                    continue;
                }
                mapped.add(c);
                if (mirror.drifted().isEmpty()) {
                    deployed.add(c);
                }
            }
            if (!deployed.isEmpty()) {
                // identical to what MetaTrader holds; several such copies have the same sources
                deployed.sort(java.util.Comparator.comparing(VirtualFile::getPath));
                return deployed.get(0);
            }
            if (mapped.size() == 1) {
                return mapped.get(0);
            }
        }
        String[] setPath = set.getPath().split("/");
        VirtualFile best = null;
        int bestShared = -1;
        boolean tie = false;
        for (VirtualFile c : copies) {
            String[] path = c.getPath().split("/");
            int shared = 0;
            while (shared < setPath.length - 1 && shared < path.length - 1 && setPath[shared].equals(path[shared])) {
                shared++;
            }
            if (shared > bestShared) {
                best = c;
                bestShared = shared;
                tie = false;
            } else if (shared == bestShared) {
                tie = true;
            }
        }
        return tie ? null : best;
    }

    @Nullable
    static Finding find(@NotNull Project project, @NotNull VirtualFile file) {
        String text;
        try {
            text = TesterInputs.decode(file.contentsToByteArray());
        } catch (IOException e) {
            return null;
        }
        Map<String, List<VirtualFile>> eas = new HashMap<>();
        for (VirtualFile vf : FileTypeIndex.getFiles(MQL5FileType.INSTANCE, GlobalSearchScope.projectScope(project))) {
            if ("mq5".equalsIgnoreCase(vf.getExtension())) {
                eas.computeIfAbsent(vf.getNameWithoutExtension(), k -> new java.util.ArrayList<>()).add(vf);
            }
        }
        String name = SetFileCheck.eaFor(file.getName(), text, eas.keySet());
        VirtualFile ea = name == null ? null : pick(project, file, eas.get(name));
        PsiFile psi = ea == null ? null : PsiManager.getInstance(project).findFile(ea);
        Map<String, String> inputs = psi == null ? null : EaInputs.of(psi);
        if (inputs == null) {
            return null;
        }
        SetFileCheck.Result result = SetFileCheck.check(text, inputs);
        return result.isEmpty() ? null : new Finding(ea, result);
    }
}
