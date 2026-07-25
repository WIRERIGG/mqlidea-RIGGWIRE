/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package inspection;

import com.intellij.codeInsight.intention.IntentionAction;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.inspection.DeleteWithoutNullCheckInspection;
import com.limemojito.oss.mql.inspection.UncheckedCopyRatesInspection;
import com.limemojito.oss.mql.inspection.UncheckedHandleInspection;

import java.util.List;

/**
 * Phase 4b: Alt-Enter intention preview for the three document-text-edit quick fixes
 * (WrapCallInFailureCheckFix, CheckHandleAfterCreationFix, NullifyAfterDeleteFix). These mutate the
 * document by text insertion rather than a pure PSI edit of the highlighted range, so each overrides
 * {@code generatePreview} to render an explicit diff; without that the preview would be empty. The
 * test drives the real preview pipeline via {@link
 * com.intellij.testFramework.fixtures.CodeInsightTestFixture#getIntentionPreviewText(IntentionAction)}
 * and asserts the rendered new-text contains the guard the fix inserts.
 */
public class QuickFixPreviewTest extends BasePlatformTestCase {

    private String previewFor(LocalInspectionTool inspection, String fileName, String code, String fixTextNeedle) {
        myFixture.configureByText(fileName, code);
        myFixture.enableInspections(inspection);
        List<IntentionAction> fixes = myFixture.getAllQuickFixes();
        IntentionAction target = null;
        for (IntentionAction action : fixes) {
            if (action.getText().contains(fixTextNeedle)) {
                target = action;
                break;
            }
        }
        assertNotNull("no quick fix whose text contains '" + fixTextNeedle + "'; available: " + fixes, target);
        return myFixture.getIntentionPreviewText(target);
    }

    public void testWrapCopyRatesFailureCheckPreview() {
        String preview = previewFor(new UncheckedCopyRatesInspection(), "test.mq5",
                "void foo() { double buf[]; CopyBuffer(handle, 0, 0, 10, buf); }",
                "failure check");
        assertNotNull("preview must not be empty", preview);
        assertTrue("preview should show the inserted '< 0' failure check:\n" + preview,
                preview.contains("< 0"));
        assertTrue("preview should reference the wrapped call:\n" + preview,
                preview.contains("CopyBuffer"));
    }

    public void testCheckHandleAfterCreationPreview() {
        String preview = previewFor(new UncheckedHandleInspection(), "test.mq5",
                "int handle;\n"
                        + "int OnInit() { handle = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE); return 0; }",
                "INVALID_HANDLE");
        assertNotNull("preview must not be empty", preview);
        assertTrue("preview should show the inserted INVALID_HANDLE guard:\n" + preview,
                preview.contains("INVALID_HANDLE"));
    }

    public void testNullifyAfterDeletePreview() {
        String preview = previewFor(new DeleteWithoutNullCheckInspection(), "test.mq4",
                "void foo() { delete ptr; }",
                "= NULL");
        assertNotNull("preview must not be empty", preview);
        assertTrue("preview should show the inserted 'ptr = NULL;' assignment:\n" + preview,
                preview.contains("= NULL"));
    }
}
