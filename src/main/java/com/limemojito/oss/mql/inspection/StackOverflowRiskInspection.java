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

public class StackOverflowRiskInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Function '%s()' appears to call itself recursively without depth limit";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                String name = func.getFunctionName();
                if (name.equals(MQL4FunctionElement.UNKNOWN_NAME) || name.startsWith("~")) continue;
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasCall(body, name)) {
                    String text = StatementAst.heuristicText(body);
                    boolean hasDepthCheck = text.contains("depth") || text.contains("level")
                            || text.contains("maxRecurs") || text.contains("MAX_DEPTH");
                    if (!hasDepthCheck) {
                        problems.add(createWarning(manager, child.getNavigationElement(),
                                String.format(MESSAGE, name)));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
