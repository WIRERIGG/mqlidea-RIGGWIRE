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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.regex.Pattern;

public class ArrayAccessWithoutSizeCheckInspection extends MQL5SafetyInspectionBase implements MQL4Elements {

    private static final String MESSAGE = "Array access without ArraySize() check — risk of out-of-bounds access";

    /** Relational (non-equality) comparison operators — a guard clause bounding an index. */
    private static final TokenSet RELATIONAL_OPERATORS = TokenSet.create(LT, LESS_EQ, GT, GT_EQ);

    /** Parameter-name fragments that suggest "this parameter is an array-size/count bound". */
    private static final Pattern BOUND_NAME_PATTERN =
            Pattern.compile("size|count|len|length|num|total|bars|rates|period", Pattern.CASE_INSENSITIVE);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                ASTNode access = StatementAst.findArrayAccess(body);
                if (access != null && body != null && !isSizeAware(func, body)) {
                    // Anchor the warning at the array access itself, not the whole function header.
                    problems.add(createWarning(manager, StatementAst.anchor(access, child.getNavigationElement()), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    // Signals that the function is already size-aware, so its array indexing is governed by a known
    // bound — don't flag it. Covers explicit size calls (ArraySize/ArrayRange), the OnCalculate size
    // contract (rates_total/prev_calculated), bar-count bounds (Bars/BarsCalculated/iBars), a bound
    // passed in as a PARAMETER alongside the array parameter (e.g. RWTop/RWBottom's
    // `(const double &data[], int currIndex, int order, int arraySize)` — LEIlight.mq5:3935/3957 and
    // the rest of the RWTop/RWBottom family), and any in-body guard comparison against a non-literal
    // bound (`if(currIndex < order || currIndex >= arraySize - order) return false;`, or the
    // `if(s < 0) continue;` sentinel-index idiom — PositionManagement.mqh:270/414/698). This removes
    // the flood of false positives on indicator/pool code that indexes via an explicit bound rather
    // than a literal ArraySize() call at the access site itself.
    private boolean isSizeAware(@NotNull MQL4FunctionElement func, @NotNull ASTNode body) {
        java.util.Set<String> ids = StatementAst.collectIdentifiers(body);
        if (ids.contains("ArraySize") || ids.contains("ArrayRange")
                || ids.contains("ArrayResize") || ids.contains("ArrayInitialize") // establish the size
                || ids.contains("rates_total") || ids.contains("prev_calculated")
                || ids.contains("Bars") || ids.contains("BarsCalculated") || ids.contains("iBars")) {
            return true;
        }
        return hasArrayParamWithBoundCompanion(func) || hasBoundGuardComparison(body);
    }

    /**
     * True when {@code func} has both an array parameter ({@code &name[]}) and a (possibly
     * different) parameter whose name suggests a size/count bound — the array's valid range is
     * established by the caller via that parameter, not by an in-body {@code ArraySize()} call.
     */
    private boolean hasArrayParamWithBoundCompanion(@NotNull MQL4FunctionElement func) {
        boolean hasArrayParam = false;
        boolean hasBoundParam = false;
        for (ASTNode arg : getFunctionArgs(func)) {
            if (arg.findChildByType(L_SQUARE_BRACKET) != null) {
                hasArrayParam = true;
            }
            PsiElement psi = arg.getPsi();
            String name = (psi instanceof MQL4FunctionArgElement argElement) ? argElement.getName() : null;
            if (name != null && BOUND_NAME_PATTERN.matcher(name).find()) {
                hasBoundParam = true;
            }
        }
        return hasArrayParam && hasBoundParam;
    }

    /**
     * True when {@code root} contains a relational comparison ({@code < <= > >=}) with at least one
     * non-literal ({@code IDENTIFIER}) operand — a guard clause bounding some index against a
     * variable (or a sentinel like {@code s < 0}), as opposed to no bound-related check at all.
     * Deliberately loose (either operand, not both): since these are advisory WEAK WARNINGs and the
     * mandate is zero false positives, err toward treating a function that guards ANY index
     * comparison as size-aware, at the cost of also silencing some unrelated comparisons.
     */
    private static boolean hasBoundGuardComparison(@NotNull ASTNode root) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (RELATIONAL_OPERATORS.contains(t)) {
                ASTNode prev = StatementAst.prevNonTrivia(child);
                ASTNode next = StatementAst.nextNonTrivia(child);
                boolean prevIsVar = prev != null && prev.getElementType() == IDENTIFIER;
                boolean nextIsVar = next != null && next.getElementType() == IDENTIFIER;
                if (prevIsVar || nextIsVar) return true;
            }
            if (hasBoundGuardComparison(child)) return true;
        }
        return false;
    }
}
