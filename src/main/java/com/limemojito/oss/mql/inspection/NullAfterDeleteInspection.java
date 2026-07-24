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

/**
 * AST-based detection: a bare {@code delete <identifier>;} ({@link StatementAst#deletedIdentifier})
 * with no {@code <identifier> = <anything>} reassignment anywhere afterwards
 * ({@link StatementAst#hasAssignmentAfter}) — not just the literal {@code = NULL} guard, since the
 * delete-then-recreate idiom {@code delete obj; obj = new CFoo();} equally ends the dangling window.
 * Also does not flag a delete that is the last statement directly in {@code OnDeinit()}'s body:
 * nothing dangles once the handler (and usually the program) has finished tearing down.
 */
public class NullAfterDeleteInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "'delete %s' without subsequent '%s = NULL' — leaves dangling pointer";
    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean isOnDeinit = "OnDeinit".equals(func.getFunctionName());
                // One problem per function (preserves the original cardinality): the message names
                // the first delete found whose variable is never subsequently reassigned. Anchor at
                // that delete's identifier, not the function header.
                ASTNode[] offenderNode = {null};
                ASTNode[] offenderStatement = {null};
                String[] offenderName = {null};
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    if (offenderNode[0] != null) return;
                    ASTNode idNode = StatementAst.deletedIdentifier(stmt);
                    if (idNode == null) return;
                    if (isOnDeinit && stmt.getTreeParent() == body) {
                        ASTNode after = StatementAst.nextNonTrivia(stmt);
                        if (after == null || after.getElementType() == MQL4Elements.R_CURLY_BRACKET) {
                            return; // last statement in OnDeinit — nothing dangles afterward
                        }
                    }
                    String name = idNode.getText();
                    if (!StatementAst.hasAssignmentAfter(body, name, stmt.getTextRange().getEndOffset())) {
                        offenderNode[0] = idNode;
                        offenderStatement[0] = stmt;
                        offenderName[0] = name;
                    }
                });
                if (offenderNode[0] != null) {
                    PsiElement anchor = StatementAst.anchor(offenderNode[0], child.getNavigationElement());
                    String message = String.format(MESSAGE, offenderName[0], offenderName[0]);
                    // Only offer the "insert <name> = NULL;" quick fix when the delete is truly a
                    // bare `delete <name>;` (bareDeletedIdentifier), not e.g. `delete arr[i];` —
                    // which still warns using the array's identifier, but must not get an
                    // `arr = NULL;` fix wiping out the whole array reference.
                    ProblemDescriptor problem = StatementAst.bareDeletedIdentifier(offenderStatement[0]) != null
                            ? createWarning(manager, anchor, message, new NullifyAfterDeleteFix(offenderName[0]))
                            : createWarning(manager, anchor, message);
                    problems.add(problem);
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
