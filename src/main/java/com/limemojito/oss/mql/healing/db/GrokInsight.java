/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing.db;

import org.jetbrains.annotations.NotNull;

public record GrokInsight(
        long id,
        long problemId,
        @NotNull String insight,
        long createdAt
) {
}
