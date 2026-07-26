/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig;

import junit.framework.TestCase;

/**
 * Locks the Run-configuration compile-log naming against the {@code name.replace(".mq4", ".log")}
 * bug: for an {@code .mq5}/{@code .mqh} source there is no {@code .mq4} substring, so the old code
 * left the name unchanged and then tried to read the SOURCE file as the log — the run console showed
 * nothing (or garbage) for every MQL5 compile. Deriving from the base name fixes all extensions.
 */
public class CompilerLogNameTest extends TestCase {

    public void testMql5SourceGetsLogExtension() {
        assertEquals("Expert.log", MQL4CompilerCommandLineState.deriveLogFileName("Expert.mq5"));
    }

    public void testMql4SourceGetsLogExtension() {
        assertEquals("Expert.log", MQL4CompilerCommandLineState.deriveLogFileName("Expert.mq4"));
    }

    public void testHeaderSourceGetsLogExtension() {
        assertEquals("Helpers.log", MQL4CompilerCommandLineState.deriveLogFileName("Helpers.mqh"));
    }

    public void testDottedBaseNameKeepsAllButLastSegment() {
        assertEquals("My.Expert.log", MQL4CompilerCommandLineState.deriveLogFileName("My.Expert.mq5"));
    }

    public void testExtensionlessNameStillGetsLog() {
        assertEquals("noext.log", MQL4CompilerCommandLineState.deriveLogFileName("noext"));
    }
}
