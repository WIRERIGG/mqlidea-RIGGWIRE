/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingPropertyVersionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Missing '#property version' — add a version for the script/indicator/EA";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        String fileName = file.getName().toLowerCase();
        if (fileName.endsWith(".mq5") || fileName.endsWith(".mq4")) {
            if (!hasPreprocessorProperty(file, "version")) {
                problems.add(manager.createProblemDescriptor(file, file, MESSAGE,
                        ProblemHighlightType.WEAK_WARNING, true, new InsertPropertyVersionFix()));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static class InsertPropertyVersionFix implements LocalQuickFix {
        @NotNull
        @Override
        public String getName() {
            return "Insert #property version";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return getName();
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiFile file = descriptor.getPsiElement().getContainingFile();
            Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
            if (doc == null) return;
            doc.insertString(0, "#property version \"1.00\"\n");
        }
    }
}
