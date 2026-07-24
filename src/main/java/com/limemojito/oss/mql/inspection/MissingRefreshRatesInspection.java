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
 * MQL4-only. Flags a function that reads live prices (Bid/Ask, or
 * MarketInfo with MODE_BID/MODE_ASK) inside a loop without ever calling
 * RefreshRates() — the predefined price variables are cached at event entry
 * and go stale while a loop runs. Price usage is looked for structurally inside the AST loop-body
 * subtree (see {@link StatementAst#findLoopBody}) rather than a brace-matched text region, so a
 * brace-less loop followed by an unrelated block can no longer be mistaken for the loop body.
 */
public class MissingRefreshRatesInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Prices (Bid/Ask) read in a loop without RefreshRates() — values may be stale";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                boolean[] usesStalePrice = {false};
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    if (usesStalePrice[0]) return;
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null) return;
                    if (StatementAst.hasIdentifier(loopBody, "Bid") || StatementAst.hasIdentifier(loopBody, "Ask")
                            || marketInfoBidAsk(loopBody)) {
                        usesStalePrice[0] = true;
                    }
                });
                if (usesStalePrice[0] && !StatementAst.hasCall(body, "RefreshRates")) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** True when a {@code MarketInfo(...)} call in {@code loopBody} requests {@code MODE_BID}/{@code MODE_ASK}. */
    private static boolean marketInfoBidAsk(@NotNull ASTNode loopBody) {
        boolean[] found = {false};
        StatementAst.forEachCall(loopBody, Set.of("MarketInfo"), callId -> {
            if (found[0]) return;
            ASTNode args = StatementAst.callArgsBlock(callId);
            if (args != null && (StatementAst.hasIdentifier(args, "MODE_BID") || StatementAst.hasIdentifier(args, "MODE_ASK"))) {
                found[0] = true;
            }
        });
        return found[0];
    }
}
