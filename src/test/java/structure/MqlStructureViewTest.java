/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package structure;

import com.intellij.ide.structureView.StructureViewBuilder;
import com.intellij.ide.structureView.StructureViewModel;
import com.intellij.ide.structureView.StructureViewTreeElement;
import com.intellij.ide.structureView.TreeBasedStructureViewBuilder;
import com.intellij.psi.PsiFile;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.structure.MQL4StructureViewBuilderFactory;

import java.util.ArrayList;
import java.util.List;

/**
 * The Structure view is built from platform-core API only ({@link TreeBasedStructureViewBuilder},
 * no {@code StructureViewComponent} / {@code PsiTreeElementBase}, which CLion 2026.3 moved to a
 * plugin this one cannot see), and lists the file's functions, classes and named enums.
 */
public class MqlStructureViewTest extends BasePlatformTestCase {

    public void testFileRootListsTopLevelDeclarations() {
        PsiFile file = myFixture.configureByText("test.mq5",
                "enum ENUM_MODE { MODE_A };\nenum { ANON };\nclass CItem { public: void Run() { } };\n"
                        + "class CFwd;\nint OnInit() { return 0; }\nvoid Helper(int v);\n");
        StructureViewBuilder builder = new MQL4StructureViewBuilderFactory().getStructureViewBuilder(file);
        assertInstanceOf(builder, TreeBasedStructureViewBuilder.class);
        TreeBasedStructureViewBuilder tree = (TreeBasedStructureViewBuilder) builder;
        assertTrue(tree.isRootNodeShown());

        StructureViewModel model = tree.createStructureViewModel(myFixture.getEditor());
        try {
            StructureViewTreeElement root = model.getRoot();
            assertEquals("test.mq5", root.getPresentation().getPresentableText());
            assertSame(file, root.getValue());
            List<String> names = new ArrayList<>();
            for (var child : root.getChildren()) {
                names.add(child.getPresentation().getPresentableText());
            }
            // the anonymous enum and the forward class declaration are not listed
            assertEquals(4, names.size());
            assertTrue(names.toString(), names.stream().anyMatch(n -> n.startsWith("ENUM_MODE")));
            assertTrue(names.toString(), names.stream().anyMatch(n -> n.startsWith("CItem")));
            assertTrue(names.toString(), names.stream().anyMatch(n -> n.startsWith("OnInit")));
            assertTrue(names.toString(), names.stream().anyMatch(n -> n.startsWith("Helper")));
        } finally {
            model.dispose();
        }
    }
}
