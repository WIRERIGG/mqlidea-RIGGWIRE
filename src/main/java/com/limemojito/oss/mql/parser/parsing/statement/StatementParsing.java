/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing.statement;

import com.intellij.lang.PsiBuilder;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.parser.parsing.BracketBlockParsing;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import static com.intellij.lang.parser.GeneratedParserUtilBase.recursion_guard_;
import static com.limemojito.oss.mql.parser.parsing.BracketBlockParsing.parseBracketsBlock;
import static com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment;
import static com.limemojito.oss.mql.parser.parsing.statement.VarDeclarationStatement.parseVarDeclaration;

/**
 * Parses individual statements inside {} code blocks.
 * <p>
 * Every parse method here is TOLERANT by design: it either consumes at least one token and
 * completes its marker, or consumes nothing, leaves no marker behind and returns false so the
 * caller's fallback ({@code advanceLexer()}) keeps today's behavior. No method in this class
 * emits parse errors — unparsable content simply terminates the current statement early.
 */
public class StatementParsing implements MQL4Elements {

    private static final TokenSet SINGLE_WORD_STATEMENTS = TokenSet.create(
            BREAK_KEYWORD,
            CONTINUE_KEYWORD
    );

    /**
     * Keywords that always start (or belong to) a dedicated statement form and therefore
     * terminate a token-scan of the current statement when met at bracket-depth 0.
     */
    private static final TokenSet STATEMENT_KEYWORDS = TokenSet.create(
            IF_KEYWORD,
            ELSE_KEYWORD,
            FOR_KEYWORD,
            WHILE_KEYWORD,
            DO_KEYWORD,
            SWITCH_KEYWORD,
            RETURN_KEYWORD,
            BREAK_KEYWORD,
            CONTINUE_KEYWORD,
            CASE_KEYWORD,
            DEFAULT_KEYWORD
    );

    public static boolean parseStatement(PsiBuilder b, int l) {
        if (!recursion_guard_(b, l, "parseStatement")) {
            return false;
        }
        IElementType t = b.getTokenType();
        if (t == null || MQL4TokenSets.COMMENTS.contains(t)) {
            return false; // comments are handled by the caller's loop
        }
        return parseEmptyStatement(b)
                || parseSingleWordStatement(b)
                || parseReturnStatement(b, l)
                || parseIfStatement(b, l)
                || parseLoopLikeStatement(b, l, FOR_KEYWORD, FOR_STATEMENT)
                || parseLoopLikeStatement(b, l, WHILE_KEYWORD, WHILE_STATEMENT)
                || parseDoStatement(b, l)
                || parseSwitchStatement(b, l)
                || parseLocalVarDeclaration(b, l)
                || parseBlockStatement(b, l)
                || parseExpressionStatement(b, l);
    }

    private static boolean parseSingleWordStatement(PsiBuilder b) {
        IElementType t = b.getTokenType();
        if (!SINGLE_WORD_STATEMENTS.contains(t)) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'break' | 'continue'
        if (b.lookAhead(0) == SEMICOLON) {
            parseCommentsRun(b);
            b.advanceLexer(); // ';'
        }
        m.done(SINGLE_WORD_STATEMENT);
        return true;
    }

    public static boolean parseEmptyStatement(PsiBuilder b) {
        IElementType t = b.getTokenType();
        if (t != SEMICOLON) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer();
        m.done(EMPTY_STATEMENT);
        return true;
    }

    /**
     * Form: return [anything up to ';'];
     */
    private static boolean parseReturnStatement(PsiBuilder b, int l) {
        if (b.getTokenType() != RETURN_KEYWORD) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'return'
        consumeStatementTail(b, l);
        m.done(RETURN_STATEMENT);
        return true;
    }

    /**
     * Form: if (cond) statement [else statement]
     */
    private static boolean parseIfStatement(PsiBuilder b, int l) {
        if (b.getTokenType() != IF_KEYWORD) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'if'
        parseParenGroup(b, l + 1);
        parseBranch(b, l); // then-branch
        if (b.lookAhead(0) == ELSE_KEYWORD) {
            parseCommentsRun(b);
            b.advanceLexer(); // 'else'
            parseBranch(b, l); // else-branch (may be another if statement)
        }
        m.done(IF_STATEMENT);
        return true;
    }

    /**
     * Form: (for|while) (header) statement
     */
    private static boolean parseLoopLikeStatement(PsiBuilder b, int l, IElementType keyword, IElementType statementType) {
        if (b.getTokenType() != keyword) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'for' | 'while'
        if (keyword == FOR_KEYWORD && b.lookAhead(0) == L_ROUND_BRACKET) {
            parseCommentsRun(b);
            BracketBlockParsing.parseForHeader(b, l + 1); // for(int i=0; ...): i is a definition
        } else {
            parseParenGroup(b, l + 1);
        }
        parseBranch(b, l); // loop body
        m.done(statementType);
        return true;
    }

    /**
     * Form: do statement while (cond);
     */
    private static boolean parseDoStatement(PsiBuilder b, int l) {
        if (b.getTokenType() != DO_KEYWORD) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'do'
        parseBranch(b, l); // loop body
        if (b.lookAhead(0) == WHILE_KEYWORD) {
            parseCommentsRun(b);
            b.advanceLexer(); // 'while'
            parseParenGroup(b, l + 1);
            if (b.lookAhead(0) == SEMICOLON) {
                parseCommentsRun(b);
                b.advanceLexer(); // ';'
            }
        }
        m.done(DO_STATEMENT);
        return true;
    }

    /**
     * Form: switch (value) { ... }. Case/default labels inside the body are parsed as
     * ordinary block content.
     */
    private static boolean parseSwitchStatement(PsiBuilder b, int l) {
        if (b.getTokenType() != SWITCH_KEYWORD) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'switch'
        parseParenGroup(b, l + 1);
        if (b.lookAhead(0) == L_CURLY_BRACKET) {
            parseCommentsRun(b);
            parseBracketsBlock(b, l + 1);
        }
        m.done(SWITCH_STATEMENT);
        return true;
    }

    /**
     * Variable declaration, used in {@code {}} code blocks, at the top level (globals) and in class
     * bodies (fields). The shape is decided by {@link VarDeclarationStatement#declarationNameIndex}:
     * {@code [modifier]* type [*|&] name} followed by {@code ;}, {@code =}, {@code ,} or {@code [},
     * where the type is a built-in keyword or a user, qualified or template type. Anything else
     * (calls, constructor-argument declarations {@code CFoo f(1);}, expressions) falls through
     * untouched to the caller's fallback.
     */
    public static boolean parseLocalVarDeclaration(PsiBuilder b, int l) {
        if (parseTypedef(b, l)) {
            return true; // `typedef int (*TOp)(int);` declares a type (T-4), not a variable
        }
        // VarDeclarationStatement.declarationNameIndex is the gate: user/qualified/template types,
        // '*'/'&', array sizes and comma lists, but only when the name is followed by ; = , or [.
        // VarDeclarationStatement uses raw mark()/done() (no enter_section_), so it is safe to call
        // with the bracket block's raw PsiBuilder.
        return parseVarDeclaration(b, l);
    }

    /**
     * Form: typedef returnType (*Name)(params); -- MQL5's only typedef, a function-pointer type. The
     * return type goes in a TYPEDEF_RETURN_TYPE node so Name is the TYPEDEF's first direct
     * IDENTIFIER. {@code typedef} isn't reserved in MQL4, so it's recognized by text. A malformed
     * typedef is consumed through its {@code ;} (stopping before a brace) as a TYPEDEF without a name.
     */
    private static boolean parseTypedef(PsiBuilder b, int l) {
        if (b.getTokenType() != IDENTIFIER || !"typedef".equals(b.getTokenText())) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.remapCurrentToken(TYPEDEF_KEYWORD);
        b.advanceLexer(); // 'typedef'
        PsiBuilder.Marker ret = b.mark();
        while (!b.eof() && !TYPEDEF_STOP.contains(b.getTokenType())) {
            b.advanceLexer();
        }
        ret.done(TYPEDEF_RETURN_TYPE);
        if (b.getTokenType() == L_ROUND_BRACKET && b.lookAhead(1) == MUL && b.lookAhead(2) == IDENTIFIER
                && b.lookAhead(3) == R_ROUND_BRACKET) {
            b.advanceLexer(); // '('
            b.advanceLexer(); // '*'
            b.advanceLexer(); // name
            b.advanceLexer(); // ')'
            if (b.getTokenType() == L_ROUND_BRACKET) {
                parseBracketsBlock(b, l + 1); // (params)
            }
        }
        while (!b.eof() && b.getTokenType() != SEMICOLON
                && b.getTokenType() != L_CURLY_BRACKET && b.getTokenType() != R_CURLY_BRACKET) {
            b.advanceLexer();
        }
        if (b.getTokenType() == SEMICOLON) {
            b.advanceLexer();
        }
        m.done(TYPEDEF);
        return true;
    }

    private static final TokenSet TYPEDEF_STOP = TokenSet.create(L_ROUND_BRACKET, SEMICOLON, L_CURLY_BRACKET, R_CURLY_BRACKET);

    /**
     * Nested {} code block used as a statement.
     */
    private static boolean parseBlockStatement(PsiBuilder b, int l) {
        return b.getTokenType() == L_CURLY_BRACKET && parseBracketsBlock(b, l);
    }

    /**
     * Fallback statement: function calls, assignments, increments etc. Consumes tokens up to and
     * including the terminating ';' at bracket-depth 0. A '{', '}', unmatched right bracket,
     * preprocessor token, statement keyword or EOF terminates the statement without being
     * consumed. Returns false (leaving no marker) if nothing could be consumed.
     */
    private static boolean parseExpressionStatement(PsiBuilder b, int l) {
        if (!canStartExpressionStatement(b.getTokenType())) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        int consumed = consumeStatementTail(b, l);
        if (consumed == 0) {
            m.drop();
            return false;
        }
        m.done(EXPRESSION_STATEMENT);
        return true;
    }

    private static boolean canStartExpressionStatement(@Nullable IElementType t) {
        if (t == null
                || t == SEMICOLON
                || t == L_CURLY_BRACKET
                || t == COLON
                || t == TEMPLATE_KEYWORD
                || t == BAD_CHARACTER) {
            return false;
        }
        return !MQL4TokenSets.RIGHT_BRACKETS.contains(t)
                && !MQL4TokenSets.COMMENTS.contains(t)
                && !MQL4TokenSets.PREPROCESSOR.contains(t)
                && !STATEMENT_KEYWORDS.contains(t);
    }

    /**
     * Consumes the rest of the current statement: everything up to and including the next ';'
     * at bracket-depth 0. Nested (...) and [...] groups are parsed as bracket blocks. Stops
     * WITHOUT consuming on '{', '}', unmatched right brackets, preprocessor tokens, statement
     * keywords and label colons (a ':' at bracket-depth 0 that has no matching '?').
     *
     * @return number of top-level items consumed (0 if the statement tail is empty).
     */
    private static int consumeStatementTail(PsiBuilder b, int l) {
        int consumed = 0;
        int ternaryNesting = 0;
        while (!b.eof()) {
            IElementType t = b.getTokenType();
            if (t == SEMICOLON) {
                b.advanceLexer(); // terminating ';'
                consumed++;
                break;
            }
            if (t == L_CURLY_BRACKET
                    || MQL4TokenSets.RIGHT_BRACKETS.contains(t)
                    || MQL4TokenSets.PREPROCESSOR.contains(t)
                    || STATEMENT_KEYWORDS.contains(t)) {
                break; // statement ends here; token is left for the caller
            }
            if (t == COLON && ternaryNesting == 0) {
                break; // most likely a case/default label colon
            }
            if (t == L_ROUND_BRACKET || t == L_SQUARE_BRACKET) {
                if (!parseBracketsBlock(b, l + 1)) {
                    break; // could not parse the group: bail out, caller's fallback advances
                }
                consumed++;
                continue;
            }
            if (t == QUESTION) {
                ternaryNesting++;
            } else if (t == COLON) {
                ternaryNesting--;
            }
            b.advanceLexer();
            consumed++;
        }
        return consumed;
    }

    /**
     * Sub-statement of a control-flow statement: '{...}' block or a single statement.
     * Comments directly before the branch become part of the enclosing statement.
     */
    private static void parseBranch(PsiBuilder b, int l) {
        parseCommentsRun(b);
        parseStatement(b, l + 1);
    }

    /**
     * Parses the (...) group of a control-flow statement if present. Tolerant: a malformed
     * header without '(' is simply skipped without reporting errors.
     */
    private static void parseParenGroup(PsiBuilder b, int l) {
        if (b.lookAhead(0) == L_ROUND_BRACKET) {
            parseCommentsRun(b);
            parseBracketsBlock(b, l);
        }
    }

    private static void parseCommentsRun(PsiBuilder b) {
        //noinspection StatementWithEmptyBody
        while (parseComment(b)) {
        }
    }
}
