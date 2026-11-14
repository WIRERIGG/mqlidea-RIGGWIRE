/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.sdk;

import junit.framework.TestCase;

import java.util.List;

/**
 * The deprecated {@code suggestHomePath()} (still abstract on 2025.3) and its replacement
 * {@code suggestHomePaths(Project)} must suggest the same folder, so SDK setup keeps its default
 * when the platform stops calling the deprecated one.
 */
public class MQL4SdkTypeHomePathTest extends TestCase {

    @SuppressWarnings("deprecation") // comparing against the deprecated override on purpose
    public void testBothHomePathSuggestionsAgree() {
        MQL4SdkType type = new MQL4SdkType();
        String home = type.suggestHomePath();
        assertNotNull(home);
        assertEquals(List.of(home), List.copyOf(type.suggestHomePaths(null)));
    }
}
