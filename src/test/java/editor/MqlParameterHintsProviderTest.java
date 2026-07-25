/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.hints.InlayInfo;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MqlParameterHintsProvider;
import com.limemojito.oss.mql.editor.parameterinfo.MqlCallSignatures;

import java.util.List;

/**
 * Phase 3a parameter-name inlay hints: a resolved call gets an {@link InlayInfo} at each positional
 * argument carrying its parameter name; unknown callees and arguments that already read as the
 * parameter name get none.
 */
public class MqlParameterHintsProviderTest extends BasePlatformTestCase {

    private final MqlParameterHintsProvider provider = new MqlParameterHintsProvider();

    /**
     * The {@code (...)} args block of a call to {@code callee}. Scans every {@code callee(}
     * occurrence and walks up, skipping a same-named function declaration (whose parameter list is
     * a FUNCTION_ARGS_LIST, not a call BRACKETS_BLOCK).
     */
    private PsiElement callArgsBlock(PsiFile file, String callee) {
        String text = file.getText();
        String needle = callee + "(";
        for (int from = text.indexOf(needle); from >= 0; from = text.indexOf(needle, from + 1)) {
            int parenOffset = from + callee.length();
            PsiElement candidate = file.findElementAt(parenOffset);
            while (candidate != null) {
                if (MqlCallSignatures.isCallArgsBlock(candidate) && callee.equals(MqlCallSignatures.callName(candidate))) {
                    return candidate;
                }
                candidate = candidate.getParent();
            }
        }
        fail("no call args block found for " + callee);
        return null;
    }

    private static InlayInfo hintWithText(List<InlayInfo> hints, String text) {
        for (InlayInfo h : hints) {
            if (text.equals(h.getText())) {
                return h;
            }
        }
        return null;
    }

    public void testBuiltinCallGetsParameterNameHints() {
        String code = "void f() { iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE, 0); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "iMA");

        List<InlayInfo> hints = provider.getParameterHints(block);
        // iMA(string symbol, int timeframe, int ma_period, int ma_shift, int ma_method, int applied_price, int shift)
        assertEquals("one hint per positional argument", 7, hints.size());

        // first hint labels the first argument with the parameter name, at that argument's offset
        assertEquals("symbol", hints.get(0).getText());
        assertEquals(code.indexOf("_Symbol"), hints.get(0).getOffset());

        InlayInfo period = hintWithText(hints, "ma_period");
        assertNotNull("expected an ma_period hint", period);
        assertEquals(code.indexOf("14"), period.getOffset());

        assertNotNull(hintWithText(hints, "timeframe"));
        assertNotNull(hintWithText(hints, "applied_price"));
    }

    public void testUnknownCalleeGetsNoHints() {
        String code = "void f() { NoSuchFunction(1, 2, 3); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "NoSuchFunction");

        assertTrue("unresolved callee must not be hinted", provider.getParameterHints(block).isEmpty());
    }

    public void testArgumentEqualToParameterNameIsSuppressed() {
        // Helper(int a, int b): arg 0 text "a" == param name "a" -> suppressed; arg 1 "2" -> "b".
        String code = "void Helper(int a, int b) { }\nvoid f() { Helper(a, 2); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "Helper");

        List<InlayInfo> hints = provider.getParameterHints(block);
        assertNull("hint suppressed when arg text equals the parameter name", hintWithText(hints, "a"));
        InlayInfo b = hintWithText(hints, "b");
        assertNotNull("second argument still hinted", b);
        assertEquals(code.indexOf("2", code.indexOf("Helper(")), b.getOffset());
    }

    public void testNonCallElementGetsNoHints() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() { int x = 1; }");
        assertTrue(provider.getParameterHints(file).isEmpty());
    }
}
