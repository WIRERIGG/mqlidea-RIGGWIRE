/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionType;
import com.intellij.patterns.PsiElementPattern;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.limemojito.oss.mql.editor.codecompletion.MQL4CompletionContributor.MQL4IdentifiersCompletionProvider;

import static com.limemojito.oss.mql.editor.codecompletion.MQL4CompletionContributor.mql4;


public class CommentsCompletions {
    static final PsiElementPattern.Capture<PsiElement> IN_COMMENT = mql4().inside(PsiComment.class);

    public static PsiElementPattern.Capture<PsiElement> extend(MQL4CompletionContributor contributor, PsiElementPattern.Capture<PsiElement> filter) {
        contributor.extend(CompletionType.BASIC, CommentsCompletions.IN_COMMENT, new MQL4IdentifiersCompletionProvider());
        return filter.andNot(CommentsCompletions.IN_COMMENT);
    }
}
