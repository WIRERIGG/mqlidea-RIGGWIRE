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

public class UncheckedHandleInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Indicator handle should be checked against INVALID_HANDLE after creation";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                PsiElement navElement = child.getNavigationElement();
                // Evaluate EVERY handle creation, each against ITS OWN guard: two indicator handles
                // where only the first is compared to INVALID_HANDLE must still flag the second. The
                // old code checked only the first creation and, worse, its guard was body-wide — any
                // single INVALID_HANDLE mention anywhere marked ALL creations safe.
                StatementAst.forEachCall(body, MQL5_HANDLE_CREATORS, call -> {
                    if (handleChecked(body, call)) {
                        return;
                    }
                    PsiElement anchor = StatementAst.anchor(call, navElement);
                    String handle = StatementAst.assignmentTargetName(call);
                    // Offer the guard fix only when the handle was assigned to a named variable.
                    if (handle != null) {
                        problems.add(createProblem(manager, anchor, MESSAGE, new CheckHandleAfterCreationFix(handle)));
                    } else {
                        problems.add(createProblem(manager, anchor, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * True when THIS handle creation's return value is validated (per-call, not body-wide).
     * INVALID_HANDLE is {@code -1}, so comparing the captured handle variable to INVALID_HANDLE,
     * {@code -1} or any failure sentinel — inline or after capture — all count (see
     * {@link StatementAst#callReturnChecked}). Only when the creation is not captured into a named
     * variable do we fall back to the old body-wide INVALID_HANDLE / failure-check guard, since there
     * is then no variable to attribute a specific check to.
     */
    private static boolean handleChecked(ASTNode body, @NotNull ASTNode call) {
        if (StatementAst.callReturnChecked(body, call)) {
            return true;
        }
        return StatementAst.assignmentTargetName(call) == null
                && (StatementAst.hasIdentifier(body, "INVALID_HANDLE") || StatementAst.hasFailureReturnCheck(body));
    }
}
