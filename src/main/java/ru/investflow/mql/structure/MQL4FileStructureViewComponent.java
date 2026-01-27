/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.structure;

import com.intellij.ide.structureView.newStructureView.StructureViewComponent;
import com.intellij.openapi.fileEditor.FileEditor;
import com.intellij.openapi.project.Project;
import ru.investflow.mql.psi.MQL4File;

public class MQL4FileStructureViewComponent extends StructureViewComponent {

    public MQL4FileStructureViewComponent(Project project, MQL4File file, FileEditor fileEditor) {
        super(fileEditor, new MQL4FileStructureViewModel(file), project, true);
    }
}
