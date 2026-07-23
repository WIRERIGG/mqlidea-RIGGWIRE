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

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class DoubleIndicatorReleaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Handle '%s' is released by IndicatorRelease() more than once — potential double-free";
    // Captures the handle-variable argument of each IndicatorRelease(...) call.
    private static final Pattern RELEASE_CALL = Pattern.compile("\\bIndicatorRelease\\s*\\(\\s*([A-Za-z_]\\w*)");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                // Releasing two DIFFERENT handles (the normal multi-indicator OnDeinit pattern) is
                // correct; only the SAME handle variable released more than once is a real double-free.
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                Matcher m = RELEASE_CALL.matcher(text);
                Set<String> seen = new HashSet<>();
                List<String> duplicated = new ArrayList<>();
                while (m.find()) {
                    String handle = m.group(1);
                    if (!seen.add(handle) && !duplicated.contains(handle)) {
                        duplicated.add(handle);
                    }
                }
                for (String handle : duplicated) {
                    problems.add(createProblem(manager, child.getNavigationElement(),
                            String.format(MESSAGE, handle)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
