/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.index;

import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.stubs.StringStubIndexExtension;
import com.intellij.psi.stubs.StubIndex;

import java.util.Collection;

import static ru.investflow.mql.psi.stub.MQL4StubElements.STUB_SCHEMA_VERSION;

public abstract class MQL4AbstractStringStubIndex<Psi extends PsiElement> extends StringStubIndexExtension<Psi> {

    @Override
    public int getVersion() {
        return STUB_SCHEMA_VERSION;
    }

    public Collection<String> getAllKeys(Project project) {
        return StubIndex.getInstance().getAllKeys(getKey(), project);
    }

}
