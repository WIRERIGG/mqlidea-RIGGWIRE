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
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class UnusedParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Parameter '%s' is never used in function body";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                if (isEventHandler(func)) continue;
                ASTNode body = findBracketsBlock(func);
                if (body == null) continue;
                List<ASTNode> args = getFunctionArgs(func);
                for (ASTNode arg : args) {
                    ASTNode idNode = arg.findChildByType(MQL4Elements.IDENTIFIER);
                    if (idNode == null) continue;
                    // The last IDENTIFIER in a FUNCTION_ARG is the parameter name;
                    // earlier IDENTIFIERs may be the type name. Walk to find the last one.
                    ASTNode lastId = idNode;
                    ASTNode sibling = idNode.getTreeNext();
                    while (sibling != null) {
                        if (sibling.getElementType() == MQL4Elements.IDENTIFIER) {
                            lastId = sibling;
                        }
                        sibling = sibling.getTreeNext();
                    }
                    String paramName = lastId.getText();
                    if (paramName == null || paramName.isEmpty()) continue;
                    if (!BracketBlockTokenWalker.containsIdentifier(body, paramName)) {
                        problems.add(createWeakWarning(manager, arg.getPsi(),
                                String.format(MESSAGE, paramName)));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
