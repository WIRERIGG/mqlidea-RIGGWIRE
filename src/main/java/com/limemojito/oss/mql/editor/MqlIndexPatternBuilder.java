/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.lexer.Lexer;
import com.intellij.openapi.fileTypes.FileType;
import com.intellij.psi.PsiFile;
import com.intellij.psi.impl.search.IndexPatternBuilder;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL5FileType;
import com.limemojito.oss.mql.parser.MQL4ParserDefinition;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Feeds MQL4/MQL5 comments into the platform's native TODO index (Phase 2d, REVAMP_PLAN.md), so
 * {@code // TODO: ...} / {@code // FIXME: ...} markers show up in the built-in TODO tool window
 * and gutter icons without needing the (now default-off) {@link
 * com.limemojito.oss.mql.inspection.TodoFixmeInspection} enabled -- that inspection's class stays
 * around as an opt-in duplicate for users who prefer inline warnings over the tool window.
 */
public class MqlIndexPatternBuilder implements IndexPatternBuilder {

    @Nullable
    @Override
    public Lexer getIndexingLexer(@NotNull PsiFile file) {
        FileType type = file.getFileType();
        if (!(type instanceof MQL4FileType) && !(type instanceof MQL5FileType)) {
            return null;
        }
        return new MQL4ParserDefinition().createLexer(file.getProject());
    }

    @NotNull
    @Override
    public TokenSet getCommentTokenSet(@NotNull PsiFile file) {
        return MQL4TokenSets.COMMENTS;
    }

    @Override
    public int getCommentStartDelta(IElementType tokenType) {
        return 0;
    }

    @Override
    public int getCommentEndDelta(IElementType tokenType) {
        return 0;
    }
}
