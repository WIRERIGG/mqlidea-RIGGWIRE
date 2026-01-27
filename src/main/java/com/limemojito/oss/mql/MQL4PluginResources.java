/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.CommonBundle;
import org.jetbrains.annotations.NonNls;
import org.jetbrains.annotations.PropertyKey;

import java.lang.ref.Reference;
import java.lang.ref.SoftReference;
import java.util.ResourceBundle;

public class MQL4PluginResources {
    private static Reference<ResourceBundle> MQL4_BUNDLE;

    @NonNls
    private static final String BUNDLE_ID = "messages.plugin";

    private MQL4PluginResources() {
    }

    public static String message(@PropertyKey(resourceBundle = BUNDLE_ID) String key, Object... params) {
        return CommonBundle.message(getBundle(), key, params);
    }

    private static ResourceBundle getBundle() {
        ResourceBundle bundle = null;
        if (MQL4_BUNDLE != null) bundle = MQL4_BUNDLE.get();
        if (bundle == null) {
            bundle = ResourceBundle.getBundle(BUNDLE_ID);
            MQL4_BUNDLE = new SoftReference<>(bundle);
        }
        return bundle;
    }
}
