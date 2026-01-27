/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure.elements;

import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.lang.ASTNode;
import com.intellij.navigation.ItemPresentation;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.structure.MQL4StructureViewElement;

import java.util.Collection;

import static com.limemojito.oss.mql.structure.MQL4FileStructureViewElement.toStructureViewElements;


public class MQL4StructureViewClassElement extends MQL4StructureViewElement<MQL4ClassElement> {

    public MQL4StructureViewClassElement(@NotNull MQL4ClassElement element) {
        super(element);
    }

    @NotNull
    public StructureViewTreeElement[] getChildren() {
        ASTNode innerBlockNode = element.getInnerBlockNode();
        if (innerBlockNode == null) {
            return new StructureViewTreeElement[0];
        }
        PsiElement[] children = innerBlockNode.getPsi().getChildren();
        Collection<StructureViewTreeElement> els = toStructureViewElements(children);
        return els.toArray(new StructureViewTreeElement[0]);
    }

    @NotNull
    public ItemPresentation getPresentation() {
        return element.getPresentation();
    }
}
