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
 * MQL4-only. Flags OrderSelect() called as a bare statement with its boolean
 * result ignored — order data read afterwards may be stale or invalid.
 */
public class OrderSelectUncheckedInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "OrderSelect() result ignored — check its bool return before reading order data";

    private static final Pattern ORDER_SELECT_CALL = Pattern.compile("\\bOrderSelect\\s*\\(");

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
                if (hasBareOrderSelect(text)) {
                    problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean hasBareOrderSelect(@NotNull String text) {
        Matcher m = ORDER_SELECT_CALL.matcher(text);
        while (m.find()) {
            ProgressManager.checkCanceled();
            if (isStatementPosition(text, m.start())) {
                return true;
            }
        }
        return false;
    }

    /**
     * True when the call at {@code callStart} sits at statement position:
     * not inside parentheses (if/while/for conditions, argument lists) and
     * immediately preceded (ignoring whitespace) by a statement boundary
     * ({@code ;}, <code>{</code>, <code>}</code> or start of the body).
     * This excludes uses such as {@code if(OrderSelect(...))},
     * {@code ok = OrderSelect(...)}, {@code !OrderSelect(...)},
     * {@code return OrderSelect(...)} and {@code && OrderSelect(...)}.
     */
    private static boolean isStatementPosition(@NotNull String text, int callStart) {
        int parenDepth = 0;
        for (int i = 0; i < callStart; i++) {
            char c = text.charAt(i);
            if (c == '(') parenDepth++;
            else if (c == ')') parenDepth--;
        }
        if (parenDepth > 0) return false;
        int q = callStart - 1;
        while (q >= 0 && Character.isWhitespace(text.charAt(q))) q--;
        if (q < 0) return true;
        char prev = text.charAt(q);
        return prev == ';' || prev == '{' || prev == '}';
    }
}
