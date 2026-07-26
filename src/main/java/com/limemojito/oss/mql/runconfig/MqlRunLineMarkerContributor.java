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
 * which cannot be built standalone). A {@code .mqh} header now carries its own
 * {@link com.limemojito.oss.mql.MqlHeaderFileType} (not {@link MQL4FileType}), so restricting to
 * {@link MQL4FileType}/{@link MQL5FileType} already excludes headers -- no extension special-case needed.
 */
public class MqlRunLineMarkerContributor extends RunLineMarkerContributor {

    private static final Set<String> RUNNABLE_ENTRY_POINTS = Set.of("OnInit", "OnStart");

    @Nullable
    @Override
    public Info getInfo(@NotNull PsiElement element) {
        if (!(element instanceof LeafPsiElement leaf) || leaf.getElementType() != MQL4Elements.IDENTIFIER) {
            return null;
        }
        // Zero-allocation name precheck: only the runnable entry-point identifiers can ever yield a
        // gutter, so bail before touching the parent PSI for every other identifier leaf. Kept in
        // sync with RUNNABLE_ENTRY_POINTS (asserted below via contains()).
        if (!leaf.textMatches("OnInit") && !leaf.textMatches("OnStart")) {
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
        // A .mqh header is MqlHeaderFileType, so it is neither of these -> headers are excluded here.
        FileType fileType = file.getFileType();
        return fileType instanceof MQL4FileType || fileType instanceof MQL5FileType;
    }
}
