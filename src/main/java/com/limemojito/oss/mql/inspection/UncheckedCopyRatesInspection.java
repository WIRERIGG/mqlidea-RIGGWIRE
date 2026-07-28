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

public class UncheckedCopyRatesInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "CopyRates/CopyBuffer return value should be checked (returns -1 on failure)";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                PsiElement navElement = child.getNavigationElement();
                // Evaluate EVERY copy/resize call, each against its own guard: a checked call followed
                // by an unchecked one (or vice-versa) must still flag the unchecked one — the old
                // first-call-only findAnyCall reported nothing whenever the FIRST call happened to be
                // checked.
                StatementAst.forEachCall(body, MQL5_COPY_FUNCS, call -> {
                    if (StatementAst.callReturnChecked(body, call)) {
                        return;
                    }
                    PsiElement anchor = StatementAst.anchor(call, navElement);
                    // Offer the wrap-in-check fix only for a bare call statement (safe to rewrite).
                    if (StatementAst.isBareCallStatement(call)) {
                        problems.add(createWarning(manager, anchor, MESSAGE, new WrapCallInFailureCheckFix(call.getText())));
                    } else {
                        problems.add(createWarning(manager, anchor, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
