/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package fileicon;

import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.intellij.ui.LayeredIcon;
import com.limemojito.oss.mql.MQL4FileIconProvider;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.MQL5FileType;
import com.limemojito.oss.mql.MqlHeaderFileType;

import javax.swing.Icon;

/**
 * Icon-flash fix (see MQL4File.getFileType / MqlHeaderFileType / MQL4FileIconProvider): the FIRST
 * painted icon (the platform's DeferredIcon placeholder, taken from the FileType) must already equal
 * the final per-extension icon, so there is no wrong->right repaint, and the problem state is a badge
 * OVERLAY on that same base icon rather than a different (desaturated) base.
 */
public class MqlFileIconAndTypeTest extends BasePlatformTestCase {

    // ---- FileType-level icons (what the DeferredIcon placeholder uses) ----------------------

    public void testMq5FileTypeIconIsMql5NotMql4Banner() {
        assertSame("the .mq5 FileType icon must be the MQL5 icon", MQL4Icons.MQL5File, MQL5FileType.INSTANCE.getIcon());
        assertNotSame("must not be the MQL4 banner", MQL4Icons.File, MQL5FileType.INSTANCE.getIcon());
    }

    public void testMqhFileTypeIconIsHeaderIcon() {
        assertSame("the .mqh FileType icon must be the neutral header icon",
                MQL4Icons.HeaderFile, MqlHeaderFileType.INSTANCE.getIcon());
    }

    public void testMq4FileTypeIconIsMql4() {
        assertSame(MQL4Icons.File, MQL4FileType.INSTANCE.getIcon());
    }

    // ---- MQL4File.getFileType() now reflects the real per-extension type ---------------------

    public void testGetFileTypeReturnsMql5ForMq5() {
        PsiFile file = myFixture.configureByText("test.mq5", "int OnInit(){return 0;}\n");
        assertSame(MQL5FileType.INSTANCE, file.getFileType());
    }

    public void testGetFileTypeReturnsHeaderForMqh() {
        PsiFile file = myFixture.configureByText("test.mqh", "int helper(){return 0;}\n");
        assertSame(MqlHeaderFileType.INSTANCE, file.getFileType());
    }

    public void testGetFileTypeReturnsMql4ForMq4() {
        PsiFile file = myFixture.configureByText("test.mq4", "int OnInit(){return 0;}\n");
        assertSame(MQL4FileType.INSTANCE, file.getFileType());
    }

    // ---- IconProvider: no-problem case returns exactly the base FileType icon (no flash) -----

    public void testIconProviderReturnsBaseIconMatchingFileTypeIcon() {
        MQL4FileIconProvider provider = new MQL4FileIconProvider();

        PsiFile mq5 = myFixture.configureByText("a.mq5", "int OnInit(){return 0;}\n");
        assertSame("no-problem .mq5 icon must equal the MQL5 FileType icon (no flash)",
                MQL5FileType.INSTANCE.getIcon(), provider.getIcon(mq5, 0));

        PsiFile mqh = myFixture.configureByText("b.mqh", "int h(){return 0;}\n");
        assertSame("no-problem .mqh icon must equal the header FileType icon (no flash)",
                MqlHeaderFileType.INSTANCE.getIcon(), provider.getIcon(mqh, 0));

        PsiFile mq4 = myFixture.configureByText("c.mq4", "int OnInit(){return 0;}\n");
        assertSame("no-problem .mq4 icon must equal the MQL4 FileType icon (no flash)",
                MQL4FileType.INSTANCE.getIcon(), provider.getIcon(mq4, 0));
    }

    // ---- Problem state is a badge OVERLAY whose base equals the no-problem icon --------------

    public void testProblemIconIsLayeredOverSameBase() {
        assertBadgedBaseEquals(MQL4Icons.FileProblem, MQL4Icons.File);
        assertBadgedBaseEquals(MQL4Icons.MQL5FileProblem, MQL4Icons.MQL5File);
        assertBadgedBaseEquals(MQL4Icons.HeaderFileProblem, MQL4Icons.HeaderFile);
    }

    private static void assertBadgedBaseEquals(Icon problemIcon, Icon expectedBase) {
        assertTrue("problem icon must be a layered/badged icon", problemIcon instanceof LayeredIcon);
        LayeredIcon layered = (LayeredIcon) problemIcon;
        assertSame("the badge's base icon must equal the no-problem base icon (base never swaps)",
                expectedBase, layered.getIcon(0));
    }
}
