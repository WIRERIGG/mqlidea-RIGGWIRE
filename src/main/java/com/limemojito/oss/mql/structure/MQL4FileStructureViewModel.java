/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.ide.structureView.TextEditorBasedStructureViewModel;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4File;

public class MQL4FileStructureViewModel extends TextEditorBasedStructureViewModel {
    private final MQL4File file;

    public MQL4FileStructureViewModel(final MQL4File file) {
        super(file);
        this.file = file;
    }

    @NotNull
    public StructureViewTreeElement getRoot() {
        return new MQL4FileStructureViewElement(file);
    }
}
