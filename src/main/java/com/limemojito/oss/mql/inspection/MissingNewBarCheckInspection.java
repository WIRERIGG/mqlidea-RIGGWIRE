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

public class MissingNewBarCheckInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Heavy computation in OnTick() without new bar check — consider using IsNewBar() or static datetime guard";
    private static final Set<String> HEAVY_FUNCS = Set.of(
            "CopyRates", "CopyBuffer", "CopyTime", "CopyOpen", "CopyHigh",
            "CopyLow", "CopyClose", "CopyTicks", "CopyTicksRange",
            "CopyTickVolume", "CopyRealVolume", "CopySpread", "CopySeries"
    );

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && "OnTick".equals(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (!BracketBlockTokenWalker.containsAnyFunctionCall(body, HEAVY_FUNCS)) continue;
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                boolean hasNewBarGuard = text.contains("IsNewBar")
                        || text.contains("isNewBar")
                        || text.contains("static datetime")
                        || text.contains("static int prevBars")
                        || text.contains("iTime")
                        || text.contains("Bars(");
                if (!hasNewBarGuard) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
