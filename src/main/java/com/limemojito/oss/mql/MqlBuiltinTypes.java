/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import java.util.Set;

/**
 * Built-in MQL5 type names the lexer leaves as IDENTIFIERs, because MQL4 doesn't reserve them
 * (MetaEditor rejects each as a variable name in MQL5).
 */
public final class MqlBuiltinTypes {

    /** Matrices and vectors (Matrix and Vector Methods) and {@code complex}. */
    public static final Set<String> MQL5_TYPES = Set.of(
            "vector", "vectorf", "vectorc", "matrix", "matrixf", "matrixc", "complex");

    private MqlBuiltinTypes() {
    }
}
