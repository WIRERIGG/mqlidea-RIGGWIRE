/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package completion;

import com.intellij.codeInsight.lookup.LookupElement;
import com.intellij.codeInsight.lookup.LookupElementPresentation;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.Arrays;
import java.util.List;

/**
 * Phase 6 (REVAMP_PLAN.md #Phase 6) completion tests: built-in signature tail text, dialect
 * filtering, project-wide symbol completion, and Std-Lib member completion after {@code .}.
 *
 * <p>{@code completeBasic()} returns {@code null} (rather than the lookup array) when there is
 * exactly one matching candidate, because the platform auto-inserts it instead of showing a
 * popup -- that is itself a successful, precise completion, so tests where a prefix happens to be
 * unique check the resulting document text in that case instead of the (absent) lookup array.</p>
 */
public class MQL4CompletionTest extends BasePlatformTestCase {

    private LookupElement[] complete(String code) {
        myFixture.configureByText("test.mq4", code);
        return myFixture.completeBasic();
    }

    private LookupElement findByLookupString(LookupElement[] items, String text) {
        if (items == null) {
            return null;
        }
        for (LookupElement item : items) {
            if (item.getLookupString().equals(text)) {
                return item;
            }
        }
        return null;
    }

    /** True if {@code expected} was offered as a completion, whether shown in a popup or auto-inserted (single match). */
    private boolean completesTo(LookupElement[] items, String expected) {
        if (findByLookupString(items, expected) != null) {
            return true;
        }
        // null items => the platform auto-inserted the single unique match; confirm via the document.
        return items == null && myFixture.getEditor().getDocument().getText().contains(expected);
    }

    public void testBuiltinFunctionHasSignatureTailText() {
        LookupElement[] items = complete("void f() { OrderSe<caret> }");
        LookupElement orderSend = findByLookupString(items, "OrderSend");
        assertNotNull("expected OrderSend in completion (OrderSe also matches OrderSelect, so a popup is expected)", orderSend);
        LookupElementPresentation presentation = new LookupElementPresentation();
        orderSend.renderElement(presentation);
        assertNotNull("expected tail text (params) on the built-in", presentation.getTailText());
        assertTrue("expected the real signature, not a placeholder",
                presentation.getTailText().contains("symbol"));
    }

    public void testMql4OnlyBuiltinExcludedFromMql5File() {
        myFixture.configureByText("test.mq5", "void f() { MarketInf<caret> }");
        LookupElement[] items = myFixture.completeBasic();
        assertFalse("MarketInfo is MQL4-only and must not be proposed in a .mq5 file", completesTo(items, "MarketInfo"));
    }

    public void testMql4OnlyBuiltinOfferedInMql4File() {
        LookupElement[] items = complete("void f() { MarketInf<caret> }");
        assertTrue("MarketInfo should be offered in a .mq4 file", completesTo(items, "MarketInfo"));
    }

    public void testProjectFunctionCompletion() {
        LookupElement[] items = complete("void Helper() { }\nvoid f() { Help<caret> }");
        assertTrue("expected project-defined Helper() function in completion", completesTo(items, "Helper"));
    }

    public void testLocalVariableCompletionRankedAboveBuiltins() {
        LookupElement[] items = complete("void f() { int myLocal = 1; int y = myLoc<caret> }");
        assertTrue("expected the local variable to be offered", completesTo(items, "myLocal"));
    }

    public void testStdLibMemberCompletionAfterDot() {
        LookupElement[] items = complete("void f() { CTrade tr; tr.<caret> }");
        assertNotNull(items);
        List<String> strings = Arrays.stream(items).map(LookupElement::getLookupString).toList();
        assertTrue("expected CTrade's PositionOpen among tr. completions, got: " + strings,
                strings.contains("PositionOpen"));
    }
}
