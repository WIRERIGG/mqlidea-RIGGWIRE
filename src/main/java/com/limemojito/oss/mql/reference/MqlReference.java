/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.openapi.util.TextRange;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiElementResolveResult;
import com.intellij.psi.PsiPolyVariantReferenceBase;
import com.intellij.psi.ResolveResult;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;

import java.util.List;

/**
 * Reference attached (via {@link MqlReferenceContributor}) to every IDENTIFIER leaf that is not
 * itself a declaration name: local/parameter reads, function calls, class/base-class type names,
 * enum type names, global variable reads/writes. See {@link MqlResolveUtil} for the resolution
 * order (REVAMP_PLAN.md #3b).
 */
public class MqlReference extends PsiPolyVariantReferenceBase<PsiElement> {

    public MqlReference(@NotNull PsiElement element) {
        super(element, new TextRange(0, element.getTextLength()));
    }

    @Override
    public ResolveResult @NotNull [] multiResolve(boolean incompleteCode) {
        String name = myElement.getText();
        if (name.isEmpty()) {
            return ResolveResult.EMPTY_ARRAY;
        }
        List<PsiElement> targets = MqlResolveUtil.resolve(myElement, name);
        if (targets.isEmpty()) {
            return ResolveResult.EMPTY_ARRAY;
        }
        ResolveResult[] results = new ResolveResult[targets.size()];
        for (int i = 0; i < targets.size(); i++) {
            results[i] = new PsiElementResolveResult(targets.get(i));
        }
        return results;
    }

    @Override
    public Object @NotNull [] getVariants() {
        // Resolve-ranked completion is a Phase 6 deliverable (REVAMP_PLAN.md); this reference is
        // resolve-only for now.
        return EMPTY_ARRAY;
    }

    @Override
    public boolean isSoft() {
        // Honesty rule (REVAMP_PLAN.md #3b): MQL has ~2,000 built-in functions/constants we don't
        // yet resolve to real PSI (that needs the synthetic-PSI std-lib catalog planned for Phase
        // 6). Until then, a name that IS a documented built-in must never be treated as an error
        // by any future "unresolved reference" check -- mark it soft instead of hard-failing.
        return resolve() == null && MQL4DocumentationProvider.getEntryByText(myElement.getText()) != null;
    }

    @NotNull
    @Override
    public PsiElement handleElementRename(@NotNull String newElementName) throws IncorrectOperationException {
        return myElement.replace(com.limemojito.oss.mql.psi.MQL4ElementsFactory.createIdentifierNode(myElement.getProject(), newElementName).getPsi());
    }
}
