/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

public class CommentsTest extends MQL4ParserTestBase {

    public CommentsTest() {
        super("parser/comments");
    }

    public void testLineComments() {
        doTest();
    }

    public void testBlockComments() {
        doTest();
    }

}
