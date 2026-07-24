/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiFileFactory;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorPropertyBlock;
import com.limemojito.oss.mql.psi.impl.MQL4PsiElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

public class MQL4ElementsFactory implements MQL4Elements {

    /**
     * Dispatches an AST node to its PSI wrapper by element TYPE. Previously this used a
     * {@code Map<ASTNode, ...>} cache keyed by the node instance — but the mapping depends only
     * on {@code getElementType()}, so keying by the node retained every ASTNode (and thus whole
     * PSI trees) for the application's lifetime. A direct type switch is allocation-free and
     * leak-free.
     */
    public static PsiElement createElement(@NotNull ASTNode node) {
        IElementType type = node.getElementType();
        if (type == PREPROCESSOR_PROPERTY_BLOCK) {
            return new MQL4PreprocessorPropertyBlock(node);
        }
        if (type == PREPROCESSOR_INCLUDE_BLOCK) {
            return new MQL4PreprocessorIncludeBlock(node);
        }
        if (type == FUNCTION_DECLARATION || type == FUNCTION) {
            return new MQL4FunctionElement(node);
        }
        if (type == ENUM_STATEMENT) {
            return new MQL4EnumElement(node);
        }
        if (type == ENUM_FIELD) {
            return new MQL4EnumFieldElement(node);
        }
        if (type == MQL4Elements.CLASS) {
            return new MQL4ClassElement(node);
        }
        if (type == VAR_DEFINITION) {
            return new MQL4VarDefinitionElement(node);
        }
        if (type == FUNCTION_ARG) {
            return new MQL4FunctionArgElement(node);
        }
        return new MQL4PsiElement(node);
    }

    /**
     * Builds a standalone IDENTIFIER leaf AST node with the given text, for use by
     * {@code setName()} implementations across the named PSI classes (Phase 4, REVAMP_PLAN.md
     * #3b). Classic IntelliJ Platform "dummy file" element-factory technique: parse a throwaway
     * file just to get a well-formed identifier leaf out of the real lexer/parser, then splice
     * that leaf into the real tree via {@code ASTNode.replaceChild}. The throwaway file/tree is
     * never attached anywhere and is simply garbage-collected once the leaf has been detached
     * from it by the caller's {@code replaceChild}.
     */
    private static final java.util.regex.Pattern VALID_IDENTIFIER = java.util.regex.Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");

    @NotNull
    public static ASTNode createIdentifierNode(@NotNull Project project, @NotNull String name) {
        if (!VALID_IDENTIFIER.matcher(name).matches()) {
            throw new IncorrectOperationException("Not a valid MQL identifier: " + name);
        }
        PsiFile dummyFile = PsiFileFactory.getInstance(project)
                .createFileFromText("_mql4_rename_dummy_.mq4", MQL4Language.INSTANCE, "void " + name + "(){}");
        MQL4FunctionElement function = PsiTreeUtil.findChildOfType(dummyFile, MQL4FunctionElement.class);
        PsiElement identifier = function == null ? null : function.getNameIdentifier();
        if (identifier == null) {
            throw new IncorrectOperationException("Cannot build an identifier for name: " + name);
        }
        return identifier.getNode();
    }
}
