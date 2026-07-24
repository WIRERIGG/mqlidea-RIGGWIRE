/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import java.util.List;

/**
 * One built-in function's signature, extracted from the bundled doc HTML syntax box by the
 * one-off {@code tools.GenerateBuiltinSignatures} generator and committed as
 * {@code mql/doc/mql4-signatures.json} (REVAMP_PLAN.md Phase 6, deliverable 1). Loaded at runtime
 * by {@link BuiltinSignatureCatalog} -- nothing parses HTML at IDE runtime.
 */
public final class BuiltinSignature {

    /** Function name, e.g. {@code "OrderSend"}. */
    public String name;

    /** Return type text, e.g. {@code "int"}; {@code null}/empty for constructors (not applicable to plain functions). */
    public String returnType;

    /** Each parameter's raw declaration text, e.g. {@code "string comment=NULL"}, in order. */
    public List<String> params;

    /** Full one-line signature text, e.g. {@code "int OrderSend(string symbol, int cmd, ...)"}. */
    public String signature;

    public BuiltinSignature() {
    }

    public BuiltinSignature(String name, String returnType, List<String> params, String signature) {
        this.name = name;
        this.returnType = returnType;
        this.params = params;
        this.signature = signature;
    }

    /** Tail text for a completion lookup element / param-info popup: {@code "(a, b, c)"}. */
    public String paramsTailText() {
        return "(" + String.join(", ", params == null ? List.<String>of() : params) + ")";
    }
}
