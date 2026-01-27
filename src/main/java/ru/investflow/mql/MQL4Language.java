/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql;

import com.intellij.lang.Language;

public class MQL4Language extends Language {

    public static final MQL4Language INSTANCE = new MQL4Language();

    private MQL4Language() {
        super("MQL4");
    }
}
