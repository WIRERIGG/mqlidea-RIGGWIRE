/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing.util;

import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;

import java.util.HashMap;
import java.util.Map;

public class ParsingMarker extends IElementType {

    private static final Map<IElementType, ParsingMarker> MARKERS_CACHE = new HashMap<>();

    @NotNull
    public final IElementType originalToken;

    public ParsingMarker(@NotNull IElementType originalToken) {
        super("ParsingMarker:" + originalToken, originalToken.getLanguage());
        this.originalToken = originalToken;
    }

    public static IElementType forType(@NotNull IElementType source) {
        return MARKERS_CACHE.computeIfAbsent(source, ParsingMarker::new);
    }
}
