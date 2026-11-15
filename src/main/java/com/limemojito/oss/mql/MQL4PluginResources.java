/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.DynamicBundle;
import org.jetbrains.annotations.Nls;
import org.jetbrains.annotations.NonNls;
import org.jetbrains.annotations.PropertyKey;

/** Messages from {@code messages/plugin.properties}. */
public final class MQL4PluginResources {

    @NonNls
    private static final String BUNDLE_ID = "messages.plugin";

    private static final DynamicBundle BUNDLE = new DynamicBundle(MQL4PluginResources.class, BUNDLE_ID);

    private MQL4PluginResources() {
    }

    @Nls
    public static String message(@PropertyKey(resourceBundle = BUNDLE_ID) String key, Object... params) {
        return BUNDLE.getMessage(key, params);
    }
}
