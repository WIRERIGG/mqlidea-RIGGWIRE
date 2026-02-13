/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.db;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public record ProblemRecord(
        long id,
        @NotNull String fileUrl,
        @NotNull String filePath,
        int line,
        @NotNull String severity,
        @NotNull String message,
        @NotNull String inspectionName,
        @Nullable String fixHint,
        long firstSeenAt,
        long lastSeenAt,
        long resolvedAt
) {
    public boolean isResolved() {
        return resolvedAt > 0;
    }
}
