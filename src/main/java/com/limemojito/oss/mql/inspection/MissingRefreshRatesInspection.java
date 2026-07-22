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
 * MQL4-only. Flags a function that reads live prices (Bid/Ask, or
 * MarketInfo with MODE_BID/MODE_ASK) inside a loop without ever calling
 * RefreshRates() — the predefined price variables are cached at event entry
 * and go stale while a loop runs.
 */
public class MissingRefreshRatesInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Prices (Bid/Ask) read in a loop without RefreshRates() — values may be stale";

    /**
     * Whole-word Bid/Ask usage, or a MarketInfo() call requesting MODE_BID/MODE_ASK.
     * Matched inside loop bodies only (via containsPatternInLoop) to stay conservative.
     */
    private static final String PRICE_USAGE_IN_LOOP_REGEX =
            "\\b(?:Bid|Ask)\\b|\\bMarketInfo\\s*\\([^;)]*MODE_(?:BID|ASK)\\b";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                if (BracketBlockTokenWalker.containsPatternInLoop(body, PRICE_USAGE_IN_LOOP_REGEX)
                        && !BracketBlockTokenWalker.containsFunctionCall(body, "RefreshRates")) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
