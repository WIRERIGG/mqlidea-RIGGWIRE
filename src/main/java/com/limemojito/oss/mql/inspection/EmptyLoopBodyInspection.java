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
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * AST-based detection of loops with an empty body: a {@code FOR/WHILE/DO_STATEMENT} whose body
 * node is an {@code EMPTY_STATEMENT} ({@code while(x);}) or a {@code {...}} code block containing
 * only whitespace/comments ({@code for(...){}}).
 */
public class EmptyLoopBodyInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Empty loop body — possible missing implementation";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null || !isEmptyBody(loopBody)) return;
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(manager.createProblemDescriptor(
                                psi, psi,
                                MESSAGE, ProblemHighlightType.WEAK_WARNING, isOnTheFly,
                                new InsertTodoInEmptyLoopFix()));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean isEmptyBody(@NotNull ASTNode body) {
        if (body.getElementType() == MQL4Elements.EMPTY_STATEMENT) {
            return true;
        }
        return StatementAst.isCodeBlock(body) && StatementAst.codeBlockIsEmpty(body);
    }

    private static class InsertTodoInEmptyLoopFix implements LocalQuickFix {

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
            if (element == null || !element.isValid()) return;
            PsiFile file = element.getContainingFile();
            if (file == null) return;
            Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
            if (doc == null) return;

            ASTNode loop = element.getNode();
            if (loop == null) return;
            ASTNode body = StatementAst.findLoopBody(loop);
            // Only the {}-block form has a place to insert a TODO comment.
            if (body == null || !StatementAst.isCodeBlock(body)) return;
            ASTNode openBrace = body.getFirstChildNode();
            if (openBrace == null) return;

            doc.insertString(openBrace.getStartOffset() + 1, " // TODO: Implement loop body ");
        }
    }
}
