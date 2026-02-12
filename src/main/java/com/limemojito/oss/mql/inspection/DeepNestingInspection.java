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

public class DeepNestingInspection extends MQL5SafetyInspectionBase {

    private static final int MAX_NESTING_DEPTH = 4;
    private static final String MESSAGE = "Excessive nesting depth (%d levels) — consider extracting methods to reduce complexity";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(func);
                if (body == null) continue;
                String stripped = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                int maxDepth = computeMaxBraceDepth(stripped);
                if (maxDepth > MAX_NESTING_DEPTH) {
                    problems.add(createWeakWarning(manager, func.getNavigationElement(),
                            String.format(MESSAGE, maxDepth)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static int computeMaxBraceDepth(@NotNull String text) {
        int depth = 0;
        int max = 0;
        for (int i = 0; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '{') {
                depth++;
                if (depth > max) {
                    max = depth;
                }
            } else if (c == '}') {
                depth--;
            }
        }
        return max;
    }
}
