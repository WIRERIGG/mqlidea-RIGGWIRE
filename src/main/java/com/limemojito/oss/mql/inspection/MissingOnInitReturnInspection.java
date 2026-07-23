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

/**
 * {@code void OnInit()} is a fully valid MQL5 form — the docs define both {@code int OnInit()} and
 * {@code void OnInit()}, and with the void form initialization is always treated as successful
 * (equivalent to {@code INIT_SUCCEEDED}). It is therefore NOT an error. This inspection surfaces only an
 * informational (weak) hint that returning {@code int} lets the handler signal {@code INIT_FAILED} /
 * {@code INIT_PARAMETERS_INCORRECT}. The quick-fix now inserts {@code return(INIT_SUCCEEDED);} when it
 * changes the return type, so it can no longer leave a non-returning {@code int} function that fails to
 * compile (the previous fix rewrote {@code void}→{@code int} without adding a return).
 */
public class MissingOnInitReturnInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "OnInit() returns 'void' (initialization is always reported successful) — "
            + "return 'int' to be able to signal INIT_FAILED / INIT_PARAMETERS_INCORRECT";

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
                            MESSAGE, ProblemHighlightType.WEAK_WARNING, true,
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
            return "Change return type to 'int' and return INIT_SUCCEEDED";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return getName();
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiElement voidKeyword = descriptor.getPsiElement();
            if (voidKeyword == null) return;
            Document doc = PsiDocumentManager.getInstance(project).getDocument(voidKeyword.getContainingFile());
            if (doc == null) return;
            TextRange voidRange = voidKeyword.getTextRange();

            // Insert the return BEFORE rewriting the type: the body's closing brace sits after the `void`
            // token, so applying the later edit first keeps the earlier (type) offset valid.
            PsiElement func = voidKeyword.getParent();
            if (func != null) {
                ASTNode block = func.getNode().findChildByType(MQL4Elements.BRACKETS_BLOCK);
                if (block != null) {
                    String blockText = block.getText();
                    int closeBrace = blockText.lastIndexOf('}');
                    if (closeBrace >= 0 && !blockText.contains("return")) {
                        int insertAt = block.getTextRange().getStartOffset() + closeBrace;
                        doc.insertString(insertAt, "   return(INIT_SUCCEEDED);\n");
                    }
                }
            }
            doc.replaceString(voidRange.getStartOffset(), voidRange.getEndOffset(), "int");
        }
    }
}
