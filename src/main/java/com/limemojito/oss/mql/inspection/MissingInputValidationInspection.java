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
import java.util.Locale;

public class MissingInputValidationInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OnInit() should validate input parameters before use";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        boolean hasInputVars = false;
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT
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
            }
            // Softened: previously any non-empty OnInit() lacking an if-statement was flagged as
            // "missing validation" — but plenty of legitimate OnInit bodies (setting a timer,
            // subscribing to a symbol, initializing an object from string/enum/bool inputs that
            // need no range check) do real setup without ever needing an `if`. That produced a
            // false positive on nearly every EA with non-numeric inputs, so this branch is dropped
            // rather than approximated further.
        }
        if (hasInputVars && onInitFuncs.isEmpty() && isMqlSourceFile(file)) {
            problems.add(createWarning(manager, file,
                    "File has input parameters but no OnInit() to validate them", isOnTheFly));
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * True when {@code file}'s name ends in {@code .mq4}/{@code .mq5} — an actual program entry
     * point that can define {@code OnInit()}. A {@code .mqh} header is never expected to have one
     * (it is included into a program file that does), so warning about a missing {@code OnInit()}
     * on every header that happens to declare an {@code input} was a false positive.
     */
    private static boolean isMqlSourceFile(@NotNull PsiFile file) {
        String name = file.getName().toLowerCase(Locale.ROOT);
        return name.endsWith(".mq4") || name.endsWith(".mq5");
    }
}
