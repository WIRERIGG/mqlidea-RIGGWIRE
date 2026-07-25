/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.spellchecker.BundledDictionaryProvider;
import org.jetbrains.annotations.NotNull;

/**
 * Bundles {@code spellcheck/mql.dic} (common MQL/MetaTrader terms) so the spellchecker doesn't
 * flag everyday API and trading vocabulary in comments, strings and identifiers.
 */
public class MqlBundledDictionaryProvider implements BundledDictionaryProvider {
    @Override
    public String @NotNull [] getBundledDictionaries() {
        return new String[]{"/spellcheck/mql.dic"};
    }
}
