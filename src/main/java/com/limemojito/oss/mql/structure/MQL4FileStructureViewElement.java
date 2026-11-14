/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.navigation.ItemPresentation;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import org.apache.commons.lang3.StringUtils;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4File;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.structure.elements.MQL4StructureViewClassElement;
import com.limemojito.oss.mql.structure.elements.MQL4StructureViewEnumElement;
import com.limemojito.oss.mql.structure.elements.MQL4StructureViewFunctionElement;

import javax.swing.Icon;
import java.util.ArrayList;
import java.util.Collection;

/**
 * Root of the Structure view. Builds on {@link MQL4StructureViewElement} rather than the platform's
 * {@code PsiTreeElementBase}: from CLion 2026.3 that class lives in the separate structure-view
 * plugin, which this plugin does not depend on, so using it fails with NoClassDefFoundError.
 */
public class MQL4FileStructureViewElement extends MQL4StructureViewElement<MQL4File> {

    protected MQL4FileStructureViewElement(@NotNull MQL4File file) {
        super(file);
    }

    @NotNull
    @Override
    public StructureViewTreeElement[] getChildren() {
        if (!element.isValid()) {
            return EMPTY_ARRAY;
        }
        return toStructureViewElements(element.getChildren()).toArray(EMPTY_ARRAY);
    }

    public static Collection<StructureViewTreeElement> toStructureViewElements(PsiElement[] elements) {
        Collection<StructureViewTreeElement> res = new ArrayList<>();
        for (PsiElement e : elements) {
            toStructureViewElement(res, e);
        }
        return res;
    }

    public static void toStructureViewElement(Collection<StructureViewTreeElement> res, PsiElement e) {
        IElementType t = e.getNode().getElementType();
        if (t == MQL4Elements.FUNCTION || t == MQL4Elements.FUNCTION_DECLARATION) {
            res.add(new MQL4StructureViewFunctionElement((MQL4FunctionElement) e));
        } else if (t == MQL4Elements.ENUM_STATEMENT) {
            MQL4EnumElement enumElement = (MQL4EnumElement) e;
            if (!StringUtils.isEmpty(enumElement.getTypeName())) {
                res.add(new MQL4StructureViewEnumElement(enumElement));
            }
        } else if (t == MQL4Elements.CLASS) {
            MQL4ClassElement classElement = (MQL4ClassElement) e;
            if (!classElement.isDeclaration()) {
                res.add(new MQL4StructureViewClassElement((MQL4ClassElement) e));
            }
        }
    }

    @NotNull
    public String getPresentableText() {
        return getFileElement().getName();
    }

    @NotNull
    private MQL4File getFileElement() {
        return element;
    }

    @NotNull
    @Override
    public ItemPresentation getPresentation() {
        return new ItemPresentation() {

            public String getPresentableText() {
                return MQL4FileStructureViewElement.this.getPresentableText();
            }

            public String getLocationString() {
                return null;
            }

            public Icon getIcon(boolean open) {
                return getFileElement().getIcon(0);
            }
        };
    }
}
