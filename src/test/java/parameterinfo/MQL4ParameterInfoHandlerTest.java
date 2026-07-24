/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parameterinfo;

import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.intellij.testFramework.utils.parameterInfo.MockCreateParameterInfoContext;
import com.intellij.testFramework.utils.parameterInfo.MockParameterInfoUIContext;
import com.intellij.testFramework.utils.parameterInfo.MockUpdateParameterInfoContext;
import com.limemojito.oss.mql.editor.parameterinfo.MQL4ParameterInfoHandler;

/**
 * Phase 6 (REVAMP_PLAN.md #Phase 6) signature-help tests, using the platform's own
 * {@code Mock*ParameterInfoContext} test doubles (same technique other JetBrains language
 * plugins use to test {@link com.intellij.lang.parameterInfo.ParameterInfoHandler} without a real
 * editor popup).
 */
public class MQL4ParameterInfoHandlerTest extends BasePlatformTestCase {

    private final MQL4ParameterInfoHandler handler = new MQL4ParameterInfoHandler();

    private PsiElement configureAndFindCallArgs(String code, String marker) {
        PsiFile file = myFixture.configureByText("test.mq4", code);
        int offset = code.indexOf(marker);
        assertTrue("marker not found: " + marker, offset >= 0);
        myFixture.getEditor().getCaretModel().moveToOffset(offset);
        MockCreateParameterInfoContext context = new MockCreateParameterInfoContext(myFixture.getEditor(), file);
        PsiElement callArgs = handler.findElementForParameterInfo(context);
        assertNotNull("expected a call argument list at the caret", callArgs);
        assertTrue("expected at least one signature item", context.getItemsToShow().length > 0);
        return callArgs;
    }

    public void testProjectFunctionSignature() {
        String code = "void Helper(int a, string b) { }\nvoid f() { Helper(1, ); }";
        int callOffset = code.indexOf("Helper(1, ") + "Helper(1, ".length();
        PsiFile file = myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(callOffset);
        MockCreateParameterInfoContext createContext = new MockCreateParameterInfoContext(myFixture.getEditor(), file);
        PsiElement callArgs = handler.findElementForParameterInfo(createContext);
        assertNotNull(callArgs);
        Object[] items = createContext.getItemsToShow();
        assertEquals(1, items.length);

        MockUpdateParameterInfoContext updateContext = new MockUpdateParameterInfoContext(myFixture.getEditor(), file, items);
        handler.updateParameterInfo(callArgs, updateContext);
        assertEquals("caret sits in the second argument (index 1)", 1, updateContext.getCurrentParameter());

        MockParameterInfoUIContext<PsiElement> uiContext = new MockParameterInfoUIContext<>(callArgs);
        uiContext.setCurrentParameterIndex(updateContext.getCurrentParameter());
        handler.updateUI(items[0], uiContext);
        assertTrue("expected both parameters rendered: " + uiContext.getText(), uiContext.getText().contains("int a") && uiContext.getText().contains("string b"));
    }

    public void testBuiltinFunctionSignature() {
        String code = "void f() { OrderSend(Symbol(), OP_BUY, 1, Ask, 3, 0, 0); }";
        int callOffset = code.indexOf("OrderSend(") + "OrderSend(".length();
        PsiFile file = myFixture.configureByText("test.mq4", code);
        myFixture.getEditor().getCaretModel().moveToOffset(callOffset);
        MockCreateParameterInfoContext context = new MockCreateParameterInfoContext(myFixture.getEditor(), file);
        PsiElement callArgs = handler.findElementForParameterInfo(context);
        assertNotNull("expected OrderSend's built-in signature to be found", callArgs);
        Object[] items = context.getItemsToShow();
        assertEquals(1, items.length);

        MockParameterInfoUIContext<PsiElement> uiContext = new MockParameterInfoUIContext<>(callArgs);
        handler.updateUI(items[0], uiContext);
        assertTrue("expected the full built-in signature text: " + uiContext.getText(), uiContext.getText().contains("symbol"));
    }
}
