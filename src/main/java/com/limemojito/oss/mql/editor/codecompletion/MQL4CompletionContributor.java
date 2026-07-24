/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionContributor;
import com.intellij.codeInsight.completion.CompletionParameters;
import com.intellij.codeInsight.completion.CompletionProvider;
import com.intellij.codeInsight.completion.CompletionResultSet;
import com.intellij.codeInsight.completion.CompletionType;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.patterns.PsiElementPattern;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiRecursiveElementVisitor;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.MQL4Elements;

import static com.intellij.patterns.PlatformPatterns.psiElement;

/**
 * Code completion for MQL4/MQL5 files (REVAMP_PLAN.md Phase 6: "completion that knows the
 * language"). Registration order matters here only in that the narrower contexts
 * (comments/preprocessor/dot-member) are carved out of the general {@code filter} via
 * {@code andNot} so the three general-purpose tiers below never fire somewhere they'd add noise
 * (e.g. proposing global built-ins right after {@code tr.}):
 *
 * <ol>
 *     <li>{@link MQL4LocalScopeCompletionProvider} -- locals/params in scope (highest priority)</li>
 *     <li>{@link MQL4ProjectSymbolCompletionProvider} -- project-wide functions/classes</li>
 *     <li>{@link MQL4BuiltinCompletionProvider} -- dialect-filtered built-ins + Std-Lib class names (lowest priority)</li>
 * </ol>
 *
 * <p>Ranking between the three is enforced by {@code PrioritizedLookupElement} priorities on each
 * provider's lookup elements, not by registration order (multiple providers can and do match the
 * same position).</p>
 */
public class MQL4CompletionContributor extends CompletionContributor {

    public MQL4CompletionContributor() {
        PsiElementPattern.Capture<PsiElement> filter = mql4();

        filter = CommentsCompletions.extend(this, filter);
        filter = PreprocessorCompletions.extend(this, filter);
        filter = PreprocessorPropertyCompletions.extend(this, filter);
        filter = PreprocessorIncludeCompletions.extend(this, filter);

        PsiElementPattern.Capture<PsiElement> afterDot = mql4().afterLeaf(psiElement().withElementType(MQL4Elements.DOT));
        extend(CompletionType.BASIC, afterDot, new MQL4StdLibMemberCompletionProvider());
        filter = filter.andNot(afterDot);

        extend(CompletionType.BASIC, filter, new MQL4LocalScopeCompletionProvider());
        extend(CompletionType.BASIC, filter, new MQL4ProjectSymbolCompletionProvider());
        extend(CompletionType.BASIC, filter, new MQL4BuiltinCompletionProvider());
    }

    /**
     * Adds to completion all named identifiers from file. Retained only for the
     * comment/string/preprocessor-value contexts wired up by {@link CommentsCompletions} and
     * friends, where a plain-text word list (rather than typed symbol completion) is exactly
     * right -- normal code positions now go through the three providers above.
     */
    public static class MQL4IdentifiersCompletionProvider extends CompletionProvider<CompletionParameters> {
        @Override
        protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
            parameters.getOriginalFile().accept(new PsiRecursiveElementVisitor() {
                @Override
                public void visitElement(@NotNull PsiElement element) {
                    super.visitElement(element);
                    if (element.getNode().getElementType() == MQL4Elements.IDENTIFIER) {
                        result.addElement(LookupElementBuilder.create(element.getText()));
                    }
                }
            });
        }
    }

    /**
     * Helper method for all filters.
     */
    static PsiElementPattern.Capture<PsiElement> mql4() {
        return psiElement().withLanguage(MQL4Language.INSTANCE);
    }

}
