/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.index;

import com.intellij.navigation.ChooseByNameContributor;
import com.intellij.navigation.NavigationItem;
import com.intellij.openapi.project.DumbService;
import com.intellij.openapi.project.Project;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.util.ArrayUtil;
import com.intellij.util.containers.HashSet;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;

import java.util.Collection;

public class MQL4GotoClassContributor implements ChooseByNameContributor {

    @NotNull
    public String[] getNames(final Project project, final boolean includeNonProjectItems) {
        // The stub index is unavailable while indexing — return empty instead of throwing.
        if (DumbService.isDumb(project)) {
            return ArrayUtil.EMPTY_STRING_ARRAY;
        }
        MQL4ClassNameIndex index = MQL4ClassNameIndex.getInstance();
        Collection<String> classes = index.getAllKeys(project);
        return ArrayUtil.toStringArray(new HashSet<>(classes));
    }

    @NotNull
    public NavigationItem[] getItemsByName(String name, String pattern, Project project, boolean includeNonProjectItems) {
        if (DumbService.isDumb(project)) {
            return NavigationItem.EMPTY_NAVIGATION_ITEM_ARRAY;
        }
        MQL4ClassNameIndex index = MQL4ClassNameIndex.getInstance();
        Collection<MQL4ClassElement> classes = index.get(name, project, GlobalSearchScope.allScope(project));
        return classes.toArray(new NavigationItem[0]);
    }
}
