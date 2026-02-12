/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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

public class MissingErrorRecoveryInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OrderSend() failure without retry or recovery logic";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (BracketBlockTokenWalker.containsFunctionCall(body, "OrderSend")) {
                    String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                    boolean hasRetry = text.contains("retry") || text.contains("attempt")
                            || text.contains("for") || text.contains("while");
                    boolean hasErrorHandling = text.contains("GetLastError") || text.contains("retcode");
                    if (hasErrorHandling && !hasRetry) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
