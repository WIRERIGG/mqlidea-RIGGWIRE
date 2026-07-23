/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;

/**
 * Retired detection. This rule scanned <em>file-scope (global)</em> variable declarations, but MQL5
 * guarantees that global and static variables are zero-initialized when no initializer is given
 * (docs: "global and static variables ... are initialized with zero"). Every variable it flagged was
 * therefore already well-defined (0 / 0.0 / false / ""), and its "add {@code = 0}" quick-fix only added
 * redundant noise. The genuinely dangerous case — an uninitialized <em>local</em> variable, which MQL5
 * does not auto-zero — requires intraprocedural data-flow analysis to detect without a flood of false
 * positives and is not implemented here. The inspection is kept (registered, disabled by default) but
 * reports nothing so it can no longer flag correctly zero-initialized globals.
 */
public class UninitializedVariableInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        return ProblemDescriptor.EMPTY_ARRAY;
    }
}
