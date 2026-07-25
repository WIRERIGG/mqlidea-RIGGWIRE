/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package runconfig;

import com.intellij.testFramework.LightVirtualFile;
import com.limemojito.oss.mql.runconfig.ui.MQL4CompilerRunnerEditor;
import junit.framework.TestCase;

/**
 * P3: the run-config file chooser must accept ANY MQL program file. The old descriptor was built
 * from a single MQL4FileType, which filtered out .mq5 files (whose FileType is MQL5FileType) so an
 * MQL5 program could not be selected. The shared filter now accepts mq4/mql4/mq5/mql5 and rejects
 * .mqh headers (not compilable standalone).
 */
public class MQL4CompilerRunnerEditorFilterTest extends TestCase {

    public void testFilterAcceptsMql5Program() {
        assertTrue(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("EA.mq5")));
    }

    public void testFilterAcceptsAllProgramDialects() {
        assertTrue(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("a.mq4")));
        assertTrue(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("b.mql4")));
        assertTrue(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("c.mq5")));
        assertTrue(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("d.mql5")));
    }

    public void testFilterRejectsHeaderAndOthers() {
        assertFalse("headers cannot be built standalone",
                MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("Lib.mqh")));
        assertFalse(MQL4CompilerRunnerEditor.acceptsProgramFile(new LightVirtualFile("notes.txt")));
        assertFalse(MQL4CompilerRunnerEditor.acceptsProgramFile(null));
    }
}
