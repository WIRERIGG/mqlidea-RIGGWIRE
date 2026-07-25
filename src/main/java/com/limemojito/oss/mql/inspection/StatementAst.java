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

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
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

    /** True for an array-index group — a raw {@code [} token or a {@code [...]} {@code BRACKETS_BLOCK}. */
    static boolean isIndexBlock(@Nullable ASTNode node) {
        if (node == null) return false;
        if (node.getElementType() == L_SQUARE_BRACKET) return true;
        if (node.getElementType() != BRACKETS_BLOCK) return false;
        ASTNode first = node.getFirstChildNode();
        return first != null && first.getElementType() == L_SQUARE_BRACKET;
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
        return findDescendant(root, types) != null;
    }

    /**
     * The first descendant (composite or token) whose element type is in {@code types}, or null —
     * for anchoring a warning at the offending construct. Same traversal as {@link #hasDescendant}.
     */
    @Nullable
    static ASTNode findDescendant(@NotNull ASTNode root, @NotNull TokenSet types) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (types.contains(child.getElementType())) {
                return child;
            }
            ASTNode found = findDescendant(child, types);
            if (found != null) return found;
        }
        return null;
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
        return isCallIdentifierAnyScope(identifier) && !isMemberOrScopedCall(identifier);
    }

    /**
     * Like {@link #isCallIdentifier} but WITHOUT the global-only guard — matches an identifier
     * directly followed by call parens whether it is a global call, a member call
     * ({@code obj.Method(...)}) or a scoped/static call ({@code Class::Method(...)}). Only
     * {@link MagicNumberInspection} uses the member-inclusive matchers built on this, because its
     * target names (Buy/Sell/PositionOpen/...) are CTrade METHOD names that legitimately appear as
     * member calls — the global-only guard would make them permanently unmatchable.
     */
    static boolean isCallIdentifierAnyScope(@NotNull ASTNode identifier) {
        if (identifier.getElementType() != IDENTIFIER) return false;
        ASTNode next = nextNonTrivia(identifier);
        return next != null && (isParenBlock(next) || next.getElementType() == L_ROUND_BRACKET);
    }

    /**
     * True when {@code identifier} is immediately preceded by a {@code .} ({@link #DOT}) or
     * {@code ::} ({@link #COLON_COLON}) token — i.e. it names a member method call
     * ({@code obj.Method(...)}) or a scoped/static method call ({@code CClass::Method(...)}), not
     * a call to a global function. The call-matching primitives ({@link #isCallIdentifier} and
     * everything built on it: {@link #forEachCall}, {@link #findAnyCall}, {@link #findCall},
     * {@link #hasCall}, {@link #hasAnyCall}, {@link #countCalls}) are used throughout the
     * inspections to recognise calls to specific GLOBAL MQL4/MQL5 function names (OrderDelete,
     * FileOpen, IndicatorRelease, ...). Without this guard, {@code obj_Trade.OrderDelete(ticket)}
     * (a CTrade method call) or {@code CClass::SelfSameName(...)} (a static delegation call) would
     * wrongly match a matcher looking for the identically-named global function — the exact false
     * positives Fable found in {@code ModernMQL5IdiomInspection} (RIGGWIRE_FINAL.mq5's
     * {@code obj_Trade.OrderDelete(ticket)} flagged as the deprecated MQL4 global function) and
     * {@code StackOverflowRiskInspection} (TradeOperationWrapper.mqh's
     * {@code return CTradeOperationWrapper::SafeOrderModify(...);} static delegation flagged as
     * infinite self-recursion).
     */
    static boolean isMemberOrScopedCall(@NotNull ASTNode identifier) {
        ASTNode prev = prevNonTrivia(identifier);
        return prev != null && (prev.getElementType() == DOT || prev.getElementType() == COLON_COLON);
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
     * Text of a call's {@code (...)} args, or null if {@code callIdentifier} is not a call. Unlike
     * {@link #callArgsBlock}, this also covers the raw-flat-tokens parser gap it documents (a
     * {@code VAR_DECLARATION_STATEMENT} initializer such as {@code double a = SymbolInfoDouble(_Symbol, SYMBOL_BID);}):
     * when the call's args are not wrapped in a proper {@code BRACKETS_BLOCK}, this walks the raw
     * sibling tokens from the call's own {@code (} to its matching {@code )}, tracking paren depth,
     * and reconstructs the same text a properly nested call would have.
     */
    @Nullable
    static String callArgsText(@NotNull ASTNode callIdentifier) {
        ASTNode next = nextNonTrivia(callIdentifier);
        if (next == null) return null;
        if (isParenBlock(next)) {
            return next.getText();
        }
        if (next.getElementType() != L_ROUND_BRACKET) {
            return null;
        }
        StringBuilder sb = new StringBuilder();
        int depth = 0;
        for (ASTNode sibling = next; sibling != null; sibling = sibling.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = sibling.getElementType();
            if (t == L_ROUND_BRACKET) depth++;
            else if (t == R_ROUND_BRACKET) depth--;
            sb.append(sibling.getText());
            if (depth == 0) break;
        }
        return sb.toString();
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

    /**
     * Like {@link #forEachCall} but ALSO visits member/scoped calls ({@code obj.Method(...)},
     * {@code Class::Method(...)}) — see {@link #isCallIdentifierAnyScope}. Only for matcher names
     * that denote CTrade methods (MagicNumber's Buy/Sell/PositionOpen/...), which the global-only
     * {@link #forEachCall} cannot reach.
     */
    static void forEachCallIncludingMembers(@Nullable ASTNode root, @NotNull Set<String> names, @NotNull Consumer<ASTNode> onCallIdentifier) {
        if (root == null) return;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && names.contains(child.getText()) && isCallIdentifierAnyScope(child)) {
                onCallIdentifier.accept(child);
            }
            forEachCallIncludingMembers(child, names, onCallIdentifier);
        }
    }

    /** True when {@code root} contains a call to {@code name}. */
    static boolean hasCall(@Nullable ASTNode root, @NotNull String name) {
        return findAnyCall(root, Set.of(name)) != null;
    }

    /** True when {@code root} contains a call to any function in {@code names}. */
    static boolean hasAnyCall(@Nullable ASTNode root, @NotNull Set<String> names) {
        return findAnyCall(root, names) != null;
    }

    /** The {@code IDENTIFIER} node of the first call to {@code name}, or null — for anchoring a warning at the call site. */
    @Nullable
    static ASTNode findCall(@Nullable ASTNode root, @NotNull String name) {
        return findAnyCall(root, Set.of(name));
    }

    /** The {@code IDENTIFIER} node of the first call to any function in {@code names}, or null. */
    @Nullable
    static ASTNode findAnyCall(@Nullable ASTNode root, @NotNull Set<String> names) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && names.contains(child.getText()) && isCallIdentifier(child)) {
                return child;
            }
            ASTNode found = findAnyCall(child, names);
            if (found != null) return found;
        }
        return null;
    }

    /** Number of calls to {@code name} anywhere in {@code root}. */
    static int countCalls(@Nullable ASTNode root, @NotNull String name) {
        if (root == null) return 0;
        int[] count = {0};
        forEachCall(root, Set.of(name), id -> count[0]++);
        return count[0];
    }

    /**
     * All {@code IDENTIFIER} token texts occurring anywhere in {@code root}, collected in ONE walk —
     * for callers that would otherwise call {@link #hasIdentifier} once per candidate name (e.g. one
     * body walk per function parameter). Test membership with {@code Set.contains} afterward.
     */
    @NotNull
    static Set<String> collectIdentifiers(@Nullable ASTNode root) {
        Set<String> names = new HashSet<>();
        collectIdentifiersInto(root, names);
        return names;
    }

    private static void collectIdentifiersInto(@Nullable ASTNode root, @NotNull Set<String> out) {
        if (root == null) return;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER) {
                out.add(child.getText());
            }
            collectIdentifiersInto(child, out);
        }
    }

    /** True when an {@code IDENTIFIER} token with text {@code name} occurs anywhere in {@code root} (call or bare reference). */
    static boolean hasIdentifier(@Nullable ASTNode root, @NotNull String name) {
        return findIdentifier(root, name) != null;
    }

    /** The first {@code IDENTIFIER} token with text {@code name} anywhere in {@code root}, or null — for anchoring. */
    @Nullable
    static ASTNode findIdentifier(@Nullable ASTNode root, @NotNull String name) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && name.equals(child.getText())) return child;
            ASTNode found = findIdentifier(child, name);
            if (found != null) return found;
        }
        return null;
    }

    /** True when an {@code IDENTIFIER} token with text {@code name} occurs at or after {@code offset} in {@code root}. */
    static boolean hasIdentifierAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        return findIdentifierAfter(root, name, offset) != null;
    }

    /**
     * The first {@code IDENTIFIER} token with text {@code name} occurring at or after {@code offset}
     * in {@code root}, or null — for anchoring a warning at the actual (e.g. post-delete) use site.
     */
    @Nullable
    static ASTNode findIdentifierAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && name.equals(child.getText())
                    && child.getStartOffset() >= offset) {
                return child;
            }
            ASTNode found = findIdentifierAfter(child, name, offset);
            if (found != null) return found;
        }
        return null;
    }

    /** True when any {@code STRING_LITERAL} token's (unquoted) content matches {@code pattern}. */
    static boolean anyStringLiteralMatches(@Nullable ASTNode root, @NotNull Pattern pattern) {
        return findStringLiteralMatch(root, pattern) != null;
    }

    /** The first {@code STRING_LITERAL} token node whose (unquoted) content matches {@code pattern}, or null — for anchoring. */
    @Nullable
    static ASTNode findStringLiteralMatch(@Nullable ASTNode root, @NotNull Pattern pattern) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == STRING_LITERAL) {
                String text = child.getText();
                String content = text.length() >= 2 && text.startsWith("\"") && text.endsWith("\"")
                        ? text.substring(1, text.length() - 1) : text;
                if (pattern.matcher(content).find()) return child;
            }
            ASTNode found = findStringLiteralMatch(child, pattern);
            if (found != null) return found;
        }
        return null;
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
     * True when an assignment {@code name = <anything>} occurs at or after {@code offset} in
     * {@code root} ({@code EQ} token whose previous sibling is identifier {@code name}). Covers the
     * delete-then-recreate idiom ({@code delete obj; obj = new CFoo();}) as well as the narrower
     * {@code obj = NULL;} guard — any reassignment ends the "dangling pointer" window, not just a
     * literal NULL.
     */
    static boolean hasAssignmentAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        return findAssignmentAfter(root, name, offset) != null;
    }

    /**
     * The {@code EQ} token of the first assignment {@code name = <anything>} occurring at or after
     * {@code offset} in {@code root}, or null. The assignment's left-hand identifier is
     * {@link #prevNonTrivia} of the returned node.
     */
    @Nullable
    static ASTNode findAssignmentAfter(@Nullable ASTNode root, @NotNull String name, int offset) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == EQ && child.getStartOffset() >= offset) {
                ASTNode prev = prevNonTrivia(child);
                if (prev != null && prev.getElementType() == IDENTIFIER && name.equals(prev.getText())) {
                    return child;
                }
            }
            ASTNode found = findAssignmentAfter(child, name, offset);
            if (found != null) return found;
        }
        return null;
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
        if (isIndexBlock(after)) return null; // delete arr[i]; — [i] is a raw token OR a wrapped BRACKETS_BLOCK
        return id;
    }

    /**
     * Stricter form of {@link #deletedIdentifier} for callers (quick fixes) that must be certain
     * the deleted pointer is a single plain variable — not just excluding the {@code [} case
     * {@link #deletedIdentifier} already excludes, but requiring the identifier be directly
     * followed by the statement's closing {@code ';'} with nothing else in between. This also
     * covers {@code delete arr[i];}, whose {@code [i]} is parsed as a nested {@code BRACKETS_BLOCK}
     * sibling (not the raw {@code L_SQUARE_BRACKET} token {@link #deletedIdentifier} checks for),
     * so that exclusion alone does not actually fire for it.
     */
    @Nullable
    static ASTNode bareDeletedIdentifier(@NotNull ASTNode statement) {
        ASTNode id = deletedIdentifier(statement);
        if (id == null) return null;
        ASTNode after = nextNonTrivia(id);
        return (after != null && after.getElementType() == SEMICOLON) ? id : null;
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

    /** Comparison operator tokens that indicate a value is being range/failure-tested. */
    private static final TokenSet FAILURE_COMPARISON_OPERATORS = TokenSet.create(LT, LESS_EQ, GT, GT_EQ, EQ_EQ, NOT_EQ);

    /**
     * True when {@code root} contains a comparison shaped like a failure-return check:
     * {@code < 0}, {@code <= 0}, {@code < 1}, {@code == -1} or {@code != -1} (as adjacent tokens,
     * ignoring whitespace), or a direct call to {@code GetLastError}. Covers the common
     * "was this negative-on-failure return value checked" idiom (ArrayResize/CopyRates/... all
     * return -1 on failure) without matching these substrings inside unrelated text.
     * <p>
     * NOTE: this deliberately does NOT accept an arbitrary {@code <}/{@code ==} against a variable
     * (e.g. a {@code for(i=0; i<n; i++)} loop counter) — doing so at whole-function scope silences
     * a genuinely-unchecked call whenever any unrelated loop is present. The count-comparison idiom
     * {@code if(CopyBuffer(...) < count)}, where the CALL itself is the operand, is handled per-call
     * by {@link #callResultCompared} instead of here.
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
            } else if (t == EQ_EQ || t == NOT_EQ) {
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

    /**
     * True when the value of the call whose callee-identifier is {@code callIdentifier} is directly
     * an operand of a comparison — i.e. a comparison operator ({@code < <= > >= == !=}) immediately
     * precedes the call or immediately follows the call's closing {@code )}. This is the
     * count-comparison failure-check idiom {@code if(CopyBuffer(...) < count)} /
     * {@code if(ArrayResize(a, n) != n)}, scoped to THIS call so an unrelated loop comparison
     * elsewhere in the function can never mask it. Handles the raw-flat-tokens parser gap (args
     * not wrapped in a {@code BRACKETS_BLOCK}) by walking to the matching {@code )} at paren depth 0.
     */
    static boolean callResultCompared(@Nullable ASTNode callIdentifier) {
        if (callIdentifier == null) return false;
        ASTNode before = prevNonTrivia(callIdentifier);
        if (before != null && FAILURE_COMPARISON_OPERATORS.contains(before.getElementType())) {
            return true;
        }
        ASTNode next = nextNonTrivia(callIdentifier);
        if (next == null) return false;
        ASTNode afterCall;
        if (isParenBlock(next)) {
            afterCall = nextNonTrivia(next);
        } else if (next.getElementType() == L_ROUND_BRACKET) {
            afterCall = tokenAfterMatchingParen(next);
        } else {
            return false;
        }
        return afterCall != null && FAILURE_COMPARISON_OPERATORS.contains(afterCall.getElementType());
    }

    /**
     * The {@code index}-th (0-based) top-level argument text of a call, or null. Splits the call's
     * {@code (...)} args on depth-0 commas, so nested calls/index-groups don't confuse the split
     * ({@code ArrayResize(a, MathMax(x, y))} → arg 1 is {@code MathMax(x, y)}).
     */
    @Nullable
    static String nthCallArg(@NotNull ASTNode callIdentifier, int index) {
        String args = callArgsText(callIdentifier);
        if (args == null || args.length() < 2) return null;
        String inner = args.substring(1, args.length() - 1); // strip the surrounding ( )
        int depth = 0, start = 0, cur = 0;
        for (int i = 0; i < inner.length(); i++) {
            char c = inner.charAt(i);
            if (c == '(' || c == '[') depth++;
            else if (c == ')' || c == ']') depth--;
            else if (c == ',' && depth == 0) {
                if (cur == index) return inner.substring(start, i);
                cur++;
                start = i + 1;
            }
        }
        return cur == index ? inner.substring(start) : null;
    }

    /**
     * True when an {@code ArrayResize} call provably cannot return {@code -1}, so its return needs no
     * check: the new size is the literal {@code 0} (clearing) or a shrink derived from an array's own
     * length ({@code ArraySize(...) - ...}) — neither triggers a physical reallocation. Growing to a
     * fixed/computed size is NOT covered (it can fail on OOM) and remains flaggable.
     */
    static boolean arrayResizeCannotFail(@NotNull ASTNode callIdentifier) {
        String sizeArg = nthCallArg(callIdentifier, 1);
        if (sizeArg == null) return false;
        sizeArg = sizeArg.trim();
        if ("0".equals(sizeArg)) return true;                              // resize to 0 — clear
        // Shrink/same-size of THE ARRAY BEING RESIZED: `ArraySize(<thatArray>)` optionally followed
        // by a subtraction. Requiring the SAME array and rejecting growth operators (*, +, <<) avoids
        // treating a grow as non-failing — e.g. `ArrayResize(dst, ArraySize(src) - 1)` where src is
        // larger, or `ArrayResize(a, ArraySize(a) * 4 - 1)`, both of which can reallocate and fail.
        String arrayArg = nthCallArg(callIdentifier, 0);
        if (arrayArg == null) return false;
        String prefix = "ArraySize(" + arrayArg.trim() + ")";
        if (!sizeArg.startsWith(prefix)) return false;
        String rest = sizeArg.substring(prefix.length()).trim();
        return rest.isEmpty()                                             // resize to current size
                || (rest.charAt(0) == '-' && rest.indexOf('*') < 0 && rest.indexOf('+') < 0 && rest.indexOf('<') < 0);
    }

    /** The first non-trivia sibling after the {@code )} matching {@code lParen}, tracking depth; or null. */
    @Nullable
    private static ASTNode tokenAfterMatchingParen(@NotNull ASTNode lParen) {
        int depth = 0;
        for (ASTNode sib = lParen; sib != null; sib = sib.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = sib.getElementType();
            if (t == L_ROUND_BRACKET) {
                depth++;
            } else if (t == R_ROUND_BRACKET && --depth == 0) {
                return nextNonTrivia(sib);
            }
        }
        return null;
    }

    /**
     * True when a copy/resize {@code call}'s return value is validated in {@code body} by any of the
     * three legitimate MQL idioms: a literal failure check ({@code <0}/{@code ==-1}/GetLastError —
     * {@link #hasFailureReturnCheck}); the call compared inline ({@code if(CopyBuffer(...) < count)}
     * — {@link #callResultCompared}); OR — the common case — the result captured into a variable
     * that is compared somewhere in the function ({@code int n = CopyBuffer(...); if(n < rates_total)}).
     * The third idiom is why these inspections must not treat a captured-then-checked call as unchecked.
     */
    static boolean callReturnChecked(@Nullable ASTNode body, @NotNull ASTNode callIdentifier) {
        // Per-call only. Deliberately NOT the whole-body hasFailureReturnCheck: at whole-function
        // scope a single `if(other < 0)` (or a stray GetLastError) elsewhere would mask a genuinely
        // unchecked sibling resize/copy. The inline form `if(CopyBuffer(...) < n)` is caught by
        // callResultCompared, and the captured form `int r = CopyBuffer(...); if(r < n)` by the
        // result-variable comparison below — together they cover the real check idioms without the
        // false negatives whole-body scoping introduces.
        if (callResultCompared(callIdentifier)) {
            return true;
        }
        String resultVar = assignmentTargetName(callIdentifier);
        return resultVar != null
                && capturedResultCompared(body, resultVar, callIdentifier.getStartOffset());
    }

    /**
     * True when the captured copy/resize result variable {@code name} is genuinely compared in
     * {@code body} — an {@code IDENTIFIER} token named {@code name} is an immediate operand of a
     * comparison ({@code < <= > >= == !=}), e.g. {@code copied < rates_total}, {@code n >= 1},
     * {@code r == -1} — with SHADOWING awareness (review finding #4): a comparison of a
     * <em>different, shadowing</em> variable of the same name must not count as a check of the
     * captured result. In {@code int i = CopyBuffer(...); for(int i = 0; i < 10; i++) ...} the
     * {@code i < 10} operand is the loop's own freshly-declared {@code i}, not the copy result —
     * a bare name-match would silently pass the genuinely-unchecked copy.
     * <p>
     * Rule (no symbol table needed, zero-false-positive by construction):
     * <ul>
     *   <li>A comparison at or before {@code captureOffset} is accepted as before (the retry-loop
     *       idiom {@code while(copied < needed) { copied = CopyBuffer(...); }} — unchanged
     *       behavior, so no previously-clean code starts being flagged).</li>
     *   <li>A comparison after the capture is accepted only when NO declaration of {@code name}
     *       lies between the capture and that comparison. With no intervening redeclaration the
     *       compared name can only denote the captured variable, so acceptance is sound; with one,
     *       the comparison (e.g. the shadowing {@code for}'s own {@code i < 10}) is distrusted.
     *       A genuine check BEFORE a later redeclaration (e.g. {@code int n = CopyBuffer(...);
     *       if(n < total) return; ... for(int n = 0; ...)}) still lies inside the clean window and
     *       stays accepted — more precise than distrusting every redeclared name outright.</li>
     * </ul>
     * Declarations are recognised structurally in both parse shapes (see {@link #isDeclarationOf}),
     * including the flat-token {@code for(int i = 0; ...)} header, which the parser never wraps in
     * a {@code VAR_DEFINITION}.
     */
    static boolean capturedResultCompared(@Nullable ASTNode body, @NotNull String name, int captureOffset) {
        if (body == null) return false;
        List<ASTNode> compared = new ArrayList<>();
        collectComparedOperands(body, name, compared);
        if (compared.isEmpty()) return false;
        List<ASTNode> declarations = new ArrayList<>();
        collectDeclarations(body, name, declarations);
        for (ASTNode operand : compared) {
            int comparisonOffset = operand.getStartOffset();
            if (comparisonOffset <= captureOffset) {
                return true; // pre-capture comparison (retry-loop idiom) — accepted as before
            }
            boolean shadowed = false;
            for (ASTNode declaration : declarations) {
                int declarationOffset = declaration.getStartOffset();
                if (declarationOffset > captureOffset && declarationOffset <= comparisonOffset) {
                    shadowed = true; // redeclared between capture and comparison — different variable
                    break;
                }
            }
            if (!shadowed) return true;
        }
        return false;
    }

    /** Collects every {@code IDENTIFIER} token named {@code name} that is an immediate operand of a comparison. */
    private static void collectComparedOperands(@NotNull ASTNode root, @NotNull String name, @NotNull List<ASTNode> out) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (FAILURE_COMPARISON_OPERATORS.contains(child.getElementType())) {
                ASTNode prev = prevNonTrivia(child);
                ASTNode next = nextNonTrivia(child);
                if (prev != null && prev.getElementType() == IDENTIFIER && name.equals(prev.getText())) {
                    out.add(prev);
                }
                if (next != null && next.getElementType() == IDENTIFIER && name.equals(next.getText())) {
                    out.add(next);
                }
            }
            collectComparedOperands(child, name, out);
        }
    }

    /** Collects every {@code IDENTIFIER} token that is a DECLARATION of {@code name} (see {@link #isDeclarationOf}). */
    private static void collectDeclarations(@NotNull ASTNode root, @NotNull String name, @NotNull List<ASTNode> out) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER && name.equals(child.getText()) && isDeclarationOf(child)) {
                out.add(child);
            }
            collectDeclarations(child, name, out);
        }
    }

    /**
     * True when this {@code IDENTIFIER} token is the declared NAME of a variable declaration, in
     * either parse shape the statement AST produces:
     * <ul>
     *   <li>its parent is a {@code VAR_DEFINITION} — the {@code int x = ...;} / {@code int x;}
     *       statement form ({@code VAR_DECLARATION_STATEMENT > VAR_DEFINITION_LIST >
     *       VAR_DEFINITION{IDENTIFIER, EQ}}); or</li>
     *   <li>its previous non-trivia sibling is a data-type keyword token ({@code int}/{@code double}
     *       /...) — the flat-token form inside a {@code for(int i = 0; ...)} header (a {@code (...)}
     *       {@code BRACKETS_BLOCK}'s content is raw tokens, never statements) and the
     *       expression-statement fallback for shapes {@code VarDeclarationStatement} declines
     *       (declaration lists, arrays). A cast like {@code (int)x} can never false-match: its
     *       {@code x} is preceded by the cast's {@code )} token (or nested {@code BRACKETS_BLOCK}),
     *       not by the bare type keyword.</li>
     * </ul>
     * A user-defined type's declaration ({@code MyStruct n;}) is not recognised (the type token is
     * an {@code IDENTIFIER}, indistinguishable from an expression without resolution) — missing a
     * declaration only means falling back to the previous, more lenient behavior, never new
     * false positives.
     */
    private static boolean isDeclarationOf(@NotNull ASTNode identifier) {
        ASTNode parent = identifier.getTreeParent();
        if (parent != null && parent.getElementType() == VAR_DEFINITION) {
            return true;
        }
        ASTNode prev = prevNonTrivia(identifier);
        return prev != null && MQL4TokenSets.DATA_TYPES.contains(prev.getElementType());
    }

    /** True when an {@code IDENTIFIER} token is directly followed by {@code [} — an array index access. */
    static boolean hasArrayAccess(@Nullable ASTNode root) {
        return findArrayAccess(root) != null;
    }

    /**
     * The {@code IDENTIFIER} node of the first array index READ ({@code id[...]}), or null — for
     * anchoring. Deliberately excludes a {@code VAR_DEFINITION} name — a variable DECLARATION's
     * array-size brackets ({@code double col[1];}) are not an index read. In practice the parser
     * already keeps that name's siblings from including the size brackets at all (they end up
     * flattened as siblings of the enclosing {@code VAR_DECLARATION_STATEMENT} instead, a parser
     * recovery quirk of {@code VarDeclarationStatement}), so this guard is belt-and-braces: it makes
     * the exclusion an explicit, obviously-correct structural check rather than an accidental
     * byproduct of that recovery path.
     */
    @Nullable
    static ASTNode findArrayAccess(@Nullable ASTNode root) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == IDENTIFIER) {
                ASTNode next = nextNonTrivia(child);
                ASTNode parent = child.getTreeParent();
                if (next != null && next.getElementType() == L_SQUARE_BRACKET
                        && (parent == null || parent.getElementType() != VAR_DEFINITION)) {
                    return child;
                }
            }
            ASTNode found = findArrayAccess(child);
            if (found != null) return found;
        }
        return null;
    }

    /** True when a {@code PLUS} token is adjacent (either side) to a {@code STRING_LITERAL} — string concatenation. */
    static boolean hasStringConcat(@Nullable ASTNode root) {
        return findStringConcat(root) != null;
    }

    /** The {@code PLUS} node of the first string concatenation, or null — for anchoring. */
    @Nullable
    static ASTNode findStringConcat(@Nullable ASTNode root) {
        if (root == null) return null;
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == PLUS) {
                ASTNode prev = prevNonTrivia(child);
                ASTNode next = nextNonTrivia(child);
                if ((prev != null && prev.getElementType() == STRING_LITERAL)
                        || (next != null && next.getElementType() == STRING_LITERAL)) {
                    return child;
                }
            }
            ASTNode found = findStringConcat(child);
            if (found != null) return found;
        }
        return null;
    }

    /**
     * Resolves the best PSI element to anchor a warning at: the given AST node's PSI if present,
     * else the fallback element. Leaf tokens in the flat statement AST are PSI-backed, but this
     * guards the rare null case so a warning still shows rather than throwing.
     */
    @NotNull
    static com.intellij.psi.PsiElement anchor(@Nullable ASTNode node, @NotNull com.intellij.psi.PsiElement fallback) {
        if (node != null) {
            com.intellij.psi.PsiElement psi = node.getPsi();
            if (psi != null) return psi;
        }
        return fallback;
    }

    /**
     * True when a call's {@code (...)} args are exactly {@code expectedCount} top-level,
     * comma-separated arguments, each a single bare {@code IDENTIFIER} token — no member access,
     * literal, or nested call/expression. This is the MQL5 request/result struct-call idiom
     * ({@code OrderSend(request, result)}, or {@code OrderSend(buy_request, buy_result)|
     * DualOrderManager.mqh:698}), as opposed to the MQL4 positional form
     * ({@code OrderSend(symbol, cmd, volume, price, ...)}), which always has more than two
     * arguments and/or non-identifier operands (literals, expressions).
     */
    static boolean callArgsAreBareIdentifiers(@NotNull ASTNode callIdentifier, int expectedCount) {
        ASTNode argsBlock = callArgsBlock(callIdentifier);
        if (argsBlock == null) return false;
        List<List<ASTNode>> segments = new ArrayList<>();
        List<ASTNode> current = new ArrayList<>();
        boolean sawAny = false;
        for (ASTNode child = argsBlock.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType t = child.getElementType();
            if (t == L_ROUND_BRACKET || t == R_ROUND_BRACKET || isTrivia(child)) continue;
            if (t == COMMA) {
                segments.add(current);
                current = new ArrayList<>();
            } else {
                current.add(child);
                sawAny = true;
            }
        }
        if (sawAny || !segments.isEmpty()) {
            segments.add(current);
        }
        if (segments.size() != expectedCount) return false;
        for (List<ASTNode> segment : segments) {
            if (segment.size() != 1 || segment.get(0).getElementType() != IDENTIFIER) return false;
        }
        return true;
    }

    /**
     * True when {@code node} has an {@code IF_STATEMENT} ancestor strictly between itself and
     * {@code boundaryRoot} (exclusive of {@code boundaryRoot} itself) — used to tell an
     * unconditional/top-level statement (e.g. a bare {@code return 0;} in {@code OnCalculate})
     * apart from one nested inside a guard clause ({@code if(rates_total<Period) return(0);}).
     */
    static boolean isNestedInIfStatement(@NotNull ASTNode node, @NotNull ASTNode boundaryRoot) {
        for (ASTNode current = node.getTreeParent(); current != null && current != boundaryRoot; current = current.getTreeParent()) {
            if (current.getElementType() == IF_STATEMENT) return true;
        }
        return false;
    }

    /**
     * The nearest {@code IF_STATEMENT} ancestor of {@code node} strictly between itself and
     * {@code boundaryRoot} (exclusive), or null if {@code node} is not nested in any {@code if}
     * within that boundary. Unlike {@link #isNestedInIfStatement}, this returns the actual branch
     * node so two nodes can be compared for "same branch" (mutually-exclusive early-return
     * branches, e.g. sibling {@code if(x == INVALID_HANDLE) { cleanup(); return; }} guards, have
     * different, non-null nearest-if ancestors and so are never mistaken for the same execution
     * path).
     */
    @Nullable
    static ASTNode nearestEnclosingIfStatement(@NotNull ASTNode node, @NotNull ASTNode boundaryRoot) {
        for (ASTNode current = node.getTreeParent(); current != null && current != boundaryRoot; current = current.getTreeParent()) {
            if (current.getElementType() == IF_STATEMENT) return current;
        }
        return null;
    }

    /**
     * Number of top-level (depth-0) comma-separated arguments in a call's {@code (...)} args
     * block, or 0 for a call with no args-block or an empty {@code ()} — for callers that need to
     * distinguish call arities (e.g. {@code ArrayResize}'s 2-arg vs. doc-endorsed 3-arg reserve
     * form). Nested calls/array literals inside an argument are their own nested
     * {@code BRACKETS_BLOCK} child, not raw tokens at this level, so a comma inside one is never
     * miscounted as a top-level argument separator.
     */
    static int callArgCount(@NotNull ASTNode callIdentifier) {
        ASTNode argsBlock = callArgsBlock(callIdentifier);
        if (argsBlock == null) return 0;
        int commas = 0;
        boolean sawContent = false;
        for (ASTNode child = argsBlock.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType t = child.getElementType();
            if (t == L_ROUND_BRACKET || t == R_ROUND_BRACKET || isTrivia(child)) continue;
            if (t == COMMA) {
                commas++;
            } else {
                sawContent = true;
            }
        }
        return (sawContent || commas > 0) ? commas + 1 : 0;
    }

    /**
     * True when {@code callIdentifier} is a call to a market-data function whose value changes on
     * every tick: {@code SymbolInfoTick}/{@code TimeCurrent}/{@code TimeLocal}, or a
     * {@code SymbolInfoDouble}/{@code SymbolInfoInteger}/{@code SymbolInfoString} call whose
     * arguments reference {@code SYMBOL_ASK}, {@code SYMBOL_BID} or {@code SYMBOL_LAST}. These
     * must never be recommended for caching across ticks — doing so would trade on a stale price.
     */
    static boolean isVolatileMarketCall(@NotNull ASTNode callIdentifier) {
        String name = callIdentifier.getText();
        if ("SymbolInfoTick".equals(name) || "TimeCurrent".equals(name) || "TimeLocal".equals(name)) {
            return true;
        }
        String text = callArgsText(callIdentifier);
        if (text == null) return false;
        return text.contains("SYMBOL_ASK") || text.contains("SYMBOL_BID") || text.contains("SYMBOL_LAST");
    }

    /** Statement nodes that a value-producing call can be the top of (bare call or var-decl init). */
    private static final TokenSet CALL_HOSTING_STATEMENTS =
            TokenSet.create(EXPRESSION_STATEMENT, VAR_DECLARATION_STATEMENT);


    /**
     * The enclosing {@code EXPRESSION_STATEMENT} or {@code VAR_DECLARATION_STATEMENT} of {@code node}
     * (the innermost one), or null — the unit a quick fix inserts after / rewrites.
     */
    @Nullable
    static ASTNode enclosingStatement(@NotNull ASTNode node) {
        for (ASTNode current = node; current != null; current = current.getTreeParent()) {
            if (CALL_HOSTING_STATEMENTS.contains(current.getElementType())) return current;
        }
        return null;
    }

    /**
     * True when {@code callIdentifier} is the leading token of a bare call statement
     * {@code foo(...);} — its enclosing {@code EXPRESSION_STATEMENT}'s first non-trivia child IS the
     * call identifier (no assignment target, no declared type in front). Only such a statement can be
     * safely wrapped as {@code if(foo(...) < 0) ...} by a quick fix; an assigned/declared call
     * ({@code int n = foo(...);}) must not be.
     */
    static boolean isBareCallStatement(@NotNull ASTNode callIdentifier) {
        ASTNode stmt = enclosingStatement(callIdentifier);
        if (stmt == null || stmt.getElementType() != EXPRESSION_STATEMENT) return false;
        ASTNode first = stmt.getFirstChildNode();
        while (first != null && isTrivia(first)) first = first.getTreeNext();
        return first == callIdentifier;
    }

    /**
     * The identifier a value is assigned to in {@code callIdentifier}'s enclosing statement — the LHS
     * of the {@code =} this call is the RHS of, for both an {@code h = iMA(...);} assignment (the
     * {@code =} is a direct sibling) and an {@code int copied = CopyBuffer(...);} declaration (the
     * name and {@code =} live inside a nested {@code VAR_DEFINITION}, the call a flat sibling after).
     * Uses the {@code =} nearest BEFORE the call — not merely the first {@code =} in the statement —
     * so in a multi-declarator {@code int a = 5, n = CopyBuffer(...);} it correctly names {@code n},
     * not {@code a}. Null if the call is not the RHS of a simple assignment. ({@code ==} is EQ_EQ,
     * {@code +=} is PLUS_EQ — neither matches EQ.)
     */
    @Nullable
    static String assignmentTargetName(@NotNull ASTNode callIdentifier) {
        ASTNode stmt = enclosingStatement(callIdentifier);
        if (stmt == null) return null;
        ASTNode[] nearest = {null};
        collectNearestPrecedingEq(stmt, callIdentifier.getStartOffset(), nearest);
        ASTNode eq = nearest[0];
        if (eq == null) return null;
        ASTNode lhs = prevNonTrivia(eq);
        return (lhs != null && lhs.getElementType() == IDENTIFIER) ? lhs.getText() : null;
    }

    /** Records into {@code best[0]} the {@code EQ} descendant of {@code node} with the greatest start
     *  offset still below {@code beforeOffset} — i.e. the '=' closest before the call. */
    private static void collectNearestPrecedingEq(@NotNull ASTNode node, int beforeOffset, @NotNull ASTNode[] best) {
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == EQ && child.getStartOffset() < beforeOffset
                    && (best[0] == null || child.getStartOffset() > best[0].getStartOffset())) {
                best[0] = child;
            }
            collectNearestPrecedingEq(child, beforeOffset, best);
        }
    }
}
