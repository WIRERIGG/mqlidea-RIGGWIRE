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
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * String concatenation inside a loop, scoped via the statement AST — but only the genuine
 * self-accumulation antipattern this inspection is meant to catch: a string variable grown across
 * iterations ({@code s += expr;} or {@code s = s + expr;}, the SAME variable on both sides). Every
 * iteration re-copies the whole accumulated buffer, which is the real O(n^2) cost
 * {@code StringConcatenate()}/{@code StringAdd()} avoid.
 * <p>
 * A FRESH per-iteration concat into a brand-new variable — e.g.
 * {@code string last_name = " " + TimeToString(RememberSessionStart[i]);} (MarketProfile.mq5:2050)
 * or {@code string obj_name = ObjectName(ChartID(), j, 0, OBJ_TREND);} and the ~11 similar
 * object-name-building loops across the codebase (LEIlight.mq5, RIGGWIRE_FINAL.mq5, TrendCipher.mq5,
 * RiskManager.mqh, ...) — allocates one string per iteration either way and is NOT the antipattern:
 * the old check (any {@code +} adjacent to a string literal anywhere in the loop body) flagged these
 * fresh-variable declarations too, which was the dominant source of false positives.
 */
public class StringConcatInLoopInspection extends MQL5SafetyInspectionBase implements MQL4Elements {

    private static final String MESSAGE = "String concatenation inside loop — use StringConcatenate() or StringAdd() for better performance";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null || findSelfAccumulatingConcat(loopBody) == null) {
                        return;
                    }
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWeakWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * The assignment operator ({@code +=} or {@code =}) of the first self-accumulating string
     * concatenation found under {@code root}, or null — for anchoring/existence-testing. Matches
     * {@code x += <rhs>;} (a compound add is self-accumulation by construction — {@code x} is read
     * and re-written) and {@code x = x + <rhs>;} (the LHS identifier reappears somewhere on the RHS
     * of its own assignment). Both additionally require a {@code STRING_LITERAL} somewhere in the
     * RHS, to tell string accumulation (the antipattern) apart from ordinary numeric accumulation
     * like {@code total += 1;}, which this inspection's message ("use StringConcatenate()") does not
     * apply to and must not flag.
     */
    @Nullable
    private static ASTNode findSelfAccumulatingConcat(@NotNull ASTNode root) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (t == PLUS_EQ || t == EQ) {
                ASTNode lhs = StatementAst.prevNonTrivia(child);
                if (lhs != null && lhs.getElementType() == IDENTIFIER) {
                    boolean selfAccumulates = (t == PLUS_EQ) || rhsHasIdentifier(child, lhs.getText());
                    if (selfAccumulates && rhsHasStringLiteral(child)) {
                        return child;
                    }
                }
            }
            ASTNode found = findSelfAccumulatingConcat(child);
            if (found != null) return found;
        }
        return null;
    }

    /**
     * True when an {@code IDENTIFIER} token with text {@code name} occurs among the siblings
     * between {@code operator} (exclusive) and the statement-terminating {@code SEMICOLON} —
     * i.e. on the right-hand side of the assignment {@code operator} belongs to.
     */
    private static boolean rhsHasIdentifier(@NotNull ASTNode operator, @NotNull String name) {
        for (ASTNode sib = operator.getTreeNext(); sib != null && sib.getElementType() != SEMICOLON; sib = sib.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (containsIdentifier(sib, name)) return true;
        }
        return false;
    }

    private static boolean containsIdentifier(@NotNull ASTNode node, @NotNull String name) {
        if (node.getElementType() == IDENTIFIER && name.equals(node.getText())) return true;
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (containsIdentifier(child, name)) return true;
        }
        return false;
    }

    /**
     * True when a {@code STRING_LITERAL} token occurs among the siblings between {@code operator}
     * (exclusive) and the statement-terminating {@code SEMICOLON}.
     */
    private static boolean rhsHasStringLiteral(@NotNull ASTNode operator) {
        for (ASTNode sib = operator.getTreeNext(); sib != null && sib.getElementType() != SEMICOLON; sib = sib.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (containsStringLiteral(sib)) return true;
        }
        return false;
    }

    private static boolean containsStringLiteral(@NotNull ASTNode node) {
        if (node.getElementType() == STRING_LITERAL) return true;
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (containsStringLiteral(child)) return true;
        }
        return false;
    }
}
