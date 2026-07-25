/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi;

import com.intellij.extapi.psi.PsiFileBase;
import com.intellij.openapi.fileTypes.FileType;
import com.intellij.psi.FileViewProvider;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;

public class MQL4File extends PsiFileBase {

    public MQL4File(@NotNull FileViewProvider viewProvider) {
        super(viewProvider, MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public FileType getFileType() {
        // Return the real per-extension FileType (MQL4/MQL5/MQL Header) rather than hardcoding
        // MQL4FileType. This makes the platform's DeferredIcon placeholder equal the final icon for
        // mq4/mql4/mq5/mql5/mqh files, so the first painted icon never has to repaint wrong->right.
        return getViewProvider().getFileType();
    }

    @Override
    public String toString() {
        return "MQL4 File";
    }
}
