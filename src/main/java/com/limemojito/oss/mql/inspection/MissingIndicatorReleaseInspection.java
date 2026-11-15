/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
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
        java.util.Set<String> handles = new java.util.LinkedHashSet<>();

        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasAnyCall(body, MQL5_HANDLE_CREATORS)) {
                    hasHandleCreation = true;
                    StatementAst.forEachCall(body, MQL5_HANDLE_CREATORS, call -> {
                        String target = StatementAst.assignmentTargetName(call);
                        if (target != null) {
                            handles.add(target);
                        }
                    });
                }
                if (StatementAst.hasCall(body, "IndicatorRelease")) {
                    hasRelease = true;
                }
            }
        }

        if (hasHandleCreation && !hasRelease) {
            java.util.Set<String> globals = globalVariableNames(file);
            List<String> releasable = handles.stream().filter(globals::contains).toList();
            LocalQuickFix[] fixes = releasable.isEmpty() ? LocalQuickFix.EMPTY_ARRAY
                    : new LocalQuickFix[]{new ReleaseIndicatorHandlesFix(releasable)};
            List<MQL4FunctionElement> onDeinit = findFunctionsByName(file, "OnDeinit");
            if (onDeinit.isEmpty()) {
                // No OnDeinit at all — report on file level
                problems.add(createProblem(manager, file, MESSAGE, fixes));
            } else {
                for (MQL4FunctionElement deinit : onDeinit) {
                    ASTNode body = findBracketsBlock(deinit);
                    if (!StatementAst.hasCall(body, "IndicatorRelease")) {
                        problems.add(createProblem(manager, deinit.getNavigationElement(), MESSAGE, fixes));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** Names of the file's global variables: only those still exist in OnDeinit to be released. */
    @NotNull
    private static java.util.Set<String> globalVariableNames(@NotNull PsiFile file) {
        java.util.Set<String> names = new java.util.HashSet<>();
        for (com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement v : com.intellij.psi.util.PsiTreeUtil.findChildrenOfType(file,
                com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement.class)) {
            if (com.intellij.psi.util.PsiTreeUtil.getParentOfType(v, MQL4FunctionElement.class, com.limemojito.oss.mql.psi.impl.MQL4ClassElement.class) == null
                    && v.getName() != null) {
                names.add(v.getName());
            }
        }
        return names;
    }
}
