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
import com.intellij.codeInsight.lookup.LookupElement;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.icons.AllIcons;
import com.intellij.psi.PsiFile;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MqlBuiltinDialect;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.doc.BuiltinSignature;
import com.limemojito.oss.mql.doc.BuiltinSignatureCatalog;
import com.limemojito.oss.mql.doc.DocEntry;
import com.limemojito.oss.mql.doc.DocEntryType;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.doc.StdLibCatalog;
import com.limemojito.oss.mql.doc.StdLibClass;

/**
 * Real (typed, signature-aware) completion for built-ins (REVAMP_PLAN.md Phase 6, deliverable 3),
 * replacing the flat bare-string list {@link MQL4CompletionContributor} used to emit directly from
 * {@link MQL4DocumentationProvider#getEntries()}.
 *
 * <ul>
 *     <li>Functions get an icon, {@code (params)} tail text from {@link BuiltinSignatureCatalog}
 *     when available, the return type as the type text, and a parentheses insert handler that
 *     drops the caret inside the call (and, courtesy of the platform's parameter-info-on-completion
 *     hook, immediately shows the signature popup).</li>
 *     <li>MQL4-only/MQL5-only functions (see {@link MqlBuiltinDialect}) are never proposed in a
 *     file of the other dialect.</li>
 *     <li>Standard Library class names ({@link StdLibCatalog}) are proposed as type names too --
 *     the bundled doc catalogs don't cover them since they come from a different corpus (the
 *     headers, not the HTML docs).</li>
 *     <li>Constants/types/keywords/preprocessor entries complete as plain lower-priority text,
 *     same as before.</li>
 * </ul>
 *
 * <p>Ranked lowest of the three completion tiers (REVAMP_PLAN.md "locals/params first, then
 * project symbols, then built-ins") via {@link PrioritizedLookupElement}.</p>
 */
public class MQL4BuiltinCompletionProvider extends CompletionProvider<CompletionParameters> {

    static final double PRIORITY_BUILTIN_FUNCTION = 10.0;
    static final double PRIORITY_BUILTIN_OTHER = 5.0;
    static final double PRIORITY_STDLIB_CLASS = 8.0;

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiFile file = parameters.getOriginalFile();
        boolean isMql5 = MqlDialect.isMql5(file);

        for (DocEntry entry : MQL4DocumentationProvider.getEntries()) {
            LookupElement element = buildElement(entry, isMql5);
            if (element != null) {
                result.addElement(element);
            }
        }
        for (String className : StdLibCatalog.all().keySet()) {
            LookupElementBuilder builder = LookupElementBuilder.create(className)
                    .withIcon(AllIcons.Nodes.Class)
                    .withTypeText("Standard Library");
            StdLibClass cls = StdLibCatalog.get(className);
            if (cls != null && cls.parent != null) {
                builder = builder.withTailText(" : " + cls.parent, true);
            }
            result.addElement(PrioritizedLookupElement.withPriority(builder, PRIORITY_STDLIB_CLASS));
        }
    }

    private LookupElement buildElement(@NotNull DocEntry entry, boolean isMql5) {
        if (entry.type == DocEntryType.BuiltInFunction) {
            if (MqlBuiltinDialect.isExcludedFromDialect(entry.text, isMql5)) {
                return null;
            }
            BuiltinSignature sig = BuiltinSignatureCatalog.get(entry.text);
            LookupElementBuilder builder = LookupElementBuilder.create(entry.text)
                    .withIcon(AllIcons.Nodes.Function)
                    .withInsertHandler(ParenthesesInsertHandler.getInstance(sig == null || !sig.params.isEmpty()));
            if (sig != null) {
                builder = builder.withTailText(sig.paramsTailText(), true);
                if (sig.returnType != null && !sig.returnType.isEmpty()) {
                    builder = builder.withTypeText(sig.returnType);
                }
            } else {
                builder = builder.withTailText("(...)", true);
            }
            return PrioritizedLookupElement.withPriority(builder, PRIORITY_BUILTIN_FUNCTION);
        }
        LookupElementBuilder builder = LookupElementBuilder.create(entry.text).withTypeText(typeLabel(entry.type));
        return PrioritizedLookupElement.withPriority(builder, PRIORITY_BUILTIN_OTHER);
    }

    @NotNull
    private static String typeLabel(@NotNull DocEntryType type) {
        return switch (type) {
            case BuiltInConstant -> "constant";
            case Keyword -> "keyword";
            case BuiltInType -> "type";
            case PreprocessorKeyword -> "preprocessor";
            default -> "";
        };
    }
}
