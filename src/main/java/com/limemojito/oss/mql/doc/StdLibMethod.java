/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import java.util.List;

/**
 * One public method (or constructor) of an MQL5 Standard Library class, scraped from the real
 * {@code Include/*.mqh} headers by the one-off {@code tools.GenerateStdlibCatalog} generator and
 * committed as {@code mql/doc/mql5-stdlib.json} (REVAMP_PLAN.md Phase 6 deliverable 2).
 */
public final class StdLibMethod {

    public String name;
    public String returnType;
    public List<String> params;
    public String signature;
    public boolean isConstructor;

    public StdLibMethod() {
    }

    public StdLibMethod(String name, String returnType, List<String> params, String signature, boolean isConstructor) {
        this.name = name;
        this.returnType = returnType;
        this.params = params;
        this.signature = signature;
        this.isConstructor = isConstructor;
    }

    public String paramsTailText() {
        return "(" + String.join(", ", params == null ? List.<String>of() : params) + ")";
    }
}
