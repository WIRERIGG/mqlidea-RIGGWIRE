/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingFunctionDocCommentInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Public function '%s()' lacks a documentation comment";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                String name = func.getFunctionName();
                if (name.startsWith("~") || name.equals(MQL4FunctionElement.UNKNOWN_NAME)) continue;
                ASTNode prevDirect = func.getNode().getTreePrev();
                boolean hasComment = false;
                while (prevDirect != null) {
                    if (prevDirect.getElementType() == MQL4Elements.BLOCK_COMMENT
                            || prevDirect.getElementType() == MQL4Elements.LINE_COMMENT) {
                        hasComment = true;
                        break;
                    }
                    if (!MQL4TokenSets.COMMENTS_OR_WS.contains(prevDirect.getElementType())) {
                        break;
                    }
                    prevDirect = prevDirect.getTreePrev();
                }
                if (!hasComment) {
                    problems.add(manager.createProblemDescriptor(child.getNavigationElement(),
                            child.getNavigationElement(),
                            String.format(MESSAGE, name),
                            ProblemHighlightType.WEAK_WARNING, true,
                            new InsertDocCommentFix(name)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private record InsertDocCommentFix(@NotNull String functionName) implements LocalQuickFix {

        @NotNull
        @Override
        public String getName() {
            return "Insert documentation comment";
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
            Document doc = PsiDocumentManager.getInstance(project).getDocument(element.getContainingFile());
            if (doc == null) return;
            TextRange range = element.getTextRange();
            if (range == null) return;
            int offset = range.getStartOffset();
            String comment = "//+------------------------------------------------------------------+\n" +
                    "//| " + functionName + "                                                |\n" +
                    "//+------------------------------------------------------------------+\n";
            doc.insertString(offset, comment);
        }
    }
}
