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

import java.util.Set;
import java.util.function.Consumer;
import java.util.regex.Pattern;

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

    // ------------------------------------------------------------------------------------------
    // Call / identifier / literal primitives (Phase 5: replace the old walker's regex-over-
    // stripped-text scans with real token-level structural checks). A "call" here is a
    // structural fact, not a parsed expression node — the flat statement AST has no call-expression
    // composite — so a call is recognised the same way {@link
    // ReturnValueIgnoredInspection#bareCallName} recognises one: an {@code IDENTIFIER} token whose
    // next non-trivia sibling is a {@code (...)} {@code BRACKETS_BLOCK}. Because these walk real
    // tokens, comment/string-literal text can never masquerade as a call or identifier — the main
    // false-positive source the old text scan (which stripped comments/strings itself) still left on
    // the table was mis-scoping (which loop/function/branch a match belonged to), not lexical noise.
    // ------------------------------------------------------------------------------------------

    /** Next sibling of {@code node} that is not whitespace/comment, or null. */
    @Nullable
    static ASTNode nextNonTrivia(@NotNull ASTNode node) {
        ASTNode sibling = node.getTreeNext();
        while (sibling != null && isTrivia(sibling)) {
            sibling = sibling.getTreeNext();
        }
        return sibling;
    }

    /** Previous sibling of {@code node} that is not whitespace/comment, or null. */
    @Nullable
    static ASTNode prevNonTrivia(@NotNull ASTNode node) {
        ASTNode sibling = node.getTreePrev();
        while (sibling != null && isTrivia(sibling)) {
            sibling = sibling.getTreePrev();
        }
        return sibling;
    }

    /**
     * True when {@code identifier} is an {@code IDENTIFIER} directly followed by a call's
     * {@code (...)} args. Normally that is a nested {@code BRACKETS_BLOCK} (see {@link #isParenBlock}),
     * but the parser has one known gap: a {@code VAR_DECLARATION_STATEMENT} initializer expression
     * (e.g. {@code int h = FileOpen(...);}) is never parsed into an expression tree — its tokens,
     * including any call's parens, are consumed flat as raw siblings with no {@code BRACKETS_BLOCK}
     * wrapper at all. A bare {@code L_ROUND_BRACKET} token sibling is accepted too so a call is still
     * recognised in that position.
     */
    static boolean isCallIdentifier(@NotNull ASTNode identifier) {
        if (identifier.getElementType() != IDENTIFIER) return false;
        ASTNode next = nextNonTrivia(identifier);
        if (next == null) return false;
        return isParenBlock(next) || next.getElementType() == L_ROUND_BRACKET;
    }

    /**
     * The {@code (...)} args block of a call identifier (see {@link #isCallIdentifier}), or null
     * when the call has no properly-nested args block to inspect (the raw-flat-tokens parser gap
     * documented on {@link #isCallIdentifier} — the call is still detected by {@link #hasCall} /
     * {@link #hasAnyCall}, but its individual arguments are not introspectable through this method).
     */
    @Nullable
    static ASTNode callArgsBlock(@NotNull ASTNode callIdentifier) {
        ASTNode next = nextNonTrivia(callIdentifier);
        return next != null && isParenBlock(next) ? next : null;
    }

    /**
     * Depth-first walk over {@code root} invoking {@code onCallIdentifier} with the
     * {@code IDENTIFIER} node of every call whose callee name is in {@code names}. Cancellable.
     */
    static void forEachCall(@Nullable ASTNode root, @NotNull Set<String> names, @NotNull Consumer<ASTNode> onCallIdentifier) {
        if (root == null) return;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && names.contains(child.getText()) && isCallIdentifier(child)) {
                onCallIdentifier.accept(child);
            }
            forEachCall(child, names, onCallIdentifier);
        }
    }

    /** True when {@code root} contains a call to {@code name}. */
    static boolean hasCall(@Nullable ASTNode root, @NotNull String name) {
        return hasAnyCall(root, Set.of(name));
    }

    /** True when {@code root} contains a call to any function in {@code names}. */
    static boolean hasAnyCall(@Nullable ASTNode root, @NotNull Set<String> names) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && names.contains(child.getText()) && isCallIdentifier(child)) {
                return true;
            }
            if (hasAnyCall(child, names)) return true;
        }
        return false;
    }

    /** Number of calls to {@code name} anywhere in {@code root}. */
    static int countCalls(@Nullable ASTNode root, @NotNull String name) {
        if (root == null) return 0;
        int[] count = {0};
        forEachCall(root, Set.of(name), id -> count[0]++);
        return count[0];
    }

    /** True when an {@code IDENTIFIER} token with text {@code name} occurs anywhere in {@code root} (call or bare reference). */
    static boolean hasIdentifier(@Nullable ASTNode root, @NotNull String name) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && name.equals(child.getText())) return true;
            if (hasIdentifier(child, name)) return true;
        }
        return false;
    }

    /** True when an {@code IDENTIFIER} token with text {@code name} occurs at or after {@code offset} in {@code root}. */
    static boolean hasIdentifierAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && name.equals(child.getText())
                    && child.getStartOffset() >= offset) {
                return true;
            }
            if (hasIdentifierAfter(child, name, offset)) return true;
        }
        return false;
    }

    /** True when any {@code STRING_LITERAL} token's (unquoted) content matches {@code pattern}. */
    static boolean anyStringLiteralMatches(@Nullable ASTNode root, @NotNull Pattern pattern) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == STRING_LITERAL) {
                String text = child.getText();
                String content = text.length() >= 2 && text.startsWith("\"") && text.endsWith("\"")
                        ? text.substring(1, text.length() - 1) : text;
                if (pattern.matcher(content).find()) return true;
            }
            if (anyStringLiteralMatches(child, pattern)) return true;
        }
        return false;
    }

    /** True when an {@code EQ_EQ}/{@code NOT_EQ} token is adjacent (either side) to an identifier {@code NULL}. */
    static boolean hasNullComparison(@Nullable ASTNode root) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (t == EQ_EQ || t == NOT_EQ) {
                ASTNode prev = prevNonTrivia(child);
                ASTNode next = nextNonTrivia(child);
                if (isNullToken(prev) || isNullToken(next)) return true;
            }
            if (hasNullComparison(child)) return true;
        }
        return false;
    }

    /**
     * True when an assignment {@code name = NULL} occurs at or after {@code offset} in {@code root}
     * ({@code EQ} token whose previous sibling is identifier {@code name} and next sibling is {@code NULL}).
     */
    static boolean hasNullAssignmentAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == EQ && child.getStartOffset() >= offset) {
                ASTNode prev = prevNonTrivia(child);
                ASTNode next = nextNonTrivia(child);
                if (prev != null && prev.getElementType() == IDENTIFIER && name.equals(prev.getText())
                        && isNullToken(next)) {
                    return true;
                }
            }
            if (hasNullAssignmentAfter(child, name, offset)) return true;
        }
        return false;
    }

    /** True when {@code statement} is exactly {@code <name> = NULL;}. */
    static boolean isNullAssignmentStatement(@Nullable ASTNode statement, @NotNull String name) {
        if (statement == null || statement.getElementType() != EXPRESSION_STATEMENT) return false;
        ASTNode id = statement.getFirstChildNode();
        while (id != null && isTrivia(id)) id = id.getTreeNext();
        if (id == null || id.getElementType() != IDENTIFIER || !name.equals(id.getText())) return false;
        ASTNode eq = nextNonTrivia(id);
        if (eq == null || eq.getElementType() != EQ) return false;
        return isNullToken(nextNonTrivia(eq));
    }

    private static boolean isNullToken(@Nullable ASTNode node) {
        return node != null && node.getElementType() == IDENTIFIER && "NULL".equalsIgnoreCase(node.getText());
    }

    /**
     * If {@code statement} is a bare {@code delete <identifier>;} (not an array-element delete like
     * {@code delete arr[i];}), returns the identifier node; otherwise null.
     */
    @Nullable
    static ASTNode deletedIdentifier(@NotNull ASTNode statement) {
        if (statement.getElementType() != EXPRESSION_STATEMENT) return null;
        ASTNode first = statement.getFirstChildNode();
        while (first != null && isTrivia(first)) first = first.getTreeNext();
        if (first == null || first.getElementType() != DELETE_KEYWORD) return null;
        ASTNode id = nextNonTrivia(first);
        if (id == null || id.getElementType() != IDENTIFIER) return null;
        ASTNode after = nextNonTrivia(id);
        if (after != null && after.getElementType() == L_SQUARE_BRACKET) return null; // delete arr[i];
        return id;
    }

    /**
     * Space-joined text of every non-trivia leaf token under {@code root}, excluding string/char
     * literal content — for coarse keyword-substring heuristics (e.g. "does this body mention
     * 'retry' or 'MAX_DEPTH' anywhere") that aren't naturally a call/identifier/statement shape.
     * Because literal content is excluded, a comment or string mentioning the keyword can no
     * longer produce a false match the way raw-text scanning could.
     */
    @NotNull
    static String heuristicText(@NotNull ASTNode root) {
        StringBuilder sb = new StringBuilder();
        appendHeuristicText(root, sb);
        return sb.toString();
    }

    private static void appendHeuristicText(@NotNull ASTNode node, @NotNull StringBuilder sb) {
        ASTNode child = node.getFirstChildNode();
        if (child == null) {
            IElementType t = node.getElementType();
            if (!isTrivia(node) && t != STRING_LITERAL && t != CHAR_LITERAL) {
                sb.append(node.getText()).append(' ');
            }
            return;
        }
        for (; child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            appendHeuristicText(child, sb);
        }
    }

    /**
     * True when {@code root} contains a comparison shaped like a failure-return check:
     * {@code < 0}, {@code <= 0}, {@code < 1} or {@code == -1} (as adjacent tokens, ignoring
     * whitespace) — or a direct call to {@code GetLastError}. Covers the common
     * "was this negative-on-failure return value checked" idiom (ArrayResize/CopyRates/... all
     * return -1 on failure) without matching these substrings inside unrelated text.
     */
    static boolean hasFailureReturnCheck(@Nullable ASTNode root) {
        if (root == null) return false;
        if (hasCall(root, "GetLastError")) return true;
        return hasFailureReturnCheckToken(root);
    }

    private static boolean hasFailureReturnCheckToken(@NotNull ASTNode root) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (t == LT || t == LESS_EQ) {
                ASTNode next = nextNonTrivia(child);
                if (next != null && next.getElementType() == INTEGER_LITERAL
                        && ("0".equals(next.getText()) || (t == LT && "1".equals(next.getText())))) {
                    return true;
                }
            } else if (t == EQ_EQ) {
                ASTNode next = nextNonTrivia(child);
                if (next != null && next.getElementType() == MINUS) {
                    ASTNode afterMinus = nextNonTrivia(next);
                    if (afterMinus != null && afterMinus.getElementType() == INTEGER_LITERAL
                            && "1".equals(afterMinus.getText())) {
                        return true;
                    }
                }
            }
            if (hasFailureReturnCheckToken(child)) return true;
        }
        return false;
    }

    /** True when an {@code IDENTIFIER} token is directly followed by {@code [} — an array index access. */
    static boolean hasArrayAccess(@Nullable ASTNode root) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER) {
                ASTNode next = nextNonTrivia(child);
                if (next != null && next.getElementType() == L_SQUARE_BRACKET) return true;
            }
            if (hasArrayAccess(child)) return true;
        }
        return false;
    }

    /** True when a {@code PLUS} token is adjacent (either side) to a {@code STRING_LITERAL} — string concatenation. */
    static boolean hasStringConcat(@Nullable ASTNode root) {
        if (root == null) return false;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == PLUS) {
                ASTNode prev = prevNonTrivia(child);
                ASTNode next = nextNonTrivia(child);
                if ((prev != null && prev.getElementType() == STRING_LITERAL)
                        || (next != null && next.getElementType() == STRING_LITERAL)) {
                    return true;
                }
            }
            if (hasStringConcat(child)) return true;
        }
        return false;
    }
}
