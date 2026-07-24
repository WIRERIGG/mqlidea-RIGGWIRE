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
 * Flags a {@code FileOpen()} call when the FILE has no {@code FileClose()} call anywhere in it.
 * Scoped to the whole file (not per-function) so the common global-handle idiom — open the file
 * in {@code OnInit()}, close it in {@code OnDeinit()} (RIGGWIRE_DataCapture.mq5:115/176,
 * RIGGWIRE_Logger.mqh:79/248) — is recognised as paired even though the two calls live in
 * different functions. A per-function pairing would wrongly flag {@code OnInit()}'s
 * {@code FileOpen()} as leaking just because the matching {@code FileClose()} is in
 * {@code OnDeinit()} instead.
 */
public class MissingFileCloseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "FileOpen() without corresponding FileClose() anywhere in the file — potential resource leak";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        boolean hasClose = false;
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body != null && StatementAst.hasCall(body, "FileClose")) {
                    hasClose = true;
                    break;
                }
            }
        }
        if (hasClose) return ProblemDescriptor.EMPTY_ARRAY;

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode call = StatementAst.findCall(body, "FileOpen");
                if (call != null) {
                    problems.add(createProblem(manager, StatementAst.anchor(call, child.getNavigationElement()), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
