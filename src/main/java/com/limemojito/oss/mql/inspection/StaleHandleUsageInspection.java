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
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class StaleHandleUsageInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Handle released then reused without reassignment — potential use-after-free";
    private static final Pattern RELEASE_PATTERN = Pattern.compile("IndicatorRelease\\s*\\(\\s*(\\w+)\\s*\\)");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                Matcher m = RELEASE_PATTERN.matcher(text);
                while (m.find()) {
                    String handle = m.group(1);
                    String remaining = text.substring(m.end());
                    Pattern reusePattern = Pattern.compile(
                            "CopyBuffer\\s*\\([^)]*\\b" + Pattern.quote(handle) + "\\b");
                    if (reusePattern.matcher(remaining).find()) {
                        problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                        break;
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
