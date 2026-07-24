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
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.Set;

public class SecureCodingPatternsInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Handle-returning function used without INVALID_HANDLE check";
    // Only functions that actually return a handle with the INVALID_HANDLE (-1) sentinel belong here.
    // Excluded: ObjectCreate (returns bool), ChartOpen (returns a long chart id, 0 on failure) — neither
    // is checked against INVALID_HANDLE, so flagging them here emitted factually wrong diagnostics.
    private static final Set<String> HANDLE_FUNCS = Set.of("FileOpen", "IndicatorCreate");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasAnyCall(body, HANDLE_FUNCS)) {
                    if (!StatementAst.hasIdentifier(body, "INVALID_HANDLE")
                            && !hasNegativeOneOrNegativeComparison(body)) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** True when a {@code != -1} or {@code < 0} comparison occurs anywhere in {@code root}. */
    private static boolean hasNegativeOneOrNegativeComparison(@Nullable ASTNode root) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == MQL4Elements.NOT_EQ && isNegativeOne(StatementAst.nextNonTrivia(child))) {
                return true;
            }
            if (child.getElementType() == MQL4Elements.LT) {
                ASTNode next = StatementAst.nextNonTrivia(child);
                if (next != null && next.getElementType() == MQL4Elements.INTEGER_LITERAL && "0".equals(next.getText())) {
                    return true;
                }
            }
            if (hasNegativeOneOrNegativeComparison(child)) return true;
        }
        return false;
    }

    private static boolean isNegativeOne(@Nullable ASTNode node) {
        if (node == null || node.getElementType() != MQL4Elements.MINUS) return false;
        ASTNode next = StatementAst.nextNonTrivia(node);
        return next != null && next.getElementType() == MQL4Elements.INTEGER_LITERAL && "1".equals(next.getText());
    }
}
