/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class FunctionNamingConventionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Function '%s' should use PascalCase naming convention";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                String name = func.getFunctionName();
                if (name.startsWith("~") || name.equals(MQL4FunctionElement.UNKNOWN_NAME)) continue;
                if (MQL5_EVENT_HANDLERS.contains(name)) continue;
                if (!isPascalCase(name)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(),
                            String.format(MESSAGE, name)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private boolean isPascalCase(@NotNull String name) {
        if (name.isEmpty()) return false;
        if (!Character.isUpperCase(name.charAt(0))) return false;
        return !name.contains("_") || name.equals(name.toUpperCase());
    }
}
