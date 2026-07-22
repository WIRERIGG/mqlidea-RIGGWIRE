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
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class EmptyEventHandlerInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Empty event handler '%s()' — consider removing or adding implementation";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && isEventHandler(func)) {
                ASTNode body = findBracketsBlock(child);
                if (body != null && bracketBlockIsEmpty(body)) {
                    String funcName = func.getFunctionName();
                    problems.add(manager.createProblemDescriptor(
                            child.getNavigationElement(), child.getNavigationElement(),
                            String.format(MESSAGE, funcName),
                            ProblemHighlightType.WARNING, true,
                            new InsertTodoInEmptyHandlerFix(funcName)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static class InsertTodoInEmptyHandlerFix implements LocalQuickFix {
        private final String functionName;

        InsertTodoInEmptyHandlerFix(String functionName) {
            this.functionName = functionName;
        }

        @NotNull
        @Override
        public String getName() {
            return "Insert TODO comment in " + functionName + "()";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return "Insert TODO comment in empty handler";
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiElement element = descriptor.getPsiElement();
            if (element == null) return;
            PsiFile file = element.getContainingFile();
            Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
            if (doc == null) return;

            ASTNode node = element.getNode();
            if (node == null) return;
            // Find the BRACKETS_BLOCK within the function element
            ASTNode body = node.findChildByType(com.limemojito.oss.mql.psi.MQL4Elements.BRACKETS_BLOCK);
            if (body == null) return;

            int bodyStart = body.getStartOffset();
            String bodyText = body.getText();
            int bracePos = bodyText.indexOf('{');
            if (bracePos < 0) return;

            int insertOffset = bodyStart + bracePos + 1;
            doc.insertString(insertOffset, "\n   // TODO: Implement " + functionName + "() handler\n");
        }
    }
}
