/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.refactoring;

import com.intellij.lang.refactoring.RefactoringSupportProvider;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Enables in-place (Shift-F6) rename for every named PSI kind added in Phase 4
 * (REVAMP_PLAN.md #3b): functions, classes/structs/interfaces, enums, enum constants, parameters
 * and variables (local, global and member field, which now share one PSI shape -- see
 * {@link com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement}).
 */
public class MqlRefactoringSupportProvider extends RefactoringSupportProvider {

    @Override
    public boolean isMemberInplaceRenameAvailable(@NotNull PsiElement element, PsiElement context) {
        return isRenameableMqlElement(element);
    }

    @Override
    public boolean isInplaceRenameAvailable(@NotNull PsiElement element, PsiElement context) {
        return isRenameableMqlElement(element);
    }

    private static boolean isRenameableMqlElement(@NotNull PsiElement element) {
        return element instanceof MQL4FunctionElement
                || element instanceof MQL4ClassElement
                || element instanceof MQL4EnumElement
                || element instanceof MQL4EnumFieldElement
                || element instanceof MQL4FunctionArgElement
                || element instanceof MQL4VarDefinitionElement;
    }
}
