/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.doc;

import org.jetbrains.annotations.NotNull;

/**
 * MQL4 documentation entry.
 */
public class DocEntry {

    /**
     * Text in editor.
     */
    @NotNull
    public final String text;

    /**
     * Link to HTML file to show in resources.
     */
    @NotNull
    public final String link;

    /**
     * Type of the entry: keyword, built-in function, built-in constant …
     */
    @NotNull
    public final DocEntryType type;

    public DocEntry(@NotNull String text, @NotNull String link, @NotNull DocEntryType type) {
        this.text = text;
        this.link = link;
        this.type = type;
    }
}
