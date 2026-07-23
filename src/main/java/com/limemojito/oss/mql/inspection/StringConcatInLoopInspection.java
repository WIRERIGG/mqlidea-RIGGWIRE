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

/**
 * String concatenation inside a loop, scoped via the statement AST: the existing concat pattern
 * ({@code +} adjacent to a string literal, matched on comment/string-stripped text) is only
 * searched within the body subtree of a {@code FOR/WHILE/DO_STATEMENT}. Concatenation outside
 * every loop body — including after a brace-less loop, which the old brace-scanning heuristic
 * misattributed to the loop — is no longer flagged.
 */
public class StringConcatInLoopInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "String concatenation inside loop — use StringConcatenate() or StringAdd() for better performance";

    private static final String CONCAT_PATTERN = "\\+\\s*\"|\"+\\s*\\+";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null || !BracketBlockTokenWalker.containsPattern(loopBody, CONCAT_PATTERN)) {
                        return;
                    }
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWeakWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
