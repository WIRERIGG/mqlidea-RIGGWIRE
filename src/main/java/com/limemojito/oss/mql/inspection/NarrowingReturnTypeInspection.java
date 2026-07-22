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

public class NarrowingReturnTypeInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Function '%s' returns int but accepts double parameters — potential precision loss";
    private static final Set<String> INTEGER_TYPES = Set.of("INT_KEYWORD", "LONG_KEYWORD", "SHORT_KEYWORD",
            "CHAR_KEYWORD", "UINT_KEYWORD", "ULONG_KEYWORD", "USHORT_KEYWORD", "UCHAR_KEYWORD");
    private static final Set<String> FLOAT_TYPES = Set.of("DOUBLE_KEYWORD", "FLOAT_KEYWORD");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode returnType = getReturnTypeNode(func);
                if (returnType == null) continue;
                String returnTypeName = returnType.getElementType().toString();
                if (!INTEGER_TYPES.contains(returnTypeName)) continue;

                boolean hasDoubleParam = false;
                for (ASTNode arg : getFunctionArgs(func)) {
                    ASTNode argChild = arg.getFirstChildNode();
                    while (argChild != null) {
                        if (FLOAT_TYPES.contains(argChild.getElementType().toString())) {
                            hasDoubleParam = true;
                            break;
                        }
                        argChild = argChild.getTreeNext();
                    }
                    if (hasDoubleParam) break;
                }

                if (hasDoubleParam) {
                    problems.add(createWarning(manager, child.getNavigationElement(),
                            String.format(MESSAGE, func.getFunctionName())));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
