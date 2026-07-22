/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.util.TextRange;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingOnInitReturnInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OnInit() should return 'int' (not 'void') to report initialization status";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && "OnInit".equals(func.getFunctionName())
                    && !func.isDeclaration()) {
                ASTNode returnType = getReturnTypeNode(func);
                if (returnType != null && returnType.getElementType() == MQL4Elements.VOID_KEYWORD) {
                    problems.add(manager.createProblemDescriptor(returnType.getPsi(), returnType.getPsi(),
                            MESSAGE, ProblemHighlightType.GENERIC_ERROR_OR_WARNING, true,
                            new ChangeVoidToIntFix()));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static class ChangeVoidToIntFix implements LocalQuickFix {
        @NotNull
        @Override
        public String getName() {
            return "Change return type to 'int'";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return getName();
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiElement element = descriptor.getPsiElement();
            Document doc = PsiDocumentManager.getInstance(project).getDocument(element.getContainingFile());
            if (doc == null) return;
            TextRange range = element.getTextRange();
            doc.replaceString(range.getStartOffset(), range.getEndOffset(), "int");
        }
    }
}
