/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
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
 * Flags an unconditional logging call in {@code OnTick()}/{@code OnCalculate()} — one that fires on
 * every single tick and floods the log/UI. A logging call nested inside an {@code if} is left
 * alone: that is the conditional/error-path idiom
 * {@code if(!trade.Buy(...)) Print("failed", GetLastError());}, which logs only on the (rare)
 * failure path, not every tick.
 */
public class PrintInOnTickInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Print()/Comment() in OnTick() causes excessive logging and performance degradation";
    private static final Set<String> TICK_HANDLERS = Set.of("OnTick", "OnCalculate");
    private static final Set<String> LOGGING_FUNCS = Set.of("Print", "PrintFormat", "Comment", "Alert");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && TICK_HANDLERS.contains(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                ASTNode[] found = {null};
                StatementAst.forEachCall(body, LOGGING_FUNCS, id -> {
                    if (found[0] == null && !StatementAst.isNestedInIfStatement(id, body)) {
                        found[0] = id;
                    }
                });
                if (found[0] != null) {
                    PsiElement anchor = StatementAst.anchor(found[0], child.getNavigationElement());
                    problems.add(manager.createProblemDescriptor(anchor, anchor, MESSAGE,
                            ProblemHighlightType.WARNING, true));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
