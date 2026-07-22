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
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class VariableNamingConventionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Variable '%s' should use camelCase or snake_case naming convention";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : findTopLevelVarDeclarations(file)) {
            ProgressManager.checkCanceled();
            String name = getVariableName(child);
            if (name == null) continue;
            if (!isCamelCase(name) && !isSnakeCase(name) && !isAllCaps(name)) {
                problems.add(createWeakWarning(manager, child,
                        String.format(MESSAGE, name)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private boolean isCamelCase(@NotNull String name) {
        if (name.isEmpty()) return false;
        return Character.isLowerCase(name.charAt(0)) && !name.contains("_");
    }

    private boolean isSnakeCase(@NotNull String name) {
        return name.equals(name.toLowerCase()) && name.contains("_");
    }

    private boolean isAllCaps(@NotNull String name) {
        return name.equals(name.toUpperCase());
    }
}
