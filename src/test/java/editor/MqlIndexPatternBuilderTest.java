/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package editor;

import com.intellij.psi.PsiFile;
import com.intellij.psi.search.PsiTodoSearchHelper;
import com.intellij.psi.search.TodoItem;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;

/**
 * Phase 2d (REVAMP_PLAN.md): {@link com.limemojito.oss.mql.editor.MqlIndexPatternBuilder} wires
 * MQL comments into the platform's native TODO search, so the built-in TODO tool window finds
 * {@code // TODO: ...}/{@code // FIXME: ...} markers without the (now default-off) {@link
 * com.limemojito.oss.mql.inspection.TodoFixmeInspection} enabled.
 */
public class MqlIndexPatternBuilderTest extends BasePlatformTestCase {

    public void testTodoCommentIsFoundByNativeTodoSearch() {
        PsiFile file = myFixture.configureByText("test.mq4", "// TODO: refactor this\nvoid f() {}\n");
        TodoItem[] items = PsiTodoSearchHelper.getInstance(getProject()).findTodoItemsLight(file);
        assertEquals(1, items.length);
    }

    public void testFixmeCommentIsFoundToo() {
        PsiFile file = myFixture.configureByText("test.mq4", "// FIXME: this leaks a handle\nvoid f() {}\n");
        TodoItem[] items = PsiTodoSearchHelper.getInstance(getProject()).findTodoItemsLight(file);
        assertEquals(1, items.length);
    }

    public void testPlainCommentIsNotFound() {
        PsiFile file = myFixture.configureByText("test.mq4", "// just an ordinary comment\nvoid f() {}\n");
        TodoItem[] items = PsiTodoSearchHelper.getInstance(getProject()).findTodoItemsLight(file);
        assertEquals(0, items.length);
    }

    public void testMql5FileIsAlsoIndexed() {
        PsiFile file = myFixture.configureByText("test.mq5", "// TODO: port to MQL5\nvoid OnStart() {}\n");
        TodoItem[] items = PsiTodoSearchHelper.getInstance(getProject()).findTodoItemsLight(file);
        assertEquals(1, items.length);
    }
}
