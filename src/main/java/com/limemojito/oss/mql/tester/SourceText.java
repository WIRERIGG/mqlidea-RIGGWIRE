/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import org.jetbrains.annotations.NotNull;

/** MQL source for pattern matching that must not look inside comments or strings. */
public final class SourceText {

    private SourceText() {
    }

    /**
     * {@code text} with comments and string/char literal contents blanked to spaces, so patterns
     * never match inside them and every offset still points at the same source position.
     */
    @NotNull
    public static String code(@NotNull CharSequence text) {
        StringBuilder out = new StringBuilder(text);
        int i = 0;
        int n = text.length();
        while (i < n) {
            char c = text.charAt(i);
            if (c == '/' && i + 1 < n && text.charAt(i + 1) == '/') {
                while (i < n && text.charAt(i) != '\n') {
                    out.setCharAt(i++, ' ');
                }
            } else if (c == '/' && i + 1 < n && text.charAt(i + 1) == '*') {
                while (i < n && !(text.charAt(i) == '*' && i + 1 < n && text.charAt(i + 1) == '/')) {
                    blank(out, i++);
                }
                if (i < n) {
                    out.setCharAt(i++, ' ');
                    out.setCharAt(i++, ' ');
                }
            } else if (c == '"' || c == '\'') {
                i++;
                while (i < n && text.charAt(i) != c && text.charAt(i) != '\n') {
                    if (text.charAt(i) == '\\' && i + 1 < n) {
                        out.setCharAt(i++, ' ');
                    }
                    out.setCharAt(i++, ' ');
                }
                i++;
            } else {
                i++;
            }
        }
        return out.toString();
    }

    private static void blank(@NotNull StringBuilder out, int i) {
        if (out.charAt(i) != '\n') {
            out.setCharAt(i, ' ');
        }
    }
}
