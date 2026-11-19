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
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class DataConsistencyInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Price comparison without NormalizeDouble() — floating point precision issues";
    private static final Set<String> PRICE_FUNCS = Set.of("Ask", "Bid", "SymbolInfoDouble", "OrderOpenPrice", "PositionGetDouble");
    private static final TokenSet EQUALITY = TokenSet.create(MQL4Elements.EQ_EQ, MQL4Elements.NOT_EQ);
    /** Tokens that end an operand of {@code ==} at the operator's level. */
    private static final TokenSet OPERAND_END = TokenSet.create(MQL4Elements.BOOL_AND, MQL4Elements.BOOL_OR, MQL4Elements.COMMA,
            MQL4Elements.SEMICOLON, MQL4Elements.L_ROUND_BRACKET, MQL4Elements.R_ROUND_BRACKET, MQL4Elements.EQ,
            MQL4Elements.QUESTION, MQL4Elements.COLON, MQL4Elements.RETURN_KEYWORD, MQL4Elements.EQ_EQ, MQL4Elements.NOT_EQ);

    /**
     * Reports {@code ==} / {@code !=} between a price ({@code Ask}, {@code Bid}, a price getter, or a
     * variable assigned from one) and anything but zero, with no {@code NormalizeDouble} on either
     * side. Ordering ({@code <}, {@code >}) is fine, and so is {@code price == 0.0}: zero is exact.
     */
    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                Set<String> prices = priceVariables(body);
                ASTNode[] found = {null};
                StatementAst.forEachDescendant(body, EQUALITY, op -> {
                    if (found[0] != null) return;
                    List<ASTNode> left = operand(op, false);
                    List<ASTNode> right = operand(op, true);
                    boolean price = isPrice(left, prices) || isPrice(right, prices);
                    if (price && !isZero(left) && !isZero(right) && !mentions(left, "NormalizeDouble") && !mentions(right, "NormalizeDouble")) {
                        found[0] = op;
                    }
                });
                if (found[0] != null) {
                    problems.add(createWeakWarning(manager, StatementAst.anchor(found[0], child.getNavigationElement()), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** Names assigned or initialised from a price: {@code double ask = Ask;}, {@code p = SymbolInfoDouble(...);} */
    private static Set<String> priceVariables(@NotNull ASTNode body) {
        Set<String> names = new HashSet<>();
        StatementAst.forEachDescendant(body, TokenSet.create(MQL4Elements.EQ), eq -> {
            ASTNode target = StatementAst.prevNonTrivia(eq);
            if (target == null || target.getElementType() != MQL4Elements.IDENTIFIER) return;
            // the tokens up to ';' or ',' -- a declaration's initializer sits after its VAR_DEFINITION, not in it
            List<ASTNode> value = new ArrayList<>();
            for (ASTNode n = nextLeaf(eq); n != null && n.getElementType() != MQL4Elements.SEMICOLON
                    && n.getElementType() != MQL4Elements.COMMA; n = nextLeaf(n)) {
                value.add(n);
            }
            if (isPrice(value, Set.of())) {
                names.add(target.getText());
            }
        });
        return names;
    }

    private static ASTNode nextLeaf(@NotNull ASTNode node) {
        ASTNode n = node;
        while (n != null && n.getTreeNext() == null) n = n.getTreeParent();
        if (n == null) return null;
        n = n.getTreeNext();
        while (n.getFirstChildNode() != null) n = n.getFirstChildNode();
        return n;
    }

    /** The sibling nodes on one side of {@code op}, up to the nearest operand boundary. */
    private static List<ASTNode> operand(@NotNull ASTNode op, boolean forward) {
        List<ASTNode> nodes = new ArrayList<>();
        for (ASTNode n = forward ? op.getTreeNext() : op.getTreePrev(); n != null && !OPERAND_END.contains(n.getElementType());
             n = forward ? n.getTreeNext() : n.getTreePrev()) {
            if (!StatementAst.isTrivia(n)) nodes.add(n);
        }
        return nodes;
    }

    private static boolean isPrice(@NotNull List<ASTNode> nodes, @NotNull Set<String> priceVariables) {
        for (ASTNode node : nodes) {
            if (containsIdentifier(node, id -> PRICE_FUNCS.contains(id) || priceVariables.contains(id))) return true;
        }
        return false;
    }

    private static boolean mentions(@NotNull List<ASTNode> nodes, @NotNull String name) {
        for (ASTNode node : nodes) {
            if (containsIdentifier(node, name::equals)) return true;
        }
        return false;
    }

    private static boolean containsIdentifier(@NotNull ASTNode node, @NotNull java.util.function.Predicate<String> test) {
        if (node.getElementType() == MQL4Elements.IDENTIFIER) return test.test(node.getText());
        for (ASTNode c = node.getFirstChildNode(); c != null; c = c.getTreeNext()) {
            if (containsIdentifier(c, test)) return true;
        }
        return false;
    }

    private static boolean isZero(@NotNull List<ASTNode> nodes) {
        if (nodes.size() != 1) return false;
        ASTNode n = nodes.get(0);
        if (n.getElementType() != MQL4Elements.INTEGER_LITERAL && n.getElementType() != MQL4Elements.DOUBLE_LITERAL) return false;
        try {
            return Double.parseDouble(n.getText().replaceAll("[^0-9.eE+-]", "")) == 0.0;
        } catch (NumberFormatException e) {
            return false;
        }
    }
}
