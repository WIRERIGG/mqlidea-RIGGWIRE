/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingIndicatorReleaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Indicator handle created but IndicatorRelease() not found in OnDeinit — potential memory leak";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        boolean hasHandleCreation = false;
        boolean hasRelease = false;

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasAnyCall(body, MQL5_HANDLE_CREATORS)) {
                    hasHandleCreation = true;
                }
                if (StatementAst.hasCall(body, "IndicatorRelease")) {
                    hasRelease = true;
                }
            }
        }

        if (hasHandleCreation && !hasRelease) {
            List<MQL4FunctionElement> onDeinit = findFunctionsByName(file, "OnDeinit");
            if (onDeinit.isEmpty()) {
                // No OnDeinit at all — report on file level
                problems.add(createProblem(manager, file, MESSAGE));
            } else {
                for (MQL4FunctionElement deinit : onDeinit) {
                    ASTNode body = findBracketsBlock(deinit);
                    if (!StatementAst.hasCall(body, "IndicatorRelease")) {
                        problems.add(createProblem(manager, deinit.getNavigationElement(), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
