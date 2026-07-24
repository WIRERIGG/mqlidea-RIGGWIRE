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
import java.util.Set;

/**
 * AST-based detection of {@code ArrayResize()} inside a loop: the call must occur in the body
 * subtree of a {@code FOR/WHILE/DO_STATEMENT} found via the statement tree (the body node after
 * the loop header, whether a {@code {...}} block or a single statement). Calls before/after a
 * loop — including the old false positive where a brace-less loop was followed by an unrelated
 * {@code {...}} block containing the call — are no longer flagged.
 * <p>
 * The 3-argument {@code ArrayResize(array, new_size, reserve_size)} form is the doc-endorsed
 * pattern for exactly this situation (arrayresize.html: "it is recommended to use a third
 * parameter that sets a reserve to reduce the number of physical memory allocations" — subsequent
 * calls only change the reported size, without a physical reallocation) — that form is never
 * flagged, only the plain 2-arg form which reallocates on every call.
 */
public class ArrayResizeInLoopInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "ArrayResize() inside loop — pre-allocate array before loop for better performance";

    private static final String ARRAY_RESIZE = "ArrayResize";
    private static final Set<String> ARRAY_RESIZE_NAMES = Set.of(ARRAY_RESIZE);

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
                    if (loopBody == null) return;
                    ASTNode[] flagged = {null};
                    StatementAst.forEachCall(loopBody, ARRAY_RESIZE_NAMES, callId -> {
                        // 3rd (reserve) argument present — the recommended no-reallocation pattern.
                        if (flagged[0] == null && StatementAst.callArgCount(callId) < 3) {
                            flagged[0] = callId;
                        }
                    });
                    if (flagged[0] == null) return;
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
