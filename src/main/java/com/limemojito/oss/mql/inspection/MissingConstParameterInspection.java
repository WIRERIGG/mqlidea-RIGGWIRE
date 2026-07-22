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
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingConstParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Parameter '%s' is a large type passed by reference — consider adding 'const'";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                checkFunctionArgs(func, manager, problems);
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private void checkFunctionArgs(@NotNull MQL4FunctionElement func,
                                   @NotNull InspectionManager manager,
                                   @NotNull List<ProblemDescriptor> problems) {
        for (ASTNode arg : getFunctionArgs(func)) {
            boolean hasConst = false;
            boolean hasRef = false;
            boolean isUserType = false;
            String paramName = null;

            ASTNode argChild = arg.getFirstChildNode();
            while (argChild != null) {
                if (argChild.getElementType() == MQL4Elements.CONST_KEYWORD) {
                    hasConst = true;
                }
                if (argChild.getElementType() == MQL4Elements.AND) {
                    hasRef = true;
                }
                if (argChild.getElementType() == MQL4Elements.IDENTIFIER) {
                    if (paramName == null) {
                        // First identifier might be a user type
                        ASTNode next = argChild.getTreeNext();
                        while (next != null && (next.getElementType() == MQL4Elements.WHITE_SPACE
                                || next.getElementType() == MQL4Elements.AND)) {
                            next = next.getTreeNext();
                        }
                        if (next != null && next.getElementType() == MQL4Elements.IDENTIFIER) {
                            isUserType = true;
                            paramName = next.getText();
                        } else {
                            paramName = argChild.getText();
                        }
                    } else {
                        paramName = argChild.getText();
                    }
                }
                argChild = argChild.getTreeNext();
            }

            if (hasRef && !hasConst && isUserType) {
                problems.add(createWeakWarning(manager, arg.getPsi(),
                        String.format(MESSAGE, paramName)));
            }
        }
    }
}
