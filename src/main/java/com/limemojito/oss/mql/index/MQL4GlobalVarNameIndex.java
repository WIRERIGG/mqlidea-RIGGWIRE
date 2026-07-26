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
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

import java.util.Collection;

/**
 * Project-wide stub index of TOP-LEVEL (file-scope) global variable names. Only VAR_DEFINITION
 * elements whose enclosing VAR_DECLARATION_STATEMENT is a direct child of the file are indexed
 * (see {@link com.limemojito.oss.mql.psi.stub.type.MQL4GlobalVarElementStubType}); class fields
 * and locals are deliberately excluded so a field/local never resolves as a global.
 */
public class MQL4GlobalVarNameIndex extends MQL4AbstractStringStubIndex<MQL4VarDefinitionElement> {

    private static final MQL4GlobalVarNameIndex INSTANCE = new MQL4GlobalVarNameIndex();

    public static MQL4GlobalVarNameIndex getInstance() {
        return INSTANCE;
    }

    @NotNull
    @Override
    public StubIndexKey<String, MQL4VarDefinitionElement> getKey() {
        return MQL4IndexKeys.GLOBAL_VAR_NAME_INDEX_KEY;
    }

    @Override
    public Collection<MQL4VarDefinitionElement> get(@NotNull String key, @NotNull Project project, @NotNull GlobalSearchScope scope) {
        return StubIndex.getElements(getKey(), key, project, scope, MQL4VarDefinitionElement.class);
    }

}
