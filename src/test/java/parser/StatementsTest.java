/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package parser;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.junit.Assert;
import com.limemojito.oss.mql.psi.MQL4Elements;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

/**
 * Ensures that {} code blocks are parsed into real statement elements (if/for/while/do/switch/
 * return/expression/var-declaration) and that unrecognized content degrades gracefully to the
 * old token-by-token fallback without producing parse errors.
 */
public class StatementsTest extends MQL4ParserTestBase implements MQL4Elements {

    public StatementsTest() {
        super("parser/statements");
    }

    public void testControlFlowStatementsProduceRealTree() throws IOException {
        PsiFile file = parseWithoutErrors("/ControlFlow.mq4");
        Map<IElementType, Integer> counts = countElementTypes(file);

        assertContains(counts, IF_STATEMENT);
        assertContains(counts, FOR_STATEMENT);
        assertContains(counts, WHILE_STATEMENT);
        assertContains(counts, DO_STATEMENT);
        assertContains(counts, SWITCH_STATEMENT);
        assertContains(counts, RETURN_STATEMENT);
        assertContains(counts, EXPRESSION_STATEMENT);
        assertContains(counts, VAR_DECLARATION_STATEMENT);
        assertContains(counts, SINGLE_WORD_STATEMENT);
        assertContains(counts, EMPTY_STATEMENT);
        assertContains(counts, BRACKETS_BLOCK); // function bodies / nested blocks keep their type

        // if / else-if chain + guard-if in Ratio(): at least 3 if statements
        Assert.assertTrue("Expected at least 3 IF_STATEMENT elements", counts.get(IF_STATEMENT) >= 3);
        // do {} while + do-single-statement-while
        Assert.assertTrue("Expected 2 DO_STATEMENT elements", counts.get(DO_STATEMENT) >= 2);
        // return; + return sum; + 2 returns in Ratio()
        Assert.assertTrue("Expected at least 4 RETURN_STATEMENT elements", counts.get(RETURN_STATEMENT) >= 4);
    }

    public void testWeirdStatementsFallBackWithoutErrors() throws IOException {
        PsiFile file = parseWithoutErrors("/Robustness.mq4");
        Map<IElementType, Integer> counts = countElementTypes(file);

        // both functions must survive the weird body of the first one
        int functions = counts.getOrDefault(FUNCTION, 0);
        Assert.assertEquals("Both function definitions must be parsed", 2, functions);
        // the valid function after the weird one parses a real return statement
        assertContains(counts, RETURN_STATEMENT);
        // the tolerant switch without a body must still be recognized
        assertContains(counts, SWITCH_STATEMENT);
    }

    @NotNull
    private PsiFile parseWithoutErrors(@NotNull String subPath) throws IOException {
        String text = loadFile(subPath);
        PsiFile file = createPsiFile("any-name", text);
        ensureParsed(file);
        ensureCorrectReparse(file);
        PsiErrorElement error = ParserTestUtils.findErrorElement(file);
        Assert.assertNull("File has errors: " + subPath + ", error: " + error, error);
        return file;
    }

    @NotNull
    private static Map<IElementType, Integer> countElementTypes(@NotNull PsiFile file) {
        Map<IElementType, Integer> counts = new HashMap<>();
        collect(file.getNode(), counts);
        return counts;
    }

    private static void collect(ASTNode node, Map<IElementType, Integer> counts) {
        counts.merge(node.getElementType(), 1, Integer::sum);
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            collect(child, counts);
        }
    }

    private static void assertContains(Map<IElementType, Integer> counts, IElementType type) {
        Assert.assertTrue("Expected element type in tree: " + type, counts.containsKey(type));
    }
}
