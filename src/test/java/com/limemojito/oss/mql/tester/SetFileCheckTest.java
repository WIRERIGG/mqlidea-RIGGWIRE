/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.tester;

import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.List;
import java.util.Map;

public class SetFileCheckTest extends BasePlatformTestCase {

    public void testEaFromMetaTradersHeaderOrTheFileName() {
        List<String> eas = List.of("RIGGWIRE_FINAL", "RIGGWIRE", "Capture");
        assertEquals("Capture", SetFileCheck.eaFor("whatever.set",
                "; this file contains input parameters for testing/optimizing Capture expert advisor\n", eas));
        assertNull("a header naming an EA the project lacks", SetFileCheck.eaFor("RIGGWIRE_FINAL.set",
                "; this file contains input parameters for testing/optimizing Other expert advisor\n", eas));
        assertEquals("RIGGWIRE_FINAL", SetFileCheck.eaFor("RIGGWIRE_FINAL_2023H1.set", "", eas));
        assertEquals("RIGGWIRE", SetFileCheck.eaFor("riggwire.set", "", eas));
        assertNull("RIGGWIRE_FINALIST is not RIGGWIRE_FINAL", SetFileCheck.eaFor("RIGGWIRE_FINALIST.set", "", List.of("RIGGWIRE_FINAL")));
    }

    public void testUnknownNamesAndBadValues() {
        Map<String, String> inputs = Map.of("TC_ExtremeLevel", "int", "EntryUsesTC", "bool", "Risk", "double", "Note", "string");
        SetFileCheck.Result r = SetFileCheck.check("""
                TC_ExtremeLevel=75||45||5||95||N
                EntryUsesTC=yes
                Risk=0.5
                Note=anything goes
                TC_ExtremLevel=80
                """, inputs);
        assertEquals(List.of("TC_ExtremLevel"), r.unknown());
        assertEquals(List.of("EntryUsesTC=yes (bool: not true or false)"), r.badValues());
        assertTrue(SetFileCheck.check("Risk=1e-3\nEntryUsesTC=1\n", inputs).isEmpty());
    }

    public void testBannerFindsTheEaAndCountsInputsFromIncludes() {
        myFixture.addFileToProject("Clock.mqh", "input group \"Clock\"\ninput int ClockOffset = 2;\n");
        myFixture.addFileToProject("Bot.mq5", "#include \"Clock.mqh\"\ninput double Risk = 1.0;\nsinput string Tag = \"x\";\nvoid OnTick() {}\n");
        VirtualFile set = myFixture.addFileToProject("Bot_test.set", "Risk=0.5\nClockOffset=3\nTag=t\nRsik=2\n").getVirtualFile();
        SetFileNotificationProvider.Finding f = SetFileNotificationProvider.find(getProject(), set);
        assertNotNull(f);
        assertEquals(List.of("Rsik"), f.result().unknown());
        assertTrue(f.text(), f.text().startsWith("1 input isn't declared by Bot.mq5, so MetaTrader ignores it and tests the default: Rsik."));
    }

    public void testNoBannerWhenCleanOrUnsure() {
        myFixture.addFileToProject("Bot.mq5", "input double Risk = 1.0;\nvoid OnTick() {}\n");
        assertNull(SetFileNotificationProvider.find(getProject(), myFixture.addFileToProject("Bot.set", "Risk=0.5\n").getVirtualFile()));
        myFixture.addFileToProject("Multi.mq5", "input int a = 1, b = 2;\nvoid OnTick() {}\n");
        assertNull("a multi-input line makes the input list unknown",
                SetFileNotificationProvider.find(getProject(), myFixture.addFileToProject("Multi.set", "c=1\n").getVirtualFile()));
        myFixture.addFileToProject("Gap.mq5", "#include \"Missing.mqh\"\nvoid OnTick() {}\n");
        assertNull("an unresolved include may declare inputs",
                SetFileNotificationProvider.find(getProject(), myFixture.addFileToProject("Gap.set", "c=1\n").getVirtualFile()));
    }

    public void testSeveralCopiesOfTheEaPickTheNearestAndATieStaysSilent() {
        myFixture.addFileToProject("main/Bot.mq5", "input double Risk = 1.0;\nvoid OnTick() {}\n");
        myFixture.addFileToProject("worktrees/seed/Bot.mq5", "input double Risk = 1.0;\ninput bool Extra = true;\nvoid OnTick() {}\n");
        SetFileNotificationProvider.Finding f = SetFileNotificationProvider.find(getProject(),
                myFixture.addFileToProject("main/Bot.set", "Risk=1\nExtra=false\n").getVirtualFile());
        assertNotNull("main/Bot.mq5 is nearest and lacks Extra", f);
        assertEquals("main", f.ea().getParent().getName());
        assertNull("the seed copy declares Extra", SetFileNotificationProvider.find(getProject(),
                myFixture.addFileToProject("worktrees/seed/Bot.set", "Risk=1\nExtra=false\n").getVirtualFile()));
        assertNull("equally near both: unsure", SetFileNotificationProvider.find(getProject(),
                myFixture.addFileToProject("Bot.set", "Risk=1\nExtra=false\n").getVirtualFile()));
    }
}
