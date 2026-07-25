/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import com.intellij.spellchecker.inspections.IdentifierSplitter;
import com.intellij.spellchecker.tokenizer.SpellcheckingStrategy;
import com.intellij.spellchecker.tokenizer.Tokenizer;
import com.intellij.spellchecker.tokenizer.TokenizerBase;
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.jetbrains.annotations.NotNull;

/**
 * Wires MQL4/MQL5 into the platform's spellchecking pass (Phase 2c, REVAMP_PLAN.md): comments and
 * string literals are checked as free text, identifiers are split on case/underscore boundaries
 * (so {@code myFastMa} is checked as "my", "Fast", "Ma", not as one nonsense word), and everything
 * else (keywords, numbers, operators, punctuation) is skipped outright.
 */
public class MqlSpellcheckingStrategy extends SpellcheckingStrategy {

    private final Tokenizer<PsiElement> identifierTokenizer = TokenizerBase.create(IdentifierSplitter.getInstance());

    @NotNull
    @Override
    public Tokenizer getTokenizer(PsiElement element) {
        if (element instanceof PsiComment) {
            return TEXT_TOKENIZER;
        }
        ASTNode node = element.getNode();
        IElementType type = node == null ? null : node.getElementType();
        if (type == MQL4Elements.STRING_LITERAL) {
            return TEXT_TOKENIZER;
        }
        if (type == MQL4Elements.IDENTIFIER) {
            return identifierTokenizer;
        }
        return EMPTY_TOKENIZER;
    }
}
