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
import com.intellij.psi.PsiWhiteSpace;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.doc.StdLibCatalog;
import com.limemojito.oss.mql.doc.StdLibMethod;
import com.limemojito.oss.mql.psi.MQL4Elements;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Member completion after {@code .} for Standard Library-typed locals/parameters (REVAMP_PLAN.md
 * Phase 6, "Done when: typing {@code CTrade tr; tr.} completes Std-Lib methods").
 *
 * <p><b>Known limitation (intentionally left as a TODO, per the phase's own constraint):</b> the
 * parser doesn't build a real declaration PSI node for a custom-class-typed local -- only
 * built-in {@code DATA_TYPES} produce a {@code VAR_DECLARATION_STATEMENT}
 * ({@link com.limemojito.oss.mql.parser.parsing.statement.VarDeclarationStatement#parseVarDeclaration}
 * gates on {@code MQL4TokenSets.DATA_TYPES}), so {@code CTrade trade;} has no PSI-level type to
 * read. A real fix needs a type model (inferring/attaching a type to every declaration and
 * expression) that is out of scope for this phase. Until then this provider uses a best-effort
 * <em>text heuristic</em>: scan the file text before the qualifier for the nearest
 * {@code ClassName qualifierName} pattern and, if {@code ClassName} is a known Standard Library
 * class, propose its (+ inherited) methods. This covers the common "declare, then dot" case but
 * not reassignment, factory-returned types, array elements, or genuinely type-inferring
 * completion -- a real type-aware member model is future work.</p>
 */
public class MQL4StdLibMemberCompletionProvider extends CompletionProvider<CompletionParameters> {

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiElement position = parameters.getPosition();
        PsiElement dot = prevMeaningfulLeaf(position);
        if (!isElementType(dot, MQL4Elements.DOT)) {
            return;
        }
        PsiElement qualifier = prevMeaningfulLeaf(dot);
        if (!isElementType(qualifier, MQL4Elements.IDENTIFIER)) {
            return;
        }
        String qualifierName = qualifier.getText();
        String className = guessDeclaredStdLibType(parameters.getOriginalFile().getText(), qualifier.getTextRange().getStartOffset(), qualifierName);
        if (className == null) {
            return;
        }
        for (StdLibMethod method : StdLibCatalog.methodsIncludingInherited(className)) {
            LookupElementBuilder builder = LookupElementBuilder.create(method.name)
                    .withIcon(AllIcons.Nodes.Method)
                    .withTailText(method.paramsTailText(), true)
                    .withInsertHandler(ParenthesesInsertHandler.getInstance(!method.params.isEmpty()));
            if (method.returnType != null && !method.returnType.isEmpty()) {
                builder = builder.withTypeText(method.returnType);
            }
            result.addElement(builder);
        }
    }

    /**
     * Heuristic (see class javadoc): looks for the nearest preceding {@code ClassName qualifierName}
     * text pattern -- covers a local declaration ({@code CTrade tr;}), a by-ref parameter
     * ({@code CTrade &tr}), or a pointer ({@code CTrade *tr}) -- and returns {@code ClassName} only
     * if it's a known Standard Library class.
     */
    @Nullable
    static String guessDeclaredStdLibType(@NotNull String fileText, int qualifierOffset, @NotNull String qualifierName) {
        if (qualifierOffset > fileText.length()) {
            qualifierOffset = fileText.length();
        }
        String before = fileText.substring(0, qualifierOffset);
        Pattern declPattern = Pattern.compile("\\b([A-Za-z_]\\w*)\\s*[&*]?\\s*" + Pattern.quote(qualifierName) + "\\b");
        Matcher m = declPattern.matcher(before);
        String lastCandidate = null;
        while (m.find()) {
            lastCandidate = m.group(1);
        }
        if (lastCandidate == null || StdLibCatalog.get(lastCandidate) == null) {
            return null;
        }
        return lastCandidate;
    }

    private static boolean isElementType(@Nullable PsiElement element, @NotNull IElementType type) {
        return element != null && element.getNode() != null && element.getNode().getElementType() == type;
    }

    @Nullable
    private static PsiElement prevMeaningfulLeaf(@Nullable PsiElement element) {
        PsiElement e = element == null ? null : PsiTreeUtil.prevLeaf(element);
        while (e instanceof PsiWhiteSpace) {
            e = PsiTreeUtil.prevLeaf(e);
        }
        return e;
    }
}
