/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class ClassNamingConventionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' should follow CClassName convention (start with 'C' prefix)";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            String name = cls.getTypeName();
            if (name.equals(MQL4ClassElement.UNKNOWN_NAME)) continue;
            if (!name.startsWith("C") || name.length() < 2 || !Character.isUpperCase(name.charAt(1))) {
                problems.add(createWeakWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, name)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
