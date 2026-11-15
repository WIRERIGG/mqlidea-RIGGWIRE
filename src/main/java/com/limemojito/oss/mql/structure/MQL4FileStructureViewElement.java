/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.icons.AllIcons;
import com.intellij.lang.ASTNode;
import com.intellij.psi.util.PsiTreeUtil;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement;
import com.limemojito.oss.mql.psi.impl.MQL4PsiElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.structure.elements.MQL4StructureViewNamedElement;
import java.util.List;

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
        } else if (e instanceof MQL4NamespaceElement namespace) {
            res.add(new MQL4StructureViewNamedElement<>(namespace, namespace.getName(), MQL4Icons.Namespace,
                    toStructureViewElements(namespace.getDeclarations()).toArray(EMPTY_ARRAY)));
        } else if (t == MQL4Elements.INPUT_GROUP && e instanceof MQL4PsiElement group) {
            res.add(new MQL4StructureViewNamedElement<>(group, inputGroupTitle(group), AllIcons.Nodes.Folder,
                    groupInputs(group)));
        }
    }

    /** {@code Risk} for {@code input group "Risk"}. */
    @NotNull
    private static String inputGroupTitle(@NotNull PsiElement group) {
        ASTNode title = group.getNode().findChildByType(MQL4Elements.STRING_LITERAL);
        String text = title == null ? "" : title.getText();
        return text.length() >= 2 && text.startsWith("\"") && text.endsWith("\"") ? text.substring(1, text.length() - 1) : text;
    }

    /** The input variables declared after {@code group}, up to the next group heading. */
    @NotNull
    private static StructureViewTreeElement[] groupInputs(@NotNull PsiElement group) {
        List<StructureViewTreeElement> inputs = new ArrayList<>();
        for (PsiElement next = group.getNextSibling(); next != null; next = next.getNextSibling()) {
            ASTNode node = next.getNode();
            if (node.getElementType() == MQL4Elements.INPUT_GROUP) {
                break;
            }
            if (node.getElementType() != MQL4Elements.VAR_DECLARATION_STATEMENT
                    || (node.findChildByType(MQL4Elements.INPUT_KEYWORD) == null && node.findChildByType(MQL4Elements.SINPUT_KEYWORD) == null)) {
                continue;
            }
            for (MQL4VarDefinitionElement var : PsiTreeUtil.findChildrenOfType(next, MQL4VarDefinitionElement.class)) {
                inputs.add(new MQL4StructureViewNamedElement<>(var, var.getName(), AllIcons.Nodes.Field, EMPTY_ARRAY));
            }
        }
        return inputs.toArray(EMPTY_ARRAY);
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
