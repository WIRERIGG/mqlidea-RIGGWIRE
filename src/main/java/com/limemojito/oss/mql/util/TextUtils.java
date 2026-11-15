/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.util;

import org.jetbrains.annotations.Contract;
import org.jetbrains.annotations.Nullable;

import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Plain text related utils.
 */
public class TextUtils {

    @Contract("null -> true")
    public static boolean isEmpty(@Nullable String v) {
        return v == null || v.isEmpty();
    }

    @Contract("null,_ -> null")
    public static String limit(@Nullable String t, int maxLen) {
        if (t == null || t.length() <= maxLen) {
            return t;
        }
        return t.substring(0, maxLen);
    }

    @Contract("null,_ -> null")
    public static String abbreviate(@Nullable String text, int maxLen) {
        if (text == null || text.length() <= maxLen) {
            return text;
        }
        if (maxLen <= 1) {
            return text.substring(0, maxLen);
        }
        return text.substring(0, maxLen - 1) + "…";
    }

    public static boolean equals(String s1, String s2) {
        return (s1 == null && s2 == null) || (s1 != null && s1.equals(s2));
    }

    private static final Pattern WS_PATTERN = Pattern.compile("\\s+");

    @Contract("null -> null")
    public static String simplify(@Nullable String s) {
        if (s == null) {
            return null;
        }
        Matcher matcher = WS_PATTERN.matcher(s);
        return matcher.replaceAll(" ");
    }

    private static final String[] XML_ENTITIES = {"&lt;", "&gt;", "&quot;", "&amp;"};
    private static final String[] XML_CHARS = {"<", ">", "\"", "&"};

    /**
     * Decodes {@code &lt; &gt; &quot; &amp;} exactly as {@code XmlUtil.unescape} does: not
     * {@code &apos;}, and {@code &amp;} last, so {@code &amp;lt;} becomes {@code &lt;}. Kept local: from CLion 2026.3 {@code XmlUtil} lives
     * in the XML plugin, which this plugin does not depend on, and this runs during stub indexing.
     */
    @Contract("null -> null")
    public static String unescape(@Nullable String val) {
        if (val == null || val.indexOf('&') < 0) {
            return val;
        }
        String result = val;
        for (int i = 0; i < XML_ENTITIES.length; i++) {
            result = result.replace(XML_ENTITIES[i], XML_CHARS[i]);
        }
        return result;
    }
}
