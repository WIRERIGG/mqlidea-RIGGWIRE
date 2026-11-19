/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiFileSystemItem;
import com.intellij.psi.impl.source.resolve.reference.impl.providers.FileReferenceSet;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.Collection;
import java.util.List;

/**
 * A {@link FileReferenceSet} for {@code #include} targets. Quoted includes ({@code "X.mqh"}) are
 * relative to the including file's directory (the platform's own default context already covers
 * this via {@link #useIncludingFileAsContext()}); angle-bracket includes
 * ({@code <Trade/Trade.mqh>}) are rooted at the MQL4/MQL5 SDK "Include" directories instead, so we
 * add those as extra default contexts when the include used angle brackets.
 */
public class MqlIncludeFileReferenceSet extends FileReferenceSet {

    private final boolean angleBracket;

    public MqlIncludeFileReferenceSet(@NotNull String path, @NotNull PsiElement element, int startInElement, boolean angleBracket) {
        super(path, element, startInElement, null, true);
        this.angleBracket = angleBracket;
    }

    /** MetaEditor takes either slash: {@code #include <Trade\Trade.mqh>} is as common as the {@code /} form. */
    @Override
    protected int findSeparatorOffset(@NotNull CharSequence sequence, int from) {
        for (int i = Math.max(from, 0); i < sequence.length(); i++) {
            char c = sequence.charAt(i);
            if (c == '/' || c == '\\') {
                return i;
            }
        }
        return -1;
    }

    @Override
    protected int findSeparatorLength(@NotNull CharSequence sequence, int atOffset) {
        return 1;
    }

    @Override
    public boolean useIncludingFileAsContext() {
        // Quoted relative includes resolve against the including file's directory; angle-bracket
        // ones are SDK-rooted only (see computeDefaultContexts()).
        return !angleBracket;
    }

    @NotNull
    @Override
    public Collection<PsiFileSystemItem> computeDefaultContexts() {
        PsiFile containingFile = getContainingFile();
        if (!angleBracket) {
            // The platform's default misses the folder when the including file sits directly in an include
            // root (MQL5/Include/Object.mqh -> "StdLibErr.mqh"), so the file's own folder comes first.
            PsiFile original = containingFile == null ? null : containingFile.getOriginalFile();
            com.intellij.psi.PsiDirectory folder = original == null ? null : original.getContainingDirectory();
            if (folder == null) {
                return super.computeDefaultContexts();
            }
            List<PsiFileSystemItem> contexts = new ArrayList<>();
            contexts.add(folder);
            for (PsiFileSystemItem context : super.computeDefaultContexts()) {
                if (!folder.equals(context)) {
                    contexts.add(context);
                }
            }
            return contexts;
        }
        if (containingFile == null) {
            return super.computeDefaultContexts();
        }
        List<PsiFileSystemItem> contexts = new ArrayList<>(
                toFileSystemItems(MqlIncludeRoots.candidateIncludeRoots(containingFile.getProject())));
        if (contexts.isEmpty()) {
            return super.computeDefaultContexts();
        }
        return contexts;
    }
}
