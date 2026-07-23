/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4ElementsFactory;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

/**
 * PSI for one FUNCTION_ARG in a function's FUNCTION_ARGS_LIST (see
 * {@link com.limemojito.oss.mql.parser.parsing.FunctionsParsing#parseFunctionArgs}). Shape is
 * {@code [const] TYPE [&|*] [NAME [ [size] ]] [= default]} where TYPE itself may be a bare
 * IDENTIFIER (a custom/class type). That means a FUNCTION_ARG can contain either one IDENTIFIER
 * (an unnamed parameter using a custom type -- legal in a function *declaration*) or two (custom
 * type + parameter name). We can't always tell which IDENTIFIER is the parameter name without
 * re-running the parser's own lookahead, so we use a conservative heuristic: the last IDENTIFIER
 * child is the parameter name UNLESS it is also the first non-trivial child of this node (i.e.
 * nothing precedes it -- meaning it's a lone type name, not `type name`).
 */
public class MQL4FunctionArgElement extends MQL4PsiElement implements PsiNameIdentifierOwner {

    public MQL4FunctionArgElement(@NotNull ASTNode node) {
        super(node);
    }

    @Nullable
    private ASTNode getNameIdentifierNode() {
        ASTNode last = null;
        ASTNode first = null;
        for (ASTNode child = getNode().getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (MQL4TokenSets.COMMENTS_OR_WS.contains(child.getElementType())) {
                continue;
            }
            if (first == null) {
                first = child;
            }
            if (child.getElementType() == MQL4Elements.IDENTIFIER) {
                last = child;
            }
        }
        if (last == null) {
            return null;
        }
        // Sole IDENTIFIER and it's also the very first meaningful child -> it's the type, not a
        // parameter name (e.g. an unnamed custom-type parameter in a forward declaration).
        return last == first ? null : last;
    }

    @Nullable
    @Override
    public PsiElement getNameIdentifier() {
        ASTNode node = getNameIdentifierNode();
        return node == null ? null : node.getPsi();
    }

    @Override
    public String getName() {
        PsiElement id = getNameIdentifier();
        return id == null ? null : id.getText();
    }

    @Override
    public PsiElement setName(@NotNull String name) throws IncorrectOperationException {
        ASTNode nameNode = getNameIdentifierNode();
        if (nameNode != null) {
            getNode().replaceChild(nameNode, MQL4ElementsFactory.createIdentifierNode(getProject(), name));
        }
        return this;
    }

    @Override
    public String toString() {
        return "FUNCTION_ARG:" + getName();
    }
}
