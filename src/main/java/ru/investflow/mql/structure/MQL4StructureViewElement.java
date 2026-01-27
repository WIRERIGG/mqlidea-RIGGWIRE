/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.structure;

import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.pom.Navigatable;
import org.jetbrains.annotations.NotNull;

public abstract class MQL4StructureViewElement<T extends Navigatable> implements StructureViewTreeElement {

    @NotNull
    protected final T element;

    public MQL4StructureViewElement(@NotNull T element) {
        this.element = element;
    }

    public Object getValue() {
        return element;
    }

    public void navigate(boolean requestFocus) {
        element.navigate(requestFocus);
    }

    public boolean canNavigate() {
        return element.canNavigate();
    }

    public boolean canNavigateToSource() {
        return element.canNavigateToSource();
    }

    @NotNull
    public StructureViewTreeElement[] getChildren() {
        return EMPTY_ARRAY;
    }
}
