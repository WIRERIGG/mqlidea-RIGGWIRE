/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.db;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

public record ClaudeTask(
        long id,
        long problemId,
        @Nullable String diff,
        @NotNull String status,
        long createdAt,
        long appliedAt
) {
    public static final String STATUS_PENDING = "pending";
    public static final String STATUS_IN_PROGRESS = "in_progress";
    public static final String STATUS_COMPLETED = "completed";
    public static final String STATUS_FAILED = "failed";
    public static final String STATUS_APPLIED = "applied";

    public boolean isApplied() {
        return appliedAt > 0;
    }
}
