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
 * Retired detection. In MQL5 destructors are <em>always</em> virtual — the docs state:
 * "Destructors are always virtual, regardless of whether they are declared with the virtual keyword
 * or not." Deleting a derived object through a base pointer therefore already dispatches to the correct
 * destructor, so the C++ "virtual method without a virtual destructor → slicing/leak" hazard this rule
 * imported does not exist in MQL5. The inspection is kept (registered, disabled by default) but reports
 * nothing so it can no longer emit false positives.
 */
public class VirtualWithoutDestructorInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        return ProblemDescriptor.EMPTY_ARRAY;
    }
}
