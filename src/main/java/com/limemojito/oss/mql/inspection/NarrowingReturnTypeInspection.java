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
import com.intellij.psi.tree.IElementType;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Flags an integer-returning function that returns a floating-point literal — a genuine narrowing
 * (truncation) conversion. The previous heuristic correlated a {@code double} <em>parameter</em> with
 * an integer return type, which is a fabricated relationship: {@code int f(double x)} (rounding/quantizing
 * helpers, comparators) is idiomatic, lossless MQL5. Nothing is narrowed by a function choosing to return
 * an int, so that rule produced only false positives. This detects the real case: {@code return 3.7;}
 * from an int-returning function silently truncates.
 */
public class NarrowingReturnTypeInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Function '%s' returns an integer type but returns a floating-point value — precision loss (truncation)";
    // Compare IElementType directly — the old String compare against getElementType().toString() never
    // matched the real debug-name, so this inspection silently never fired.
    private static final Set<IElementType> INTEGER_TYPES = Set.of(
            MQL4Elements.INT_KEYWORD, MQL4Elements.LONG_KEYWORD, MQL4Elements.SHORT_KEYWORD,
            MQL4Elements.CHAR_KEYWORD, MQL4Elements.UINT_KEYWORD, MQL4Elements.ULONG_KEYWORD,
            MQL4Elements.USHORT_KEYWORD, MQL4Elements.UCHAR_KEYWORD);
    // A `return` whose expression contains a floating-point literal (1.0, .5, 2.) before the statement
    // end. The (?<![\w.]) lookbehind stops the digit-dot of member access on a digit-suffixed identifier
    // (e.g. `return obj1.value;` — the `1.` there) from matching as a literal (Fable review, bug #2).
    private static final Pattern RETURN_FLOAT_LITERAL =
            Pattern.compile("\\breturn\\b[^;]*?(?<![\\w.])(?:\\d+\\.\\d*|\\.\\d+)");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode returnType = getReturnTypeNode(func);
                if (returnType == null) continue;
                if (!INTEGER_TYPES.contains(returnType.getElementType())) continue;

                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                if (RETURN_FLOAT_LITERAL.matcher(text).find()) {
                    problems.add(createWarning(manager, child.getNavigationElement(),
                            String.format(MESSAGE, func.getFunctionName())));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
