/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.util;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public class ObjectUtils {

    @NotNull
    public static <T> T firstNonNull(@Nullable T v1, @NotNull T v2) {
        return v1 == null ? v2 : v1;
    }

}
