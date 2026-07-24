/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.doc;

import java.util.List;

/**
 * One MQL5 Standard Library class (e.g. {@code CTrade}, {@code CArrayObj}, {@code CPositionInfo}),
 * scraped from the real {@code Include/*.mqh} headers -- see {@link StdLibMethod}.
 */
public final class StdLibClass {

    public String name;

    /** Base class name (public inheritance only), or {@code null} for a root class like {@code CObject}. */
    public String parent;

    /** Path of the header this class was scraped from, relative to the Include root, for quick-doc/debugging. */
    public String file;

    public List<StdLibMethod> methods;

    public StdLibClass() {
    }

    public StdLibClass(String name, String parent, String file, List<StdLibMethod> methods) {
        this.name = name;
        this.parent = parent;
        this.file = file;
        this.methods = methods;
    }
}
