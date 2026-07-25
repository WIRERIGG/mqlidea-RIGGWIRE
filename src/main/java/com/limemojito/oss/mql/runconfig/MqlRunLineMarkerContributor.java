/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import com.intellij.execution.lineMarker.ExecutorAction;
import com.intellij.execution.lineMarker.RunLineMarkerContributor;
import com.intellij.icons.AllIcons;
import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.fileTypes.FileType;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.impl.source.tree.LeafPsiElement;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL5FileType;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Set;

/**
 * Run-gutter (&#9654;) on {@code OnInit}/{@code OnStart} -- the entry points MetaEditor actually
 * compiles/runs a file from -- in a top-level compilable source file (never a {@code .mqh} header,
 * which cannot be built standalone). {@code MQL4FileType} covers {@code .mqh} too (see its
 * registered extensions in plugin.xml), so the header exclusion has to check the real file
 * extension rather than the file type class.
 */
public class MqlRunLineMarkerContributor extends RunLineMarkerContributor {

    private static final Set<String> RUNNABLE_ENTRY_POINTS = Set.of("OnInit", "OnStart");
    private static final String HEADER_EXTENSION = "mqh";

    @Nullable
    @Override
    public Info getInfo(@NotNull PsiElement element) {
        if (!(element instanceof LeafPsiElement leaf) || leaf.getElementType() != MQL4Elements.IDENTIFIER) {
            return null;
        }
        PsiElement parent = element.getParent();
        if (!(parent instanceof MQL4FunctionElement function) || function.isDeclaration()) {
            return null;
        }
        if (function.getNameIdentifier() != element) {
            return null;
        }
        if (!RUNNABLE_ENTRY_POINTS.contains(function.getFunctionName())) {
            return null;
        }
        if (!isCompilableTopLevelFile(element.getContainingFile())) {
            return null;
        }
        AnAction[] actions = ExecutorAction.getActions(0);
        return new Info(AllIcons.RunConfigurations.TestState.Run, actions, psiElement -> "Run");
    }

    private static boolean isCompilableTopLevelFile(@Nullable PsiFile file) {
        if (file == null) {
            return false;
        }
        VirtualFile vf = file.getVirtualFile();
        if (vf != null && HEADER_EXTENSION.equalsIgnoreCase(vf.getExtension())) {
            return false;
        }
        FileType fileType = file.getFileType();
        return fileType instanceof MQL4FileType || fileType instanceof MQL5FileType;
    }
}
