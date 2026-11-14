/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.hints.declarative.CollapseState;
import com.intellij.codeInsight.hints.declarative.CollapsiblePresentationTreeBuilder;
import com.intellij.codeInsight.hints.declarative.HintFormat;
import com.intellij.codeInsight.hints.declarative.InlayActionData;
import com.intellij.codeInsight.hints.declarative.InlayHintsProviderExtensionBean;
import com.intellij.codeInsight.hints.declarative.InlayPayload;
import com.intellij.codeInsight.hints.declarative.InlayPosition;
import com.intellij.codeInsight.hints.declarative.InlayTreeSink;
import com.intellij.codeInsight.hints.declarative.InlineInlayPosition;
import com.intellij.codeInsight.hints.declarative.PresentationTreeBuilder;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MqlParameterHintsProvider;
import com.limemojito.oss.mql.editor.MqlParameterHintsProvider.Hint;
import com.limemojito.oss.mql.editor.parameterinfo.MqlCallSignatures;

import java.util.ArrayList;
import java.util.List;
import kotlin.Unit;
import kotlin.jvm.functions.Function0;
import kotlin.jvm.functions.Function1;

/**
 * Phase 3a parameter-name inlay hints: a resolved call gets a {@link Hint} at each positional
 * argument carrying its parameter name; unknown callees and arguments that already read as the
 * parameter name get none.
 */
public class MqlParameterHintsProviderTest extends BasePlatformTestCase {

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

    private static Hint hintWithText(List<Hint> hints, String text) {
        for (Hint h : hints) {
            if (text.equals(h.name())) {
                return h;
            }
        }
        return null;
    }

    public void testBuiltinCallGetsParameterNameHints() {
        String code = "void f() { iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE, 0); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "iMA");

        List<Hint> hints = MqlParameterHintsProvider.computeHints(block);
        // iMA(string symbol, int timeframe, int ma_period, int ma_shift, int ma_method, int applied_price, int shift)
        assertEquals("one hint per positional argument", 7, hints.size());

        // first hint labels the first argument with the parameter name, at that argument's offset
        assertEquals("symbol", hints.get(0).name());
        assertEquals(code.indexOf("_Symbol"), hints.get(0).offset());

        Hint period = hintWithText(hints, "ma_period");
        assertNotNull("expected an ma_period hint", period);
        assertEquals(code.indexOf("14"), period.offset());

        assertNotNull(hintWithText(hints, "timeframe"));
        assertNotNull(hintWithText(hints, "applied_price"));
    }

    public void testUnknownCalleeGetsNoHints() {
        String code = "void f() { NoSuchFunction(1, 2, 3); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "NoSuchFunction");

        assertTrue("unresolved callee must not be hinted", MqlParameterHintsProvider.computeHints(block).isEmpty());
    }

    public void testArgumentEqualToParameterNameIsSuppressed() {
        // Helper(int a, int b): arg 0 text "a" == param name "a" -> suppressed; arg 1 "2" -> "b".
        String code = "void Helper(int a, int b) { }\nvoid f() { Helper(a, 2); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "Helper");

        List<Hint> hints = MqlParameterHintsProvider.computeHints(block);
        assertNull("hint suppressed when arg text equals the parameter name", hintWithText(hints, "a"));
        Hint b = hintWithText(hints, "b");
        assertNotNull("second argument still hinted", b);
        assertEquals(code.indexOf("2", code.indexOf("Helper(")), b.offset());
    }

    public void testNonCallElementGetsNoHints() {
        PsiFile file = myFixture.configureByText("test.mq4", "void f() { int x = 1; }");
        assertTrue(MqlParameterHintsProvider.computeHints(file).isEmpty());
    }

    public void testVariadicLoggingCallGetsNoHints() {
        String code = "void f() { PrintFormat(\"%d %d\", 1, 2); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "PrintFormat");

        assertTrue("variadic logging calls are never hinted", MqlParameterHintsProvider.computeHints(block).isEmpty());
    }

    /** The collector renders each hint as an inline {@code name:} text inlay at the argument offset. */
    public void testCollectorRendersNameColonAtArgumentOffset() {
        String code = "void Helper(int a, int b) { }\nvoid f() { Helper(1, 2); }";
        PsiFile file = myFixture.configureByText("test.mq4", code);
        PsiElement block = callArgsBlock(file, "Helper");

        RecordingSink sink = new RecordingSink();
        MqlParameterHintsProvider.addHints(block, sink);

        int call = code.indexOf("Helper(1");
        assertEquals(List.of("a:@" + code.indexOf("1", call), "b:@" + code.indexOf("2", call)), sink.inlays);
    }

    /** Registered under the declarative EP for MQL4, enabled by default, in the parameter-names group. */
    public void testRegisteredAsDeclarativeParameterNamesProvider() {
        InlayHintsProviderExtensionBean bean = InlayHintsProviderExtensionBean.Companion.getEP().getExtensionList().stream()
                .filter(b -> MqlParameterHintsProvider.class.getName().equals(b.getImplementationClass()))
                .findFirst().orElse(null);
        assertNotNull("provider must be registered as codeInsight.declarativeInlayProvider", bean);
        assertEquals("MQL4", bean.getLanguage());
        assertTrue(bean.isEnabledByDefault());
        assertEquals("PARAMETERS_GROUP", bean.group.name());
        assertEquals("Parameter names", bean.getProviderName());
    }

    /** Records each inlay as {@code text@offset}. */
    private static final class RecordingSink implements InlayTreeSink {
        final List<String> inlays = new ArrayList<>();

        @Override
        public void addPresentation(InlayPosition position, List<InlayPayload> payloads, String tooltip,
                                    HintFormat hintFormat, Function1<? super PresentationTreeBuilder, Unit> builder) {
            StringBuilder text = new StringBuilder();
            builder.invoke(new TextOnlyBuilder(text));
            inlays.add(text + "@" + ((InlineInlayPosition) position).getOffset());
        }

        @Override
        public void whenOptionEnabled(String optionId, Function0<Unit> block) {
            block.invoke();
        }
    }

    /** Collects plain text; the provider only ever emits text nodes. */
    private record TextOnlyBuilder(StringBuilder out) implements PresentationTreeBuilder {
        @Override
        public void text(String text, InlayActionData actionData) {
            out.append(text);
        }

        @Override
        public void list(Function1<? super PresentationTreeBuilder, Unit> builder) {
            builder.invoke(this);
        }

        @Override
        public void collapsibleList(CollapseState state, Function1<? super CollapsiblePresentationTreeBuilder, Unit> expanded,
                                    Function1<? super CollapsiblePresentationTreeBuilder, Unit> collapsed) {
            fail("unexpected collapsible list");
        }

        @Override
        public void clickHandlerScope(InlayActionData actionData, Function1<? super PresentationTreeBuilder, Unit> builder) {
            builder.invoke(this);
        }
    }
}
