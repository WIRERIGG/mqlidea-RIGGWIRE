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
import java.util.Set;

public class LargeStructByValueInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "User-defined type '%s' passed by value — use pass-by-reference (&) to avoid unnecessary copy";
    private static final Set<String> MQL5_LARGE_STRUCTS = Set.of(
            "MqlTradeRequest", "MqlTradeResult", "MqlTradeCheckResult",
            "MqlRates", "MqlTick", "MqlBookInfo", "MqlDateTime"
    );

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
            boolean hasRef = false;
            String typeName = null;
            boolean isUserType = false;

            ASTNode argChild = arg.getFirstChildNode();
            while (argChild != null) {
                if (argChild.getElementType() == MQL4Elements.AND) {
                    hasRef = true;
                }
                if (argChild.getElementType() == MQL4Elements.IDENTIFIER) {
                    ASTNode next = argChild.getTreeNext();
                    while (next != null && next.getElementType() == MQL4Elements.WHITE_SPACE) {
                        next = next.getTreeNext();
                    }
                    if (next != null && (next.getElementType() == MQL4Elements.IDENTIFIER
                            || next.getElementType() == MQL4Elements.AND)) {
                        typeName = argChild.getText();
                        isUserType = true;
                    }
                }
                argChild = argChild.getTreeNext();
            }

            if (!hasRef && isUserType && typeName != null) {
                if (MQL5_LARGE_STRUCTS.contains(typeName) || Character.isUpperCase(typeName.charAt(0))) {
                    problems.add(createWarning(manager, arg.getPsi(),
                            String.format(MESSAGE, typeName)));
                }
            }
        }
    }
}
