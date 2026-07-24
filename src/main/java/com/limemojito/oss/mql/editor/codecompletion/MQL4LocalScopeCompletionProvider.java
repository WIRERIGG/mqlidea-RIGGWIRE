/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionParameters;
import com.intellij.codeInsight.completion.CompletionProvider;
import com.intellij.codeInsight.completion.CompletionResultSet;
import com.intellij.codeInsight.completion.PrioritizedLookupElement;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.icons.AllIcons;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.reference.MqlPsiUtil;

/**
 * Locals/parameters visible at the caret (REVAMP_PLAN.md Phase 6, deliverable 3). Ranked highest
 * of the three completion tiers ("locals/params first").
 *
 * <p>This walks the same enclosing-block/function parent chain {@code MqlResolveUtil.resolveLocal}
 * (Phase 4) uses for reference resolution, but collects every declaration in scope instead of
 * stopping at the first name match; it's implemented as its own small scope-walk here (rather than
 * a new method on the Phase 4 {@code reference} package's {@code MqlResolveUtil}) per this phase's
 * constraint to only USE that package, not extend it. It does call the reference package's public
 * {@link MqlPsiUtil#isCodeBlock} helper, which is exactly such a use.</p>
 */
public class MQL4LocalScopeCompletionProvider extends CompletionProvider<CompletionParameters> {

    static final double PRIORITY_LOCAL = 100.0;

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiElement position = parameters.getPosition();
        PsiElement parent = position.getParent();
        while (parent != null) {
            if (parent instanceof MQL4FunctionElement function) {
                addParams(function, result);
            } else if (MqlPsiUtil.isCodeBlock(parent)) {
                addVarsInBlockChildren(parent.getNode(), result);
            }
            parent = parent.getParent();
        }
    }

    private void addParams(@NotNull MQL4FunctionElement function, @NotNull CompletionResultSet result) {
        ASTNode argsList = function.getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        if (argsList == null) {
            return;
        }
        for (ASTNode arg = argsList.getFirstChildNode(); arg != null; arg = arg.getTreeNext()) {
            if (arg.getElementType() == MQL4Elements.FUNCTION_ARG && arg.getPsi() instanceof MQL4FunctionArgElement argElement) {
                addElement(result, argElement.getName(), AllIcons.Nodes.Parameter);
            }
        }
    }

    private void addVarsInBlockChildren(@NotNull ASTNode blockNode, @NotNull CompletionResultSet result) {
        for (ASTNode child = blockNode.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                addVarDefinitionsInDeclaration(child, result);
            }
        }
    }

    private void addVarDefinitionsInDeclaration(@NotNull ASTNode varDeclarationStatement, @NotNull CompletionResultSet result) {
        ASTNode list = varDeclarationStatement.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (list == null) {
            return;
        }
        for (ASTNode def = list.getFirstChildNode(); def != null; def = def.getTreeNext()) {
            if (def.getElementType() == MQL4Elements.VAR_DEFINITION && def.getPsi() instanceof MQL4VarDefinitionElement varElement) {
                addElement(result, varElement.getName(), AllIcons.Nodes.Variable);
            }
        }
    }

    private void addElement(@NotNull CompletionResultSet result, String name, javax.swing.Icon icon) {
        if (name == null || name.isEmpty()) {
            return;
        }
        LookupElementBuilder builder = LookupElementBuilder.create(name).withIcon(icon);
        result.addElement(PrioritizedLookupElement.withPriority(builder, PRIORITY_LOCAL));
    }
}
