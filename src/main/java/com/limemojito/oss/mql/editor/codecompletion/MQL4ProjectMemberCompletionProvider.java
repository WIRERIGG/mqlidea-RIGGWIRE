/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionParameters;
import com.intellij.codeInsight.completion.CompletionProvider;
import com.intellij.codeInsight.completion.CompletionResultSet;
import com.intellij.codeInsight.completion.util.ParenthesesInsertHandler;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.icons.AllIcons;
import com.intellij.psi.PsiElement;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import com.limemojito.oss.mql.reference.MqlTypeResolver;

/**
 * Dot-member completion for PROJECT class types (Phase 5), the type-resolved sibling of
 * {@link MQL4StdLibMemberCompletionProvider} (which covers only bundled Standard Library classes).
 * Registered on the same {@code afterDot} pattern; when the qualifier's type resolves to a project
 * {@link MQL4ClassElement} via {@link MqlTypeResolver} it offers that class's (and its bases')
 * fields and methods. Std-Lib-typed and project-typed receivers are disjoint, so the two providers
 * never double-propose.
 */
public class MQL4ProjectMemberCompletionProvider extends CompletionProvider<CompletionParameters> {

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiElement position = parameters.getPosition();
        PsiElement dot = MqlTypeResolver.prevMeaningfulLeaf(position);
        if (dot == null || dot.getNode() == null || dot.getNode().getElementType() != MQL4Elements.DOT) {
            return;
        }
        PsiElement qualifier = MqlTypeResolver.prevMeaningfulLeaf(dot);
        if (qualifier == null) {
            return;
        }
        MQL4ClassElement cls = MqlTypeResolver.resolveQualifierClass(qualifier);
        if (cls == null) {
            return;
        }
        for (PsiElement member : MqlResolveUtil.collectAllMembers(cls)) {
            if (member instanceof MQL4FunctionElement method) {
                String name = method.getFunctionName();
                if (name == null || name.isEmpty() || MQL4FunctionElement.UNKNOWN_NAME.equals(name)) {
                    continue;
                }
                String signature = method.getSignature();
                result.addElement(LookupElementBuilder.create(name)
                        .withIcon(AllIcons.Nodes.Method)
                        .withTailText("(" + signature + ")", true)
                        .withInsertHandler(ParenthesesInsertHandler.getInstance(!signature.isEmpty())));
            } else if (member instanceof MQL4VarDefinitionElement field) {
                String name = field.getName();
                if (name != null && !name.isEmpty()) {
                    result.addElement(LookupElementBuilder.create(name).withIcon(AllIcons.Nodes.Field));
                }
            }
        }
    }
}
