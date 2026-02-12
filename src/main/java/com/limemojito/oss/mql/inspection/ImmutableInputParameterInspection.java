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

import java.util.ArrayList;
import java.util.List;

public class ImmutableInputParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Input parameter '%s' appears to be reassigned — input variables should be treated as immutable";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        List<String> inputNames = new ArrayList<>();

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == com.limemojito.oss.mql.psi.MQL4Elements.VAR_DECLARATION_STATEMENT
                    && isInputVariable(child)) {
                String name = getVariableName(child);
                if (name != null) inputNames.add(name);
            }
        }
        if (inputNames.isEmpty()) return ProblemDescriptor.EMPTY_ARRAY;

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                for (String inputName : inputNames) {
                    if (text.contains(inputName + " =") || text.contains(inputName + "=")
                            || text.contains(inputName + "++") || text.contains(inputName + "--")
                            || text.contains("++" + inputName) || text.contains("--" + inputName)) {
                        problems.add(createWarning(manager, child.getNavigationElement(),
                                String.format(MESSAGE, inputName)));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
