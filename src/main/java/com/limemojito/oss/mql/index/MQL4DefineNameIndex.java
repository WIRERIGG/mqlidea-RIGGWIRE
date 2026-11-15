/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.index;

import com.intellij.openapi.project.Project;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.stubs.StubIndex;
import com.intellij.psi.stubs.StubIndexKey;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.impl.MQL4DefineElement;

import java.util.Collection;

public class MQL4DefineNameIndex extends MQL4AbstractStringStubIndex<MQL4DefineElement> {

    private static final MQL4DefineNameIndex INSTANCE = new MQL4DefineNameIndex();

    public static MQL4DefineNameIndex getInstance() {
        return INSTANCE;
    }

    @NotNull
    @Override
    public StubIndexKey<String, MQL4DefineElement> getKey() {
        return MQL4IndexKeys.DEFINE_NAME_INDEX_KEY;
    }

    /** Elements named {@code key}. */
    public Collection<MQL4DefineElement> getElements(@NotNull String key, @NotNull Project project, @NotNull GlobalSearchScope scope) {
        return StubIndex.getElements(getKey(), key, project, scope, MQL4DefineElement.class);
    }
}
