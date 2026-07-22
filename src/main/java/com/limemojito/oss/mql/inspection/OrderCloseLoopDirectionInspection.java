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

/**
 * MQL4-only. Flags a forward (ascending) loop over OrdersTotal() that closes
 * or deletes orders inside — the order pool re-indexes after each close, so a
 * forward loop skips every other order. Iterate downward instead.
 */
public class OrderCloseLoopDirectionInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Closing/deleting orders in a forward OrdersTotal() loop skips orders — iterate downward (for(i=OrdersTotal()-1; i>=0; i--))";

    /**
     * Matches an ascending for-header over OrdersTotal(): initialised to 0,
     * bounded with {@code < OrdersTotal()} and incremented with {@code ++}.
     * Descending loops ({@code i >= 0; i--}) do not match.
     */
    private static final Pattern FORWARD_ORDERS_LOOP = Pattern.compile(
            "\\bfor\\s*\\(\\s*[^;]*=\\s*0\\s*;[^;]*<\\s*OrdersTotal\\s*\\(\\s*\\)[^;]*;[^)]*\\+\\+\\s*\\)");

    private static final Pattern CLOSE_OR_DELETE = Pattern.compile("\\b(?:OrderClose|OrderDelete)\\s*\\(");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql5Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                if (hasForwardCloseLoop(text)) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean hasForwardCloseLoop(@NotNull String text) {
        Matcher m = FORWARD_ORDERS_LOOP.matcher(text);
        while (m.find()) {
            ProgressManager.checkCanceled();
            String loopBody = extractLoopBody(text, m.end());
            if (CLOSE_OR_DELETE.matcher(loopBody).find()) {
                return true;
            }
        }
        return false;
    }

    /**
     * Returns the loop body starting after the for-header: a balanced brace
     * block if one follows, a single statement up to the next {@code ;}
     * otherwise. Falls back to the remaining text when braces are unbalanced.
     */
    @NotNull
    private static String extractLoopBody(@NotNull String text, int afterHeader) {
        int i = afterHeader;
        while (i < text.length() && Character.isWhitespace(text.charAt(i))) i++;
        if (i >= text.length()) return "";
        if (text.charAt(i) == '{') {
            int end = findMatchingBrace(text, i);
            return end >= 0 ? text.substring(i, end + 1) : text.substring(i);
        }
        int semi = text.indexOf(';', i);
        return semi >= 0 ? text.substring(i, semi + 1) : text.substring(i);
    }

    private static int findMatchingBrace(@NotNull String text, int openPos) {
        int depth = 0;
        for (int i = openPos; i < text.length(); i++) {
            char c = text.charAt(i);
            if (c == '{') depth++;
            else if (c == '}') {
                depth--;
                if (depth == 0) return i;
            }
        }
        return -1;
    }
}
