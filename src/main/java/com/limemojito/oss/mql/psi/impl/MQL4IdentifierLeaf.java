/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.impl;

import com.intellij.psi.ContributedReferenceHost;
import com.intellij.psi.PsiReference;
import com.intellij.psi.impl.source.resolve.reference.ReferenceProvidersRegistry;
import com.intellij.psi.impl.source.tree.LeafPsiElement;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

/**
 * IDENTIFIER leaf that opts into contributor-based references (Phase 4, REVAMP_PLAN.md #3b).
 *
 * <p>The platform's default {@code LeafPsiElement.getReferences()} does NOT consult
 * {@code psi.referenceContributor} registrations -- {@code PsiReferenceServiceImpl} (the code
 * path behind Ctrl-click, Find Usages, rename, etc.) only calls
 * {@code ReferenceProvidersRegistry.getReferencesFromProviders(element)} for elements that
 * implement {@link ContributedReferenceHost}; plain leaves fall through to
 * {@code element.getReference()} (singular, unimplemented, always null). Without this class every
 * identifier's contributed {@code MqlReference} would silently never be found by any platform
 * feature. See {@link MQL4ASTFactory}, which is what actually produces this class for IDENTIFIER
 * tokens instead of the default {@code LeafPsiElement}.</p>
 */
public class MQL4IdentifierLeaf extends LeafPsiElement implements ContributedReferenceHost {

    public MQL4IdentifierLeaf(@NotNull IElementType type, @NotNull CharSequence text) {
        super(type, text);
    }

    @Override
    public PsiReference @NotNull [] getReferences() {
        return ReferenceProvidersRegistry.getReferencesFromProviders(this);
    }
}
