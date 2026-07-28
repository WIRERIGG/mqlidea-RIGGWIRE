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

/**
 * Stub index keyed by enum CONSTANT (field) name -> the enclosing {@link MQL4EnumElement}. Enum
 * fields are not stub-backed PSI (only the enum statement is), so the enum element carries its
 * constant names (see {@code MQL4EnumElementStubType.indexStub}). A lookup here yields every enum in
 * scope declaring a constant of the given name; the caller then picks the matching field PSI from the
 * enum's children. Mirrors {@link MQL4EnumNameIndex} exactly, but on the field-name key.
 */
public class MQL4EnumFieldNameIndex extends MQL4AbstractStringStubIndex<MQL4EnumElement> {

    private static final MQL4EnumFieldNameIndex INSTANCE = new MQL4EnumFieldNameIndex();

    public static MQL4EnumFieldNameIndex getInstance() {
        return INSTANCE;
    }

    @NotNull
    @Override
    public StubIndexKey<String, MQL4EnumElement> getKey() {
        return MQL4IndexKeys.ENUM_FIELD_NAME_INDEX_KEY;
    }

    @Override
    public Collection<MQL4EnumElement> get(@NotNull String key, @NotNull Project project, @NotNull GlobalSearchScope scope) {
        return StubIndex.getElements(getKey(), key, project, scope, MQL4EnumElement.class);
    }

}
