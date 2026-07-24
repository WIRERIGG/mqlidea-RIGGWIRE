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
 * Flags {@code MathSrand()} seeded with anything other than {@code GetTickCount()}. Per the spec
 * (math/mathsrand.html): {@code GetTickCount()} is the one call explicitly recommended for a
 * non-recurring sequence; {@code MathSrand(TimeCurrent())} is explicitly called out as
 * <em>not</em> suitable ("returns the time of the last tick, which can be unchanged for a long
 * time, for example at the weekend") — so {@code TimeCurrent()}/{@code TimeLocal()} must not
 * suppress this warning the way an earlier version did. The check also inspects the seed
 * argument itself (via {@link StatementAst#callArgsText}) rather than merely whether
 * {@code GetTickCount} is called anywhere in the function, so an unrelated {@code GetTickCount()}
 * call elsewhere in the body can no longer mask a bad seed.
 */
public class DeterministicSeedInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "MathSrand() not seeded with GetTickCount() — hardcoded/TimeCurrent()/TimeLocal() seeds are not suitable for non-deterministic randomness";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode call = StatementAst.findCall(body, "MathSrand");
                if (call != null) {
                    String seedArg = StatementAst.callArgsText(call);
                    boolean seededWithTickCount = seedArg != null && seedArg.contains("GetTickCount");
                    if (!seededWithTickCount) {
                        problems.add(createWeakWarning(manager, StatementAst.anchor(call, child.getNavigationElement()), MESSAGE));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
