/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.index;

import com.intellij.navigation.ChooseByNameContributor;
import com.intellij.navigation.NavigationItem;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.DumbService;
import com.intellij.openapi.project.Project;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.stubs.StubIndex;
import com.intellij.util.ArrayUtil;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

public class MQL4GotoSymbolContributor implements ChooseByNameContributor {

    @NotNull
    public String[] getNames(Project project, boolean includeNonProjectItems) {
        if (DumbService.isDumb(project)) {
            return ArrayUtil.EMPTY_STRING_ARRAY;
        }
        // Stream the index keys via processAllKeys rather than materializing each index's full key
        // Collection first (getAllKeys) — same set of names collected, one fewer intermediate list.
        Set<String> results = new HashSet<>();
        StubIndex stubIndex = StubIndex.getInstance();
        stubIndex.processAllKeys(MQL4ClassNameIndex.getInstance().getKey(), project, key -> {
            ProgressManager.checkCanceled();
            results.add(key);
            return true;
        });
        stubIndex.processAllKeys(MQL4FunctionNameIndex.getInstance().getKey(), project, key -> {
            ProgressManager.checkCanceled();
            results.add(key);
            return true;
        });

        return ArrayUtil.toStringArray(results);
    }

    @NotNull
    public NavigationItem[] getItemsByName(String name, String pattern, Project project, boolean includeNonProjectItems) {
        if (DumbService.isDumb(project)) {
            return NavigationItem.EMPTY_NAVIGATION_ITEM_ARRAY;
        }
        GlobalSearchScope scope = GlobalSearchScope.allScope(project);

        Collection<MQL4ClassElement> classes = MQL4ClassNameIndex.getInstance().get(name, project, scope);
        List<NavigationItem> result = new ArrayList<>(classes);

        Collection<MQL4FunctionElement> functions = MQL4FunctionNameIndex.getInstance().get(name, project, scope);
        result.addAll(functions);

        return result.toArray(new NavigationItem[0]);
    }
}
