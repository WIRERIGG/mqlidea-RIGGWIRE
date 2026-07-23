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

public class DeleteWithoutNullCheckInspection extends MQL5SafetyInspectionBase {

    // NOTE: absence of a null check before `delete` is not "use-after-free" (that is dereferencing a
    // pointer AFTER deletion — see DanglingObjectReferenceInspection). MQL5 does not require a null check
    // before `delete`, but validating a pointer with CheckPointer(p) == POINTER_DYNAMIC first is a
    // reasonable defensive habit, so this is surfaced only as a weak, optional suggestion.
    private static final String MESSAGE = "'delete' without a prior CheckPointer()/NULL guard — consider validating the pointer (CheckPointer(p) == POINTER_DYNAMIC) before deleting";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (BracketBlockTokenWalker.containsPattern(body, "\\bdelete\\b")) {
                    if (!BracketBlockTokenWalker.containsPattern(body, "!=\\s*NULL")
                            && !BracketBlockTokenWalker.containsPattern(body, "==\\s*NULL")
                            && !BracketBlockTokenWalker.containsIdentifier(body, "CheckPointer")) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
