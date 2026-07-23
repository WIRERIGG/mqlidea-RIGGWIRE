/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiReference;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.reference.MqlIncludeFileReferenceSet;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MQL4PreprocessorIncludeBlock extends MQL4PsiElement {

    // Matches either a quoted path ("X.mqh") or an angle-bracket path (<Trade/Trade.mqh>),
    // whichever the #include line actually used (see PreprocessorIncludeParsing).
    private static final Pattern INCLUDE_PATH = Pattern.compile("\"([^\"\\n]*)\"|<([^>\\n]*)>");

    public MQL4PreprocessorIncludeBlock(@NotNull ASTNode node) {
        super(node);
    }

    /**
     * FileReferenceSet-based reference on the include path (Phase 4, REVAMP_PLAN.md #3b): makes
     * both {@code #include "Relative.mqh"} and {@code #include <Trade/Trade.mqh>} Ctrl-clickable.
     * The whole block is used as the reference host (rather than a single literal token) because
     * the angle-bracket form isn't lexed as one literal -- it's a raw run of tokens between '&lt;'
     * and '&gt;' (see {@code PreprocessorIncludeParsing.parseIncludeStringLiteral}) -- so the path
     * is instead located by regex over this element's own text.
     */
    @Override
    public PsiReference @NotNull [] getReferences() {
        String text = getText();
        Matcher m = INCLUDE_PATH.matcher(text);
        if (!m.find()) {
            return PsiReference.EMPTY_ARRAY;
        }
        boolean quoted = m.group(1) != null;
        String path = quoted ? m.group(1) : m.group(2);
        int group = quoted ? 1 : 2;
        int start = m.start(group);
        return new MqlIncludeFileReferenceSet(path, this, start, !quoted).getAllReferences();
    }

    /**
     * The file this #include resolves to, or {@code null} if it doesn't resolve (unconfigured
     * SDK, missing file, etc.) -- used by the include-closure walk in
     * {@code com.limemojito.oss.mql.reference.MqlResolveUtil}.
     */
    @Nullable
    public PsiFile resolveIncludedFile() {
        PsiReference[] refs = getReferences();
        if (refs.length == 0) {
            return null;
        }
        PsiElement resolved = refs[refs.length - 1].resolve();
        return resolved instanceof PsiFile ? (PsiFile) resolved : null;
    }

    @Override
    public String toString() {
        return "#include";
    }
}
