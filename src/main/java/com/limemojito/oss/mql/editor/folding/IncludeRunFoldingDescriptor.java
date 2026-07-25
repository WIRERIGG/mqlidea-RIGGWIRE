/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.folding;

import com.intellij.lang.ASTNode;
import com.intellij.lang.folding.FoldingDescriptor;
import com.intellij.openapi.util.TextRange;
import org.jetbrains.annotations.NotNull;

/**
 * Collapses a run of {@code >= 2} consecutive {@code #include} directives (e.g. a block of header
 * includes at the top of a file) into a single fold, so a long include list doesn't dominate the
 * top of the editor.
 */
public class IncludeRunFoldingDescriptor extends FoldingDescriptor {
    private final int count;

    public IncludeRunFoldingDescriptor(@NotNull ASTNode node, @NotNull TextRange range, int count) {
        super(node, range);
        this.count = count;
    }

    @NotNull
    @Override
    public String getPlaceholderText() {
        return "#include (" + count + ")";
    }
}
