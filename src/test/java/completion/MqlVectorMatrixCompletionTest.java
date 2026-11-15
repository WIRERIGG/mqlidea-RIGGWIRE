/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package completion;

import com.intellij.testFramework.fixtures.BasePlatformTestCase;

import java.util.List;

/** T-5: members of MQL5's vector/matrix/complex types complete, in MQL5 files only. */
public class MqlVectorMatrixCompletionTest extends BasePlatformTestCase {

    private List<String> complete(String fileName, String code) {
        myFixture.configureByText(fileName, code);
        myFixture.completeBasic();
        List<String> items = myFixture.getLookupElementStrings();
        return items == null ? List.of() : items;
    }

    public void testVectorInstanceMethods() {
        List<String> items = complete("test.mq5", "void OnStart() { vector v = {1, 2, 3}; v.<caret> }");
        assertTrue(items.toString(), items.containsAll(List.of("Sum", "Mean", "ArgMax", "CopyRates", "Size")));
        assertFalse("matrix-only method offered on a vector", items.contains("Transpose"));
    }

    public void testMatrixFromConstructorForm() {
        List<String> items = complete("test.mq5", "void OnStart() { matrixf m(2, 2); m.<caret> }");
        assertTrue(items.toString(), items.containsAll(List.of("Transpose", "Inv", "Det", "Rows", "Cols")));
    }

    public void testStaticConstructors() {
        assertEquals(List.of("Eye", "Full", "Identity", "Ones", "Random", "Tri", "Zeros"),
                complete("test.mq5", "void OnStart() { matrix m = matrix::<caret> }").stream().sorted().toList());
        assertFalse("Eye isn't a vector constructor",
                complete("test.mq5", "void OnStart() { vector v = vector::<caret> }").contains("Eye"));
    }

    public void testComplexFields() {
        assertTrue(complete("test.mq5", "void OnStart() { complex z = {1, 2}; z.<caret> }").containsAll(List.of("real", "imag")));
    }

    public void testNotOfferedInMql4() {
        assertFalse(complete("test.mq4", "void OnStart() { vector v; v.<caret> }").contains("Sum"));
    }
}
