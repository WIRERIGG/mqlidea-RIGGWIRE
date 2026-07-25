/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.refactoring;

import com.intellij.lang.refactoring.RefactoringSupportProvider;
import com.intellij.psi.PsiElement;
import com.intellij.refactoring.RefactoringActionHandler;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4File;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Enables the refactorings the plugin supports for MQL PSI:
 * <ul>
 *     <li>In-place (Shift-F6) rename for every named PSI kind added in Phase 4 (REVAMP_PLAN.md #3b):
 *     functions, classes/structs/interfaces, enums, enum constants, parameters and variables (local,
 *     global and member field, which share {@link MQL4VarDefinitionElement}).</li>
 *     <li>Phase 6b: Extract Variable ({@link #getIntroduceVariableHandler()}), a conservative
 *     selection-to-{@code <type> name = expr;} introduction.</li>
 *     <li>Phase 6c: Safe Delete ({@link #isSafeDeleteAvailable(PsiElement)}) for top-level functions
 *     and class members -- the platform's SafeDeleteProcessor runs the (now member-aware, Phase 5)
 *     Find Usages and blocks deletion of anything still referenced.</li>
 * </ul>
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

    // ---- Phase 6b: Extract Variable --------------------------------------------------------

    @Override
    public boolean isAvailable(@NotNull PsiElement context) {
        return context.getContainingFile() instanceof MQL4File;
    }

    @Nullable
    @Override
    public RefactoringActionHandler getIntroduceVariableHandler() {
        return new MqlIntroduceVariableHandler();
    }

    @Nullable
    @Override
    public RefactoringActionHandler getIntroduceVariableHandler(PsiElement element) {
        return new MqlIntroduceVariableHandler();
    }

    // ---- Phase 6c: Safe Delete -------------------------------------------------------------

    @Override
    public boolean isSafeDeleteAvailable(@NotNull PsiElement element) {
        return element instanceof MQL4FunctionElement
                || element instanceof MQL4ClassElement
                || element instanceof MQL4EnumElement
                || element instanceof MQL4EnumFieldElement
                || element instanceof MQL4VarDefinitionElement;
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
