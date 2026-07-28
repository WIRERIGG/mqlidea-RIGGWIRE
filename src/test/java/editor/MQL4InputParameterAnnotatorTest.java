/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.editor.MQL4Annotator;

import java.util.List;
import java.util.stream.Collectors;

/**
 * L2 regression for {@link MQL4Annotator#annotate}: an input declaration's declarator gets the
 * input-parameter highlight, and a non-input declaration does not.
 *
 * <p>The fix changed {@code annotateInputParameter} from {@code findChildByType(VAR_DEFINITION)}
 * (first declarator only) to a loop over EVERY {@code VAR_DEFINITION} child, so any declarator the
 * parser puts in a {@code VAR_DEFINITION_LIST} is annotated. NOTE: the literal multi-declarator case
 * {@code input int a, b, c;} cannot be asserted here because the CURRENT parser never builds multiple
 * {@code VAR_DEFINITION} nodes for it — two conservative gates
 * ({@code StatementParsing.parseLocalVarDeclaration} rejects a name followed by {@code ','}, and
 * {@code VarDeclarationStatement.parseVarDefinitionList} drops everything after the first comma) leave
 * the whole statement as flat tokens with no {@code VAR_DECLARATION_STATEMENT}. Fixing that is a
 * separate parser/stub-indexing change; this annotator loop is the necessary editor-side half and is
 * already correct for whenever the parser does emit multiple declarators.</p>
 */
public class MQL4InputParameterAnnotatorTest extends BasePlatformTestCase {

    private List<String> inputHighlights(String code) {
        myFixture.configureByText("test.mq5", code);
        return myFixture.doHighlighting().stream()
                .filter(info -> info.forcedTextAttributesKey == MQL4Annotator.INPUT_PARAMETER)
                .map(HighlightInfo::getText)
                .collect(Collectors.toList());
    }

    public void testInputDeclaratorIsHighlighted() {
        assertTrue("the input declarator 'x' must get the input-parameter highlight",
                inputHighlights("input int x;\n").contains("x"));
    }

    public void testPlainDeclarationGetsNoInputHighlight() {
        // A non-input declaration (forms a VAR_DECLARATION_STATEMENT/VAR_DEFINITION but has no
        // input/sinput keyword) must not get the input-parameter attribute.
        assertTrue("plain (non-input) declarations must not be highlighted as input parameters",
                inputHighlights("int x;\n").isEmpty());
    }
}
