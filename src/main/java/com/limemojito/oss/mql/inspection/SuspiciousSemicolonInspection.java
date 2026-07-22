/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class SuspiciousSemicolonInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Suspicious semicolon after control statement — likely a logic error (empty body)";

    private static final Pattern CONTROL_STATEMENT_PATTERN = Pattern.compile("\\b(?:if|for|while)\\s*\\(");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (hasSuspiciousSemicolon(body)) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * Finds {@code if}/{@code for}/{@code while} headers whose <em>balanced</em> closing
     * parenthesis is immediately followed by a semicolon (an empty body). Balancing the
     * parentheses avoids false positives on inner calls such as
     * {@code for(i=Foo(); i<n; i++)} where a naive regex stops at the first {@code )}.
     */
    private static boolean hasSuspiciousSemicolon(ASTNode body) {
        if (body == null) return false;
        String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
        Matcher m = CONTROL_STATEMENT_PATTERN.matcher(text);
        while (m.find()) {
            int openParen = m.end() - 1;
            int closeParen = findMatchingParen(text, openParen);
            if (closeParen < 0) continue;
            int i = closeParen + 1;
            while (i < text.length() && Character.isWhitespace(text.charAt(i))) i++;
            if (i < text.length() && text.charAt(i) == ';') {
                return true;
            }
        }
        return false;
    }

    private static int findMatchingParen(String text, int openPos) {
        int depth = 0;
        for (int i = openPos; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '(') depth++;
            else if (c == ')') {
                depth--;
                if (depth == 0) return i;
            }
        }
        return -1;
    }
}
