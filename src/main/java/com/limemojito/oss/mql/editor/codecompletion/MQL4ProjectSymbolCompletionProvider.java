/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionParameters;
import com.intellij.codeInsight.completion.CompletionProvider;
import com.intellij.codeInsight.completion.CompletionResultSet;
import com.intellij.codeInsight.completion.PrioritizedLookupElement;
import com.intellij.codeInsight.completion.util.ParenthesesInsertHandler;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.index.MQL4ClassNameIndex;
import com.limemojito.oss.mql.index.MQL4FunctionNameIndex;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

/**
 * Project-wide symbol completion (REVAMP_PLAN.md Phase 6, deliverable 3): every function/class
 * name in the project's stub indexes, not just identifiers textually present in the current file
 * (the previous {@code MQL4IdentifiersCompletionProvider} behavior, now reserved for
 * comment/string contexts -- see {@link MQL4CompletionContributor}).
 *
 * <p>Ranked above built-ins, below in-scope locals/params (REVAMP_PLAN.md "locals/members first,
 * dialect-filtered built-ins... ranked").</p>
 */
public class MQL4ProjectSymbolCompletionProvider extends CompletionProvider<CompletionParameters> {

    static final double PRIORITY_PROJECT_FUNCTION = 50.0;
    static final double PRIORITY_PROJECT_CLASS = 50.0;

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiFile file = parameters.getOriginalFile();
        Project project = file.getProject();
        GlobalSearchScope scope = GlobalSearchScope.allScope(project);

        MQL4FunctionNameIndex functionIndex = MQL4FunctionNameIndex.getInstance();
        for (String name : functionIndex.getAllKeys(project)) {
            for (MQL4FunctionElement function : functionIndex.get(name, project, scope)) {
                if (!name.equals(function.getFunctionName())) {
                    continue;
                }
                String signatureText = function.getSignature();
                LookupElementBuilder builder = LookupElementBuilder.create(name)
                        .withIcon(function.getPresentation().getIcon(false))
                        .withTailText("(" + signatureText + ")", true)
                        .withTypeText(function.getContainingFile().getName())
                        .withInsertHandler(ParenthesesInsertHandler.getInstance(!signatureText.isEmpty()));
                result.addElement(PrioritizedLookupElement.withPriority(builder, PRIORITY_PROJECT_FUNCTION));
            }
        }

        MQL4ClassNameIndex classIndex = MQL4ClassNameIndex.getInstance();
        for (String name : classIndex.getAllKeys(project)) {
            for (MQL4ClassElement cls : classIndex.get(name, project, scope)) {
                if (!name.equals(cls.getTypeName())) {
                    continue;
                }
                LookupElementBuilder builder = LookupElementBuilder.create(name)
                        .withIcon(MQL4Icons.Class)
                        .withTypeText(cls.getContainingFile().getName());
                result.addElement(PrioritizedLookupElement.withPriority(builder, PRIORITY_PROJECT_CLASS));
            }
        }
    }
}
