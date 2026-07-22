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

public class ExcessiveGlobalVariablesInspection extends MQL5SafetyInspectionBase {

    private static final int MAX_GLOBALS = 10;
    private static final String MESSAGE = "Excessive global variables (%d non-input globals) — consider encapsulating in a class";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        List<PsiElement> vars = findTopLevelVarDeclarations(file);
        int nonInputCount = 0;
        for (PsiElement var : vars) {
            ProgressManager.checkCanceled();
            if (!isInputVariable(var) && !isExternVariable(var)) {
                nonInputCount++;
            }
        }
        if (nonInputCount > MAX_GLOBALS) {
            problems.add(createWeakWarning(manager, file,
                    String.format(MESSAGE, nonInputCount)));
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
