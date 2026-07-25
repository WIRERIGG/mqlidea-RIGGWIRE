/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.lang.Language;
import com.intellij.psi.PsiElement;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.ui.breadcrumbs.BreadcrumbsProvider;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

/**
 * Editor breadcrumbs (Phase 3b): a {@code CClass ▸ Method} trail at the bottom of the editor,
 * so you always know which class/function the caret sits in inside a large EA file.
 *
 * <p>Crumb-worthy nodes are exactly the structure-view's own top nodes -- classes/structs
 * ({@link MQL4ClassElement}) and functions/methods ({@link MQL4FunctionElement}) -- and their
 * labels reuse the same names those PSI elements already expose to the structure view.</p>
 *
 * <p>Note: the platform interface is {@code com.intellij.ui.breadcrumbs.BreadcrumbsProvider}
 * (registered under the {@code breadcrumbsInfoProvider} extension point); it exposes a single
 * {@link #getParent(PsiElement)} step rather than a "getParents" list, and the breadcrumbs bar
 * walks it up the tree, keeping every element {@link #acceptElement(PsiElement)} approves.</p>
 */
public class MqlBreadcrumbsProvider implements BreadcrumbsProvider {

    private static final Language[] LANGUAGES = {MQL4Language.INSTANCE};

    @Override
    public Language[] getLanguages() {
        return LANGUAGES;
    }

    @Override
    public boolean acceptElement(@NotNull PsiElement element) {
        return element instanceof MQL4ClassElement || element instanceof MQL4FunctionElement;
    }

    @NotNull
    @Override
    public String getElementInfo(@NotNull PsiElement element) {
        if (element instanceof MQL4ClassElement clazz) {
            return clazz.getTypeName();
        }
        if (element instanceof MQL4FunctionElement function) {
            return function.getFunctionName();
        }
        return "";
    }

    /**
     * Jumps straight to the nearest enclosing crumb-worthy ancestor (class or function), skipping
     * the flat statement/expression nodes in between; the breadcrumbs bar then keeps each such
     * ancestor {@link #acceptElement} approves, yielding the {@code Class ▸ Method} trail.
     */
    @Nullable
    @Override
    public PsiElement getParent(@NotNull PsiElement element) {
        return PsiTreeUtil.getParentOfType(element, MQL4ClassElement.class, MQL4FunctionElement.class);
    }
}
