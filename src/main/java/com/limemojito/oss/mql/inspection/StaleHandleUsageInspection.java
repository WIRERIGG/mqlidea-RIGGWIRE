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
 * AST-based detection: an {@code IndicatorRelease(handle)} call followed (at or after its own end
 * offset) by a {@code CopyBuffer(...)} call whose args reference the same handle identifier — the
 * released handle reused without reassignment.
 */
public class StaleHandleUsageInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Handle released then reused without reassignment — potential use-after-free";
    private static final Set<String> INDICATOR_RELEASE = Set.of("IndicatorRelease");
    private static final Set<String> COPY_BUFFER = Set.of("CopyBuffer");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean[] flagged = {false};
                StatementAst.forEachCall(body, INDICATOR_RELEASE, releaseCall -> {
                    if (flagged[0]) return;
                    ASTNode args = StatementAst.callArgsBlock(releaseCall);
                    ASTNode handleId = args == null ? null : firstIdentifier(args);
                    if (handleId == null) return;
                    String handle = handleId.getText();
                    int afterRelease = args.getTextRange().getEndOffset();
                    boolean[] reused = {false};
                    StatementAst.forEachCall(body, COPY_BUFFER, copyCall -> {
                        if (reused[0] || copyCall.getStartOffset() < afterRelease) return;
                        ASTNode copyArgs = StatementAst.callArgsBlock(copyCall);
                        if (copyArgs != null && StatementAst.hasIdentifier(copyArgs, handle)) {
                            reused[0] = true;
                        }
                    });
                    if (reused[0]) flagged[0] = true;
                });
                if (flagged[0]) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** First {@code IDENTIFIER} token directly inside a {@code (...)} args block, or null. */
    private static ASTNode firstIdentifier(@NotNull ASTNode argsBlock) {
        for (ASTNode c = argsBlock.getFirstChildNode(); c != null; c = c.getTreeNext()) {
            if (c.getElementType() == com.limemojito.oss.mql.psi.MQL4Elements.IDENTIFIER) {
                return c;
            }
        }
        return null;
    }
}
