/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.codeInsight.navigation.actions.TypeDeclarationProvider;
import com.intellij.psi.PsiElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Go To Type Declaration (Ctrl+Shift+B) for MQL: from a variable/parameter (or a use of one) jumps
 * to the declaration of its class type. Reuses the Phase-5 declared-type resolution
 * ({@link MqlTypeResolver} / {@link MqlResolveUtil#findClassByName}); returns {@code null} when the
 * symbol has no project-class type (a primitive, a built-in, or an unresolved type), so there is no
 * wrong jump.
 */
public final class MqlTypeDeclarationProvider implements TypeDeclarationProvider {

    @Override
    public PsiElement @Nullable [] getSymbolTypeDeclarations(@NotNull PsiElement symbol) {
        MQL4ClassElement type = resolveTypeClass(symbol);
        return type == null ? null : new PsiElement[]{type};
    }

    @Nullable
    private static MQL4ClassElement resolveTypeClass(@NotNull PsiElement symbol) {
        // A resolved declaration element: read its declared type name and look up the class.
        if (symbol instanceof MQL4VarDefinitionElement var) {
            return classForName(var.getDeclaredTypeName(), symbol);
        }
        if (symbol instanceof MQL4FunctionArgElement arg) {
            return classForName(arg.getDeclaredTypeName(), symbol);
        }
        // A bare identifier leaf (a use of a variable/parameter): type it as a receiver would be.
        if (symbol.getNode() != null && symbol.getNode().getElementType() == MQL4Elements.IDENTIFIER) {
            return MqlTypeResolver.resolveQualifierClass(symbol);
        }
        return null;
    }

    @Nullable
    private static MQL4ClassElement classForName(@Nullable String typeName, @NotNull PsiElement context) {
        if (typeName == null || typeName.isEmpty()) {
            return null;
        }
        return MqlResolveUtil.findClassByName(typeName, context.getProject(), context);
    }
}
