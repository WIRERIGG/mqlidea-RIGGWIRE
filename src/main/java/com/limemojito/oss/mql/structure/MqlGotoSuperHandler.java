/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.structure;

import com.intellij.codeInsight.CodeInsightActionHandler;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.project.Project;
import com.intellij.pom.Navigatable;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.util.PsiTreeUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;

import java.util.List;

/**
 * Phase 6a (REVAMP_PLAN.md): Go to Super Method / Super Class ({@code Ctrl+U}) for MQL5 class
 * hierarchies. Registered under the platform {@code codeInsight.gotoSuper} extension point (a
 * {@link CodeInsightActionHandler}, driven by {@code GotoSuperAction}).
 *
 * <ul>
 *     <li>Caret inside an overriding method -&gt; navigates to the overridden base-class method (the
 *     nearest declaration up the {@code CLASS_INHERITANCE_LIST} hierarchy with the same name); if no
 *     base method matches, falls back to the base class itself.</li>
 *     <li>Caret elsewhere in a derived class -&gt; navigates to the (first) base class.</li>
 * </ul>
 * Reuses the Phase-5 base-class resolution ({@link MqlResolveUtil#directBaseClasses} /
 * {@link MqlResolveUtil#findSuperMembers}); does nothing when there is no resolvable super.
 */
public class MqlGotoSuperHandler implements CodeInsightActionHandler {

    @Override
    public void invoke(@NotNull Project project, @NotNull Editor editor, @NotNull PsiFile file) {
        PsiElement target = findSuperTarget(editor, file);
        if (target instanceof Navigatable navigatable && navigatable.canNavigate()) {
            navigatable.navigate(true);
        }
    }

    /**
     * The super declaration a Go-to-Super from the caret should land on (base method, else base
     * class), or {@code null} if there is none. Public so it can be asserted directly in a fixture
     * test without driving the (editor-opening) navigation.
     */
    @Nullable
    public static PsiElement findSuperTarget(@NotNull Editor editor, @NotNull PsiFile file) {
        PsiElement at = file.findElementAt(editor.getCaretModel().getOffset());
        if (at == null) {
            return null;
        }
        MQL4FunctionElement method = PsiTreeUtil.getParentOfType(at, MQL4FunctionElement.class);
        if (method != null) {
            MQL4ClassElement owner = PsiTreeUtil.getParentOfType(method, MQL4ClassElement.class);
            if (owner != null) {
                List<PsiElement> supers = MqlResolveUtil.findSuperMembers(owner, method.getFunctionName());
                if (!supers.isEmpty()) {
                    return supers.get(0);
                }
                MQL4ClassElement base = firstBase(owner);
                if (base != null) {
                    return base;
                }
            }
        }
        MQL4ClassElement cls = PsiTreeUtil.getParentOfType(at, MQL4ClassElement.class);
        return cls == null ? null : firstBase(cls);
    }

    @Nullable
    private static MQL4ClassElement firstBase(@NotNull MQL4ClassElement cls) {
        List<MQL4ClassElement> bases = MqlResolveUtil.directBaseClasses(cls);
        return bases.isEmpty() ? null : bases.get(0);
    }

    @Override
    public boolean startInWriteAction() {
        return false;
    }
}
