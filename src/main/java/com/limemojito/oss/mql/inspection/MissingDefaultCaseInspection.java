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

public class MissingDefaultCaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Switch statement without 'default' case — unhandled values may cause unexpected behavior";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (BracketBlockTokenWalker.containsPattern(body, "\\bswitch\\s*\\(")
                        && !BracketBlockTokenWalker.containsPattern(body, "\\bdefault\\s*:")) {
                    problems.add(manager.createProblemDescriptor(
                            child.getNavigationElement(), child.getNavigationElement(),
                            MESSAGE, ProblemHighlightType.WARNING, true,
                            new AddDefaultCaseFix()));
                }
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

            // Find the switch keyword in the body
            int switchIdx = bodyText.indexOf("switch");
            if (switchIdx < 0) return;

            // Find the opening brace of the switch block (after the parenthesized expression)
            int parenDepth = 0;
            int i = switchIdx + 6;
            // Skip to opening paren
            while (i < bodyText.length() && bodyText.charAt(i) != '(') i++;
            // Skip past the condition
            for (; i < bodyText.length(); i++) {
                if (bodyText.charAt(i) == '(') parenDepth++;
                if (bodyText.charAt(i) == ')') {
                    parenDepth--;
                    if (parenDepth == 0) { i++; break; }
                }
            }
            // Skip whitespace to find the switch body '{'
            while (i < bodyText.length() && Character.isWhitespace(bodyText.charAt(i))) i++;
            if (i >= bodyText.length() || bodyText.charAt(i) != '{') return;

            int switchBraceStart = i;
            // Find matching closing brace
            int braceDepth = 0;
            int closingBrace = -1;
            for (int j = switchBraceStart; j < bodyText.length(); j++) {
                if (bodyText.charAt(j) == '{') braceDepth++;
                if (bodyText.charAt(j) == '}') {
                    braceDepth--;
                    if (braceDepth == 0) {
                        closingBrace = j;
                        break;
                    }
                }
            }
            if (closingBrace < 0) return;

            int insertOffset = bodyStart + closingBrace;
            doc.insertString(insertOffset, "      default:\n         break;\n   ");
        }
    }
}
