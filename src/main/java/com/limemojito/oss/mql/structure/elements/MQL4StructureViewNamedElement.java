/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure.elements;

import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.navigation.ItemPresentation;
import com.intellij.navigation.NavigationItem;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.structure.MQL4StructureViewElement;

import javax.swing.Icon;

/** A structure-view node with a fixed label, icon and children (namespaces, input groups, inputs). */
public class MQL4StructureViewNamedElement<T extends NavigationItem> extends MQL4StructureViewElement<T> {

    @Nullable
    private final String text;
    @Nullable
    private final Icon icon;
    @NotNull
    private final StructureViewTreeElement[] children;

    public MQL4StructureViewNamedElement(@NotNull T element, @Nullable String text, @Nullable Icon icon,
                                         @NotNull StructureViewTreeElement[] children) {
        super(element);
        this.text = text;
        this.icon = icon;
        this.children = children;
    }

    @NotNull
    @Override
    public StructureViewTreeElement[] getChildren() {
        return children;
    }

    @NotNull
    @Override
    public ItemPresentation getPresentation() {
        return new ItemPresentation() {
            @Override
            public String getPresentableText() {
                return text;
            }

            @Override
            public Icon getIcon(boolean unused) {
                return icon;
            }
        };
    }
}
