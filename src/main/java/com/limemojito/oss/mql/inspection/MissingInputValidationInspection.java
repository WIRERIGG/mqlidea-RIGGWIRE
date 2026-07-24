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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingInputValidationInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OnInit() should validate input parameters before use";
    private static final TokenSet IF_STATEMENT = TokenSet.create(MQL4Elements.IF_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        boolean hasInputVars = false;
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == com.limemojito.oss.mql.psi.MQL4Elements.VAR_DECLARATION_STATEMENT
                    && isInputVariable(child)) {
                hasInputVars = true;
                break;
            }
        }
        if (!hasInputVars) return ProblemDescriptor.EMPTY_ARRAY;

        List<MQL4FunctionElement> onInitFuncs = findFunctionsByName(file, "OnInit");
        for (MQL4FunctionElement onInit : onInitFuncs) {
            if (onInit.isDeclaration()) continue;
            ASTNode body = findBracketsBlock(onInit);
            if (body == null || bracketBlockIsEmpty(body)) {
                problems.add(createWarning(manager, onInit.getNavigationElement(), MESSAGE, isOnTheFly));
            } else {
                boolean hasValidation = StatementAst.hasDescendant(body, IF_STATEMENT)
                        || StatementAst.hasIdentifier(body, "INIT_PARAMETERS_INCORRECT");
                if (!hasValidation) {
                    problems.add(createWeakWarning(manager, onInit.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        if (hasInputVars && onInitFuncs.isEmpty()) {
            problems.add(createWarning(manager, file,
                    "File has input parameters but no OnInit() to validate them", isOnTheFly));
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
