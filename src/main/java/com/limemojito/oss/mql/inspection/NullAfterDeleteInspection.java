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
 * with no {@code <identifier> = NULL} assignment anywhere afterwards
 * ({@link StatementAst#hasNullAssignmentAfter}).
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
                // One problem per function (preserves the original cardinality): the message names
                // the first delete found whose variable is never subsequently nulled.
                String[] offender = {null};
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    if (offender[0] != null) return;
                    ASTNode idNode = StatementAst.deletedIdentifier(stmt);
                    if (idNode == null) return;
                    String name = idNode.getText();
                    if (!StatementAst.hasNullAssignmentAfter(body, name, stmt.getTextRange().getEndOffset())) {
                        offender[0] = name;
                    }
                });
                if (offender[0] != null) {
                    problems.add(createWarning(manager, child.getNavigationElement(),
                            String.format(MESSAGE, offender[0], offender[0])));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
