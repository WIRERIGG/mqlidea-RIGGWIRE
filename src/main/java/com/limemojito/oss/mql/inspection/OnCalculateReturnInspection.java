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
 * MQL5-only. Flags {@code return 0;} / {@code return(0);} inside
 * OnCalculate() — returning 0 tells the terminal that nothing was calculated,
 * forcing a full indicator recalculation on every tick. Return rates_total
 * (or prev_calculated) instead.
 */
public class OnCalculateReturnInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "OnCalculate() returning 0 forces a full recalculation each tick — return rates_total (or prev_calculated)";

    private static final TokenSet RETURN_STATEMENT = TokenSet.create(MQL4Elements.RETURN_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && "OnCalculate".equals(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean[] flagged = {false};
                StatementAst.forEachDescendant(body, RETURN_STATEMENT, returnStmt -> {
                    if (!flagged[0] && isReturnZero(returnStmt)) flagged[0] = true;
                });
                if (flagged[0]) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** True when {@code returnStmt} is {@code return 0;} or {@code return(0);} — a bare literal 0, nothing else. */
    private static boolean isReturnZero(@NotNull ASTNode returnStmt) {
        ASTNode expr = returnStmt.findChildByType(MQL4Elements.RETURN_KEYWORD);
        if (expr == null) return false;
        ASTNode next = StatementAst.nextNonTrivia(expr);
        if (next != null && StatementAst.isParenBlock(next)) {
            String inner = next.getText().trim();
            inner = inner.substring(1, inner.length() - 1).trim();
            return "0".equals(inner);
        }
        return next != null && next.getElementType() == MQL4Elements.INTEGER_LITERAL && "0".equals(next.getText());
    }
}
