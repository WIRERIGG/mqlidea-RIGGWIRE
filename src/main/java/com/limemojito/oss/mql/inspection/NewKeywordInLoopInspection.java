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
 * AST-based detection of heap allocation inside a loop: a {@code NEW_KEYWORD} token anywhere in
 * the body subtree of a {@code FOR/WHILE/DO_STATEMENT}. The old text heuristic matched
 * {@code new} against the next {@code {...}} region after any loop keyword, so a brace-less loop
 * followed by an unrelated block containing {@code new} was a false positive; an allocation
 * outside every loop body is no longer flagged.
 */
public class NewKeywordInLoopInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Heap allocation ('new') inside loop — causes repeated allocation overhead and potential memory leaks";

    private static final TokenSet NEW_KEYWORD = TokenSet.create(MQL4Elements.NEW_KEYWORD);

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
                    if (loopBody == null || !StatementAst.hasDescendant(loopBody, NEW_KEYWORD)) return;
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
