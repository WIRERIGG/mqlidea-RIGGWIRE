/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.ide.structureView.StructureViewBuilder;
import com.intellij.ide.structureView.StructureViewModel;
import com.intellij.ide.structureView.TreeBasedStructureViewBuilder;
import com.intellij.openapi.editor.Editor;
import com.intellij.lang.PsiStructureViewFactory;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4File;

public class MQL4StructureViewBuilderFactory implements PsiStructureViewFactory {
    @Nullable
    @Override
    public StructureViewBuilder getStructureViewBuilder(@NotNull PsiFile psiFile) {
        // The platform's tree builder, not a StructureViewComponent subclass: from CLion 2026.3 that
        // component lives in the separate structure-view plugin, which this plugin cannot see.
        return new TreeBasedStructureViewBuilder() {
            @NotNull
            @Override
            public StructureViewModel createStructureViewModel(@Nullable Editor editor) {
                return new MQL4FileStructureViewModel((MQL4File) psiFile);
            }

            @Override
            public boolean isRootNodeShown() {
                return true; // the old component passed showRootNode = true
            }
        };
    }
}
