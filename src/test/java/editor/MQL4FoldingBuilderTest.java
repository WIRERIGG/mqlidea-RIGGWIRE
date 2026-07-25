/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.lang.folding.FoldingDescriptor;
import com.intellij.openapi.editor.Document;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MQL4FoldingBuilder;

import java.util.Arrays;

/**
 * Covers the two additions to {@link MQL4FoldingBuilder} in Phase 2b: {@code #region}/{@code
 * #endregion} folding and collapsing runs of {@code >= 2} consecutive {@code #include}
 * directives. Neither construct is a first-class composite PSI element (see the folding builder's
 * javadoc), so these tests exercise {@code buildFoldRegions} directly rather than using PSI
 * navigation to locate the folded elements.
 */
public class MQL4FoldingBuilderTest extends BasePlatformTestCase {

    private FoldingDescriptor[] fold(String code) {
        PsiFile file = myFixture.configureByText("test.mq4", code);
        Document document = myFixture.getEditor().getDocument();
        return new MQL4FoldingBuilder().buildFoldRegions(file.getNode(), document);
    }

    public void testRegionFoldsWithName() {
        String code = "#region My Region\nvoid f() {}\n#endregion\n";
        FoldingDescriptor[] descriptors = fold(code);
        FoldingDescriptor region = Arrays.stream(descriptors)
                .filter(d -> "My Region".equals(d.getPlaceholderText()))
                .findFirst()
                .orElse(null);
        assertNotNull("Expected a #region...#endregion fold named 'My Region':\n" + Arrays.toString(descriptors), region);
        assertEquals(0, region.getRange().getStartOffset());
        assertEquals(code.indexOf("#endregion") + "#endregion".length(), region.getRange().getEndOffset());
    }

    public void testRegionFoldsWithoutName() {
        String code = "#region\nint x = 1;\n#endregion\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean found = Arrays.stream(descriptors).anyMatch(d -> "region".equals(d.getPlaceholderText()));
        assertTrue("Expected the unnamed region to fall back to the 'region' placeholder", found);
    }

    public void testNestedRegionsBothFold() {
        String code = "#region Outer\nvoid a(){}\n#region Inner\nvoid b(){}\n#endregion\nvoid c(){}\n#endregion\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean outer = Arrays.stream(descriptors).anyMatch(d -> "Outer".equals(d.getPlaceholderText()));
        boolean inner = Arrays.stream(descriptors).anyMatch(d -> "Inner".equals(d.getPlaceholderText()));
        assertTrue("Expected the outer region to fold", outer);
        assertTrue("Expected the inner region to fold", inner);
    }

    public void testUnmatchedEndregionIsSkippedGracefully() {
        // No opening #region -- must not throw and must not produce a region fold.
        String code = "#endregion\nvoid f() {}\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean anyRegion = Arrays.stream(descriptors)
                .anyMatch(d -> d instanceof com.limemojito.oss.mql.editor.folding.RegionFoldingDescriptor);
        assertFalse("An unmatched #endregion must not produce a fold", anyRegion);
    }

    public void testUnmatchedTrailingRegionIsSkippedGracefully() {
        // Opening #region with no closing #endregion anywhere in the file.
        String code = "#region Never Closed\nvoid f() {}\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean anyRegion = Arrays.stream(descriptors)
                .anyMatch(d -> d instanceof com.limemojito.oss.mql.editor.folding.RegionFoldingDescriptor);
        assertFalse("An unmatched trailing #region must not produce a fold", anyRegion);
    }

    public void testThreeConsecutiveIncludesFoldTogether() {
        String code = "#include <A.mqh>\n#include <B.mqh>\n#include <C.mqh>\nvoid f() {}\n";
        FoldingDescriptor[] descriptors = fold(code);
        FoldingDescriptor includeFold = Arrays.stream(descriptors)
                .filter(d -> "#include (3)".equals(d.getPlaceholderText()))
                .findFirst()
                .orElse(null);
        assertNotNull("Expected 3 consecutive #include directives to collapse into one fold:\n" + Arrays.toString(descriptors), includeFold);
        assertEquals(0, includeFold.getRange().getStartOffset());
        int lastIncludeEnd = code.indexOf("#include <C.mqh>") + "#include <C.mqh>".length();
        assertEquals(lastIncludeEnd, includeFold.getRange().getEndOffset());
    }

    public void testSingleIncludeDoesNotFold() {
        String code = "#include <A.mqh>\nvoid f() {}\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean anyIncludeFold = Arrays.stream(descriptors)
                .anyMatch(d -> d instanceof com.limemojito.oss.mql.editor.folding.IncludeRunFoldingDescriptor);
        assertFalse("A single #include must not fold as a run", anyIncludeFold);
    }

    public void testTwoIncludesSeparatedByCodeDoNotMerge() {
        String code = "#include <A.mqh>\nvoid f() {}\n#include <B.mqh>\n";
        FoldingDescriptor[] descriptors = fold(code);
        boolean anyIncludeFold = Arrays.stream(descriptors)
                .anyMatch(d -> d instanceof com.limemojito.oss.mql.editor.folding.IncludeRunFoldingDescriptor);
        assertFalse("Non-consecutive #include directives must not merge into a run fold", anyIncludeFold);
    }
}
