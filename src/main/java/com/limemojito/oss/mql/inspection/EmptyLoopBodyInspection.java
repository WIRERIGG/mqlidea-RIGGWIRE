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
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class EmptyLoopBodyInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Empty loop body — possible missing implementation";

    private static final String PATTERN = "\\b(for|while)\\s*\\([^)]*\\)\\s*\\{\\s*\\}";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (BracketBlockTokenWalker.containsPattern(body, PATTERN)) {
                    problems.add(manager.createProblemDescriptor(
                            child.getNavigationElement(), child.getNavigationElement(),
                            MESSAGE, ProblemHighlightType.WEAK_WARNING, true,
                            new InsertTodoInEmptyLoopFix()));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static class InsertTodoInEmptyLoopFix implements LocalQuickFix {
        private static final Pattern EMPTY_LOOP = Pattern.compile(
                "\\b(for|while)\\s*\\([^)]*\\)\\s*\\{(\\s*)\\}");

        @NotNull
        @Override
        public String getName() {
            return "Insert TODO comment in empty loop body";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return getName();
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
            ASTNode body = node.findChildByType(com.limemojito.oss.mql.psi.MQL4Elements.BRACKETS_BLOCK);
            if (body == null) return;

            String bodyText = body.getText();
            int bodyStart = body.getStartOffset();

            Matcher m = EMPTY_LOOP.matcher(bodyText);
            if (m.find()) {
                // Insert after the opening '{' of the empty loop
                int braceOffset = bodyText.indexOf('{', m.start());
                if (braceOffset < 0) return;
                int insertOffset = bodyStart + braceOffset + 1;
                doc.insertString(insertOffset, " // TODO: Implement loop body ");
            }
        }
    }
}
