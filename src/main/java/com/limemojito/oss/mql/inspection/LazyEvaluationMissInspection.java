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
 * Retired detection. The former heuristic — "an indicator call followed anywhere later by an {@code if}"
 * — is satisfied by virtually every real {@code OnTick}, so it fired almost unconditionally, and its
 * premise was confused: MQL5 {@code &&}/{@code ||} are already short-circuit (documented), so there is no
 * "lazy evaluation" defect to introduce. Deciding whether a {@code CopyBuffer}/{@code CopyRates} call
 * should be moved inside a branch requires real data-flow analysis, not a keyword-position text scan, and
 * the per-bar-vs-per-tick concern is already covered by MissingNewBarCheckInspection. The inspection is
 * kept (registered, disabled by default) but reports nothing so it can no longer emit false positives.
 */
public class LazyEvaluationMissInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        return ProblemDescriptor.EMPTY_ARRAY;
    }
}
