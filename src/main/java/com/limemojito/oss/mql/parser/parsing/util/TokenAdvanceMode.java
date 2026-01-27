/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing.util;

public enum TokenAdvanceMode {
    /**
     * Lexer will be advanced for the stop token found.
     */
    ADVANCE,
    /**
     * Lexer will not be advanced for the stop token found, position before stop token will be returned.
     */
    DO_NOT_ADVANCE
}
