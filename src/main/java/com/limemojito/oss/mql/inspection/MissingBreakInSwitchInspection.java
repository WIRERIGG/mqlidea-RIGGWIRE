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
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class MissingBreakInSwitchInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Possible unintended switch case fall-through — missing 'break' or 'return' statement";

    private static final Pattern CASE_PATTERN = Pattern.compile("\\bcase\\b|\\bdefault\\s*:");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body != null && hasFallThrough(body)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private boolean hasFallThrough(@NotNull ASTNode body) {
        String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
        if (!Pattern.compile("\\bswitch\\s*\\(").matcher(text).find()) {
            return false;
        }
        Matcher caseMatcher = CASE_PATTERN.matcher(text);
        List<Integer> casePositions = new ArrayList<>();
        while (caseMatcher.find()) {
            casePositions.add(caseMatcher.start());
        }
        if (casePositions.size() < 2) {
            return false;
        }
        for (int i = 0; i < casePositions.size() - 1; i++) {
            int start = casePositions.get(i);
            int end = casePositions.get(i + 1);
            String between = text.substring(start, end);
            if (!between.contains("break;") && !between.contains("break ;")
                    && !Pattern.compile("\\breturn\\b").matcher(between).find()) {
                // Check it is not an intentional empty fallthrough (case X: case Y:)
                String afterColon = between.substring(between.indexOf(':') + 1).trim();
                if (!afterColon.isEmpty()) {
                    return true;
                }
            }
        }
        return false;
    }
}
