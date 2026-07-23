/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTFactory;
import com.intellij.psi.impl.source.tree.LeafElement;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;

/**
 * Produces {@link MQL4IdentifierLeaf} for IDENTIFIER tokens instead of the platform's default
 * {@code LeafPsiElement}, so identifier leaves can opt into contributor-based references (Phase
 * 4, REVAMP_PLAN.md #3b -- see {@link MQL4IdentifierLeaf} for why this is necessary). Every other
 * token type falls through to the platform default (returning {@code null} here means "use the
 * default").
 */
public class MQL4ASTFactory extends ASTFactory {

    @Nullable
    @Override
    public LeafElement createLeaf(@NotNull IElementType type, @NotNull CharSequence text) {
        if (type == MQL4Elements.IDENTIFIER) {
            return new MQL4IdentifierLeaf(type, text);
        }
        return null;
    }
}
