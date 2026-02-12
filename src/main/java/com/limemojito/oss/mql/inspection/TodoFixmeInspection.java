/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiFile;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import org.jetbrains.annotations.NotNull;

import java.util.Collection;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class TodoFixmeInspection extends MQL5SafetyInspectionBase {

    private static final Pattern MARKER_PATTERN = Pattern.compile("\\b(TODO|FIXME|HACK|XXX)\\b", Pattern.CASE_INSENSITIVE);
    private static final String MESSAGE = "Contains '%s' marker — address before production deployment";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        Collection<PsiComment> comments = PsiTreeUtil.findChildrenOfType(file, PsiComment.class);
        for (PsiComment comment : comments) {
            ProgressManager.checkCanceled();
            String text = comment.getText();
            Matcher matcher = MARKER_PATTERN.matcher(text);
            if (matcher.find()) {
                String marker = matcher.group(1).toUpperCase();
                problems.add(createWeakWarning(manager, comment,
                        String.format(MESSAGE, marker)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
