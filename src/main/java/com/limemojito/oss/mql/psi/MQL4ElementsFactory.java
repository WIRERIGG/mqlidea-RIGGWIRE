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
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;
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

    private final static Map<ASTNode, Function<ASTNode, PsiElement>> ELEMENT_FACTORY = Collections.synchronizedMap(new HashMap<>());

    public static PsiElement createElement(@NotNull ASTNode node) {
        Function<ASTNode, PsiElement> psiFunction = ELEMENT_FACTORY.computeIfAbsent(node, n -> {
            IElementType type = n.getElementType();
            if (type == PREPROCESSOR_PROPERTY_BLOCK) {
                return MQL4PreprocessorPropertyBlock::new;
            }
            if (type == PREPROCESSOR_INCLUDE_BLOCK) {
                return MQL4PreprocessorIncludeBlock::new;
            }
            if (type == FUNCTION_DECLARATION || type == FUNCTION) {
                return MQL4FunctionElement::new;
            }
            if (type == ENUM_STATEMENT) {
                return MQL4EnumElement::new;
            }
            if (type == ENUM_FIELD) {
                return MQL4EnumFieldElement::new;
            }
            if (type == MQL4Elements.CLASS) {
                return MQL4ClassElement::new;
            }
            if (type == VAR_DEFINITION) {
                return MQL4VarDefinitionElement::new;
            }
            if (type == FUNCTION_ARG) {
                return MQL4FunctionArgElement::new;
            }

            return MQL4PsiElement::new;
        });
        return psiFunction.apply(node);
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
