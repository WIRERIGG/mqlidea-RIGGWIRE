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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * AST-based detection of {@code switch} statements without a {@code default} case. Each
 * {@code SWITCH_STATEMENT}'s own {@code {...}} body block is inspected for a direct
 * {@code default} label token, so a {@code default} belonging to another switch (or appearing
 * anywhere else in the function) no longer masks the problem.
 */
public class MissingDefaultCaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Switch statement without 'default' case — unhandled values may cause unexpected behavior";

    private static final TokenSet SWITCH_STATEMENTS = TokenSet.create(MQL4Elements.SWITCH_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, SWITCH_STATEMENTS, switchStmt -> {
                    ASTNode switchBody = StatementAst.findCodeBlockChild(switchStmt);
                    // No body block (tolerant parse of malformed switch): nothing to judge.
                    if (switchBody == null) return;
                    if (switchBody.findChildByType(MQL4Elements.DEFAULT_KEYWORD) != null) return;
                    PsiElement psi = switchStmt.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(manager.createProblemDescriptor(
                                psi, psi,
                                MESSAGE, ProblemHighlightType.WARNING, isOnTheFly,
                                new AddDefaultCaseFix()));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static class AddDefaultCaseFix implements LocalQuickFix {
        @NotNull
        @Override
        public String getName() {
            return "Add 'default: break;' case";
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

            ASTNode switchStmt = element.getNode();
            if (switchStmt == null) return;
            ASTNode switchBody = StatementAst.findCodeBlockChild(switchStmt);
            if (switchBody == null) return;
            ASTNode closingBrace = findClosingBrace(switchBody);
            if (closingBrace == null) return;

            doc.insertString(closingBrace.getStartOffset(), "      default:\n         break;\n   ");
        }

        @Nullable
        private static ASTNode findClosingBrace(@NotNull ASTNode codeBlock) {
            // Direct child search: nested braces live inside nested statement nodes.
            for (ASTNode child = codeBlock.getLastChildNode(); child != null; child = child.getTreePrev()) {
                if (child.getElementType() == MQL4Elements.R_CURLY_BRACKET) {
                    return child;
                }
            }
            return null;
        }
    }
}
