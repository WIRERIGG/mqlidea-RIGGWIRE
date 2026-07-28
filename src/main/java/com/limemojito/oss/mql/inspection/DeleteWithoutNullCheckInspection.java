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

public class DeleteWithoutNullCheckInspection extends MQL5SafetyInspectionBase {

    private static final TokenSet DELETE_KEYWORD = TokenSet.create(MQL4Elements.DELETE_KEYWORD);

    // NOTE: absence of a null check before `delete` is not "use-after-free" (that is dereferencing a
    // pointer AFTER deletion — see DanglingObjectReferenceInspection). MQL5 does not require a null check
    // before `delete`, but validating a pointer with CheckPointer(p) == POINTER_DYNAMIC first is a
    // reasonable defensive habit, so this is surfaced only as a weak, optional suggestion.
    // Message describes what the quick fix (NullifyAfterDeleteFix) actually does — set the pointer to
    // NULL AFTER the delete so a later reuse is a safe null-deref, not a dangling-pointer access — as
    // the primary guidance, with the CheckPointer(p) == POINTER_DYNAMIC pre-delete validation offered
    // as the alternative. (The old message told the user to validate BEFORE delete while the fix acted
    // AFTER, a mismatch between the advice and the applied change.)
    private static final String MESSAGE = "'delete' without a null guard — set the pointer to NULL after deleting to prevent reuse of a dangling pointer (or validate it first with CheckPointer(p) == POINTER_DYNAMIC before deleting)";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode deleteNode = body == null ? null : StatementAst.findDescendant(body, DELETE_KEYWORD);
                if (deleteNode != null) {
                    if (!StatementAst.hasNullComparison(body)
                            && !StatementAst.hasIdentifier(body, "CheckPointer")) {
                        // Only offer the "null it after delete" quick fix for a bare `delete ptr;` —
                        // an array-element delete (`delete arr[i];`) has no single pointer variable
                        // to null out, so bareDeletedIdentifier() returns null and we fall back to
                        // the plain (fix-less) warning rather than guessing at what to insert.
                        ASTNode statement = deleteNode.getTreeParent();
                        ASTNode idNode = statement != null ? StatementAst.bareDeletedIdentifier(statement) : null;
                        ProblemDescriptor problem = idNode != null
                                ? createWeakWarning(manager, StatementAst.anchor(deleteNode, child.getNavigationElement()), MESSAGE,
                                        new NullifyAfterDeleteFix(idNode.getText()))
                                : createWeakWarning(manager, StatementAst.anchor(deleteNode, child.getNavigationElement()), MESSAGE);
                        problems.add(problem);
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
