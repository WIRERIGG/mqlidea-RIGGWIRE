/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.psi.stub;

import com.intellij.psi.PsiElement;
import com.intellij.psi.stubs.StubElement;
import org.jetbrains.annotations.Nullable;

/** Stub of a declaration that carries only its name: a {@code typedef} or a {@code #define}. */
public interface MQL4NamedElementStub<T extends PsiElement> extends StubElement<T> {

    /** The declared name, or {@code null} when the declaration is malformed and has none. */
    @Nullable
    String getName();
}
