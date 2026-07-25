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
import com.intellij.psi.impl.source.resolve.ResolveCache;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.IncorrectOperationException;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.psi.MQL4Elements;

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

    /** Shared cached resolver — the actual resolution runs once and is reused until a PSI change. */
    private static final ResolveCache.PolyVariantResolver<MqlReference> RESOLVER =
            (ref, incompleteCode) -> ref.resolveUncached();

    @Override
    public ResolveResult @NotNull [] multiResolve(boolean incompleteCode) {
        if (!myElement.isValid()) {
            return ResolveResult.EMPTY_ARRAY;
        }
        // ResolveCache makes repeat resolves (highlight, Ctrl-click, isSoft's own resolve()) free
        // until a PSI modification, instead of re-running the 3-tier #include-closure resolution.
        return ResolveCache.getInstance(myElement.getProject()).resolveWithCaching(this, RESOLVER, false, incompleteCode);
    }

    private ResolveResult @NotNull [] resolveUncached() {
        String name = myElement.getText();
        if (name.isEmpty()) {
            return ResolveResult.EMPTY_ARRAY;
        }
        // Member access (`obj.field` / `obj.method()`): resolve the member *inside the receiver's
        // resolved class type* (Phase 5). If the receiver's type doesn't resolve to a project class,
        // fall back to today's behavior (EMPTY_ARRAY) -- never resolve `field` as a free identifier,
        // which would wrongly jump to any same-named global/function in the include closure.
        if (isMemberAccess()) {
            return toResults(MqlTypeResolver.resolveMember(myElement));
        }
        List<PsiElement> targets = MqlResolveUtil.resolve(myElement, name);
        return toResults(targets);
    }

    private static ResolveResult @NotNull [] toResults(@NotNull List<PsiElement> targets) {
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
        // Member accesses are intentionally unresolved (see multiResolve) until type inference
        // exists — they must never be flagged as an unresolved-reference error.
        if (isMemberAccess()) {
            return true;
        }
        // Honesty rule (REVAMP_PLAN.md #3b): MQL has ~2,000 built-in functions/constants we don't
        // yet resolve to real PSI (that needs the synthetic-PSI std-lib catalog planned for Phase
        // 6). Until then, a name that IS a documented built-in must never be treated as an error
        // by any future "unresolved reference" check -- mark it soft instead of hard-failing.
        return resolve() == null && MQL4DocumentationProvider.getEntryByText(myElement.getText()) != null;
    }

    /** True when this identifier is the member side of a {@code receiver.member} access (preceded by {@code .}). */
    private boolean isMemberAccess() {
        PsiElement prev = PsiTreeUtil.prevVisibleLeaf(myElement);
        return prev != null && prev.getNode().getElementType() == MQL4Elements.DOT;
    }

    @NotNull
    @Override
    public PsiElement handleElementRename(@NotNull String newElementName) throws IncorrectOperationException {
        return myElement.replace(com.limemojito.oss.mql.psi.MQL4ElementsFactory.createIdentifierNode(myElement.getProject(), newElementName).getPsi());
    }
}
