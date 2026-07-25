/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.folding;

import com.intellij.lang.ASTNode;
import com.intellij.lang.folding.FoldingDescriptor;
import com.intellij.openapi.util.TextRange;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Folds a {@code #region NAME ... #endregion} block (a MetaEditor folding convention). MQL's
 * lexer has no dedicated tokens for {@code #region}/{@code #endregion} -- unlike the real
 * preprocessor keywords ({@code #include}, {@code #property}, ...) they fall through to a
 * {@code BAD_CHARACTER('#')} leaf immediately followed by an {@code IDENTIFIER} leaf ({@code
 * "region"}/{@code "endregion"}). The pair is matched at the folding-builder level from those raw
 * leaves -- see {@link com.limemojito.oss.mql.editor.MQL4FoldingBuilder}.
 */
public class RegionFoldingDescriptor extends FoldingDescriptor {
    private final String name;

    public RegionFoldingDescriptor(@NotNull ASTNode node, @NotNull TextRange range, @Nullable String name) {
        super(node, range);
        this.name = name;
    }

    @NotNull
    @Override
    public String getPlaceholderText() {
        return name == null || name.isBlank() ? "region" : name;
    }
}
