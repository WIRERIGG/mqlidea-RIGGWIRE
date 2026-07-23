/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.function.Consumer;

/**
 * Helpers for querying the statement AST produced by
 * {@code com.limemojito.oss.mql.parser.parsing.statement.StatementParsing} inside function-body
 * {@code BRACKETS_BLOCK} nodes.
 * <p>
 * Structural facts (confirmed empirically against the parser):
 * <ul>
 *   <li>{@code IF/FOR/WHILE_STATEMENT} = keyword, condition {@code BRACKETS_BLOCK} starting with
 *       {@code '('}, then the body statement node as a following sibling.</li>
 *   <li>{@code DO_STATEMENT} = {@code do} keyword, body statement node, {@code while}, condition
 *       block, {@code ';'}.</li>
 *   <li>{@code SWITCH_STATEMENT} = keyword, condition {@code '('} block, body {@code '{'} block;
 *       {@code case}/{@code default} labels are raw tokens directly inside the body block.</li>
 *   <li>A bare call {@code EXPRESSION_STATEMENT} = {@code IDENTIFIER}, args {@code '('} block,
 *       {@code ';'}; assignments carry a top-level assignment-operator token instead.</li>
 * </ul>
 * Both a control statement's condition and a {@code {...}} code block are {@code BRACKETS_BLOCK}
 * nodes — they are distinguished by their first child token ({@code '('} vs {@code '{'}).
 */
final class StatementAst implements MQL4Elements {

    static final TokenSet CONTROL_FLOW_STATEMENTS = TokenSet.create(
            IF_STATEMENT, FOR_STATEMENT, WHILE_STATEMENT, DO_STATEMENT, SWITCH_STATEMENT
    );

    static final TokenSet LOOP_STATEMENTS = TokenSet.create(
            FOR_STATEMENT, WHILE_STATEMENT, DO_STATEMENT
    );

    static final TokenSet CONDITION_STATEMENTS = TokenSet.create(
            IF_STATEMENT, FOR_STATEMENT, WHILE_STATEMENT
    );

    /** Plain and compound assignment operator tokens ('=', '+=', '-=', ...). */
    static final TokenSet ASSIGNMENT_OPERATORS = TokenSet.create(
            EQ, PLUS_EQ, MINUS_EQ, MUL_EQ, DIV_EQ, MOD_EQ,
            AND_EQ, OR_EQ, XOR_EQ, TILDA_EQ, POW_EQ,
            SH_LEFT_EQ, SH_RIGHT_EQ, USH_RIGHT_EQ
    );

    private StatementAst() {
    }

    /** True for a {@code BRACKETS_BLOCK} that is a {@code {...}} code block. */
    static boolean isCodeBlock(@Nullable ASTNode node) {
        if (node == null || node.getElementType() != BRACKETS_BLOCK) return false;
        ASTNode first = node.getFirstChildNode();
        return first != null && first.getElementType() == L_CURLY_BRACKET;
    }

    /** True for a {@code BRACKETS_BLOCK} that is a {@code (...)} group (condition / call args). */
    static boolean isParenBlock(@Nullable ASTNode node) {
        if (node == null || node.getElementType() != BRACKETS_BLOCK) return false;
        ASTNode first = node.getFirstChildNode();
        return first != null && first.getElementType() == L_ROUND_BRACKET;
    }

    /** True for whitespace / line terminator / comment nodes. */
    static boolean isTrivia(@NotNull ASTNode node) {
        return MQL4TokenSets.COMMENTS_OR_WS.contains(node.getElementType());
    }

    /** First direct child {@code (...)} group of a control statement, or null. */
    @Nullable
    static ASTNode findConditionBlock(@NotNull ASTNode controlStatement) {
        for (ASTNode child = controlStatement.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (isParenBlock(child)) {
                return child;
            }
        }
        return null;
    }

    /**
     * Body of an {@code if}/{@code for}/{@code while} statement: the first non-trivia sibling
     * after the condition {@code (...)} block. Null when the condition or body is missing.
     */
    @Nullable
    static ASTNode findBodyAfterCondition(@NotNull ASTNode controlStatement) {
        ASTNode condition = findConditionBlock(controlStatement);
        if (condition == null) return null;
        for (ASTNode sibling = condition.getTreeNext(); sibling != null; sibling = sibling.getTreeNext()) {
            if (!isTrivia(sibling)) {
                return sibling;
            }
        }
        return null;
    }

    /** Body of a {@code do} statement: the first non-trivia child after the {@code do} keyword. */
    @Nullable
    static ASTNode findDoBody(@NotNull ASTNode doStatement) {
        ASTNode keyword = doStatement.findChildByType(DO_KEYWORD);
        if (keyword == null) return null;
        for (ASTNode sibling = keyword.getTreeNext(); sibling != null; sibling = sibling.getTreeNext()) {
            if (isTrivia(sibling)) continue;
            if (sibling.getElementType() == WHILE_KEYWORD) return null; // malformed: no body
            return sibling;
        }
        return null;
    }

    /**
     * Body of a {@code for}/{@code while}/{@code do} loop statement: the statement after the
     * condition {@code (...)} block, or after the {@code do} keyword. May be a {@code {...}}
     * code block or a single statement node. Null when missing (malformed source).
     */
    @Nullable
    static ASTNode findLoopBody(@NotNull ASTNode loop) {
        if (loop.getElementType() == DO_STATEMENT) {
            return findDoBody(loop);
        }
        return findBodyAfterCondition(loop);
    }

    /** First direct child {@code {...}} code block (e.g. a switch statement's body), or null. */
    @Nullable
    static ASTNode findCodeBlockChild(@NotNull ASTNode statement) {
        for (ASTNode child = statement.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (isCodeBlock(child)) {
                return child;
            }
        }
        return null;
    }

    /** True when a {@code {...}} code block contains only its braces, whitespace and comments. */
    static boolean codeBlockIsEmpty(@NotNull ASTNode codeBlock) {
        for (ASTNode child = codeBlock.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType t = child.getElementType();
            if (t == L_CURLY_BRACKET || t == R_CURLY_BRACKET || isTrivia(child)) {
                continue;
            }
            return false;
        }
        return true;
    }

    /**
     * True when the subtree under {@code root} contains a node (composite or token) whose
     * element type is in {@code types}. Early-exiting counterpart of
     * {@link #forEachDescendant}. Cancellable.
     */
    static boolean hasDescendant(@NotNull ASTNode root, @NotNull TokenSet types) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (types.contains(child.getElementType()) || hasDescendant(child, types)) {
                return true;
            }
        }
        return false;
    }

    /**
     * Depth-first walk over all AST descendants of {@code root}, invoking {@code consumer} for
     * every node whose element type is in {@code types}. Cancellable.
     */
    static void forEachDescendant(@NotNull ASTNode root, @NotNull TokenSet types, @NotNull Consumer<ASTNode> consumer) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (types.contains(child.getElementType())) {
                consumer.accept(child);
            }
            forEachDescendant(child, types, consumer);
        }
    }
}
