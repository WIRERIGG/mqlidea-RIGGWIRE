/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.daemon.LineMarkerInfo;
import com.intellij.codeInsight.daemon.LineMarkerProvider;
import com.intellij.icons.AllIcons;
import com.intellij.psi.PsiElement;
import com.intellij.openapi.editor.markup.GutterIconRenderer;
import com.intellij.psi.impl.source.tree.LeafPsiElement;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MqlEventHandlers;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Gutter icon on the name of a defined (non-declaration) MQL5 event handler ({@code OnTick},
 * {@code OnInit}, ...), marking it as an entry point MetaTrader itself calls. Only ever anchors
 * the leaf identifier -- the platform throws if a {@code LineMarkerInfo} is anchored on a
 * composite element (the whole function), so {@link #getLineMarkerInfo(PsiElement)} bails out for
 * anything that isn't the specific name leaf.
 */
public class MqlEventHandlerLineMarkerProvider implements LineMarkerProvider {

    private static final String TOOLTIP = "MT5 entry point";

    @Nullable
    @Override
    public LineMarkerInfo<?> getLineMarkerInfo(@NotNull PsiElement element) {
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
        if (!MqlEventHandlers.NAMES.contains(function.getFunctionName())) {
            return null;
        }
        return new LineMarkerInfo<>(
                element,
                element.getTextRange(),
                AllIcons.Nodes.Function,
                psiElement -> TOOLTIP,
                null,
                GutterIconRenderer.Alignment.LEFT,
                () -> TOOLTIP);
    }
}
