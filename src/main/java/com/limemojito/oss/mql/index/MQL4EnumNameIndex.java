/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.index;

import com.intellij.openapi.project.Project;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.stubs.StubIndex;
import com.intellij.psi.stubs.StubIndexKey;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;

import java.util.Collection;

public class MQL4EnumNameIndex extends MQL4AbstractStringStubIndex<MQL4EnumElement> {

    private static final MQL4EnumNameIndex INSTANCE = new MQL4EnumNameIndex();

    public static MQL4EnumNameIndex getInstance() {
        return INSTANCE;
    }

    @NotNull
    @Override
    public StubIndexKey<String, MQL4EnumElement> getKey() {
        return MQL4IndexKeys.ENUM_NAME_INDEX_KEY;
    }

    @Override
    public Collection<MQL4EnumElement> get(@NotNull String key, @NotNull Project project, @NotNull GlobalSearchScope scope) {
        return StubIndex.getElements(getKey(), key, project, scope, MQL4EnumElement.class);
    }

}
