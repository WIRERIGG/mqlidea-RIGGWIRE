/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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

public class InfiniteLoopRiskInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Potential infinite loop — 'while(true)' or 'for(;;)' without visible 'break' or 'return' statement";

    private static final Pattern INFINITE_LOOP_PATTERN =
            Pattern.compile("\\b(?:while\\s*\\(\\s*(?:true|1)\\s*\\)|for\\s*\\(\\s*;\\s*;\\s*\\))");

    private static final Pattern BREAK_OR_RETURN_PATTERN =
            Pattern.compile("\\b(?:break|return)\\b");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                if (hasInfiniteLoopWithoutBreak(body)) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private boolean hasInfiniteLoopWithoutBreak(@NotNull ASTNode body) {
        String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
        Matcher loopMatcher = INFINITE_LOOP_PATTERN.matcher(text);
        while (loopMatcher.find()) {
            int loopStart = loopMatcher.end();
            int braceStart = text.indexOf('{', loopStart);
            if (braceStart < 0) continue;
            int braceEnd = findMatchingBrace(text, braceStart);
            if (braceEnd < 0) continue;
            String loopBody = text.substring(braceStart + 1, braceEnd);
            if (!BREAK_OR_RETURN_PATTERN.matcher(loopBody).find()) {
                return true;
            }
        }
        return false;
    }

    private static int findMatchingBrace(@NotNull String text, int openPos) {
        int depth = 0;
        for (int i = openPos; i < text.length(); i++) {
            if (text.charAt(i) == '{') depth++;
            else if (text.charAt(i) == '}') {
                depth--;
                if (depth == 0) return i;
            }
        }
        return -1;
    }
}
