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

/**
 * AST-based detection of {@code if(x);} / {@code for(...);} / {@code while(y);}: a control
 * statement whose body (the first statement node after the condition {@code (...)} block) is an
 * {@code EMPTY_STATEMENT}. Semicolons inside a {@code for} header are children of the condition
 * block, and calls in the header (e.g. {@code for(i=Foo(); i<n; i++){...}}) never produce false
 * positives because only the statement's body node is examined.
 */
public class SuspiciousSemicolonInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Suspicious semicolon after control statement — likely a logic error (empty body)";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.CONDITION_STATEMENTS, stmt -> {
                    ASTNode stmtBody = StatementAst.findBodyAfterCondition(stmt);
                    if (stmtBody != null && stmtBody.getElementType() == MQL4Elements.EMPTY_STATEMENT) {
                        PsiElement psi = stmt.getPsi();
                        if (psi != null && psi.isValid()) {
                            problems.add(createWarning(manager, psi, MESSAGE, isOnTheFly));
                        }
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
