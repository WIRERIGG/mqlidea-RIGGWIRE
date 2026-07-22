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

public class ImplicitCastInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Explicit type cast detected — verify this is intentional and safe";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                checkForCasts(func.getNode(), manager, problems);
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private void checkForCasts(@NotNull ASTNode node, @NotNull InspectionManager manager,
                               @NotNull List<ProblemDescriptor> problems) {
        ASTNode child = node.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.CAST_BLOCK) {
                problems.add(createWeakWarning(manager, child.getPsi(), MESSAGE));
            }
            if (child.getElementType() == MQL4Elements.BRACKETS_BLOCK) {
                // Don't recurse into function bodies deeper
            } else {
                checkForCasts(child, manager, problems);
            }
            child = child.getTreeNext();
        }
    }
}
