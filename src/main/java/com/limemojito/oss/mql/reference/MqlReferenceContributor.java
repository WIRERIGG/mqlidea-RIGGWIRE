/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.patterns.PlatformPatterns;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiReference;
import com.intellij.psi.PsiReferenceContributor;
import com.intellij.psi.PsiReferenceProvider;
import com.intellij.psi.PsiReferenceRegistrar;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;

/**
 * Registers {@link MqlReference} on every IDENTIFIER leaf that is not itself a declaration name
 * (REVAMP_PLAN.md #3b, Phase 4). The MQL parser doesn't wrap call sites / type references in a
 * dedicated "identifier expression" node (function bodies are a tolerant flat statement AST, see
 * {@link com.limemojito.oss.mql.parser.parsing.statement.StatementParsing}), so identifiers are
 * matched by element TYPE rather than by a dedicated PSI class; {@link MqlPsiUtil#isDeclarationNameIdentifier}
 * is what tells a usage apart from a declaration site.
 */
public class MqlReferenceContributor extends PsiReferenceContributor {

    @Override
    public void registerReferenceProviders(@NotNull PsiReferenceRegistrar registrar) {
        registrar.registerReferenceProvider(
                PlatformPatterns.psiElement().withElementType(MQL4Elements.IDENTIFIER),
                new PsiReferenceProvider() {
                    @Override
                    public PsiReference @NotNull [] getReferencesByElement(@NotNull PsiElement element, @NotNull ProcessingContext context) {
                        if (MqlPsiUtil.isDeclarationNameIdentifier(element)) {
                            return PsiReference.EMPTY_ARRAY;
                        }
                        return new PsiReference[]{new MqlReference(element)};
                    }
                });
    }
}
