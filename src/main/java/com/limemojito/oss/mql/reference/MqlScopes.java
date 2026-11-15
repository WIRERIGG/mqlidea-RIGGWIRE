/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.stubs.StubIndex;
import com.intellij.psi.stubs.StubIndexKey;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import org.jetbrains.annotations.NotNull;

import java.util.Collection;

/**
 * Project-wide lookups that prefer the project. The MetaTrader Include folders are indexed as a
 * library ({@link MqlIncludeLibraryProvider}) and often hold older copies of the project's own
 * headers, so a name the project declares must never also pick up those copies.
 */
public final class MqlScopes {

    private MqlScopes() {
    }

    /**
     * The project's declarations of {@code name}, or the library's when the project has none. A
     * library declaration never stands in for a documented built-in: Include folders carry MQL4
     * compatibility shims named {@code OrderSend}, {@code TimeHour} and so on.
     */
    @NotNull
    public static <T extends PsiElement> Collection<T> projectFirst(@NotNull StubIndexKey<String, T> key, @NotNull String name,
                                                                   @NotNull Project project, @NotNull Class<T> type) {
        Collection<T> own = StubIndex.getElements(key, name, project, GlobalSearchScope.projectScope(project), type);
        if (!own.isEmpty() || MQL4DocumentationProvider.getEntryByText(name) != null) {
            return own;
        }
        return StubIndex.getElements(key, name, project, GlobalSearchScope.allScope(project), type);
    }
}
