/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * One diagnostic emitted by the MetaEditor compiler: a file location plus a severity and message.
 * Line and column are 1-based, exactly as MetaEditor reports them.
 *
 * @param fileName the file MetaEditor attributed the diagnostic to (may be an {@code #include}d header,
 *                 not the compiled program)
 * @param line     1-based line, or 0 for a file-level diagnostic with no location
 * @param column   1-based column, or 0 when none was reported
 * @param severity error / warning / information
 * @param code     MetaEditor's numeric code (e.g. {@code "100"}), or null when absent
 * @param message  the human-readable text
 */
public record CompilerDiagnostic(@NotNull String fileName,
                                 int line,
                                 int column,
                                 @NotNull Severity severity,
                                 @Nullable String code,
                                 @NotNull String message) {

    public enum Severity {ERROR, WARNING, INFORMATION}

    public boolean hasLocation() {
        return line > 0;
    }
}
