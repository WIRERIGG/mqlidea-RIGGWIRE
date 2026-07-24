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
import java.util.Set;

public class ArrayResizeReturnCheckInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "ArrayResize() return value should be checked (returns -1 on failure)";
    private static final Set<String> ARRAY_RESIZE = Set.of("ArrayResize");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachCall(body, ARRAY_RESIZE, call -> {
                    // Skip a resize whose return is already checked, and one that provably cannot
                    // fail (resize-to-0 / shrink) — flagging those would only invite dead checks.
                    if (StatementAst.callReturnChecked(body, call) || StatementAst.arrayResizeCannotFail(call)) {
                        return;
                    }
                    PsiElement anchor = StatementAst.anchor(call, child.getNavigationElement());
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
