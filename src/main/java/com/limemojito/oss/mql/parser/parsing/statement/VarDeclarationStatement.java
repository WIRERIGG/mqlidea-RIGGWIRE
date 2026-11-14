/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing.statement;

import com.intellij.lang.PsiBuilder;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.parser.parsing.BracketBlockParsing;
import com.limemojito.oss.mql.parser.parsing.util.ParsingUtils;
import com.limemojito.oss.mql.parser.parsing.util.TokenAdvanceMode;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import static com.intellij.lang.parser.GeneratedParserUtilBase.recursion_guard_;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingUtils.checkTokenOrFail;

public class VarDeclarationStatement implements MQL4Elements {

    private static final TokenSet PRE_TYPES = TokenSet.create(CONST_KEYWORD, EXTERN_KEYWORD, INPUT_KEYWORD, SINPUT_KEYWORD, STATIC_KEYWORD);

    /** Pointer / reference marker between a declaration's type and a name: {@code CFoo *p}, {@code int &r}. */
    private static final TokenSet DECLARATOR_PREFIX = TokenSet.create(MUL, AND);

    /** Tokens that may follow a declared name and its array sizes: end, initializer, next name. */
    private static final TokenSet AFTER_NAME = TokenSet.create(SEMICOLON, EQ, COMMA);

    private static final int MAX_ARRAY_SIZE_TOKENS = 64;

    /** Tokens allowed inside a type's template argument list ({@code CStack<double>}, {@code CMap<string,CFoo*>}). */
    private static final TokenSet TEMPLATE_ARG_TOKENS = TokenSet.orSet(MQL4TokenSets.DATA_TYPES,
            TokenSet.create(IDENTIFIER, COMMA, MUL, AND, COLON_COLON, CONST_KEYWORD, LT, GT, SH_RIGHT));

    private static final int MAX_TEMPLATE_ARG_TOKENS = 32;

    /**
     * Lookahead-only recogniser for a variable declaration starting at the current token. Returns
     * the lookahead index of the first declared name, or -1 when the tokens are not a declaration.
     * Consumes nothing. Shape:
     * <pre>
     *   modifier* ( builtinType | Ident (:: Ident)* (&lt; templateArgs &gt;)? ) (* | &amp;)? name ([...])* (; | = | ,)
     * </pre>
     * Requiring {@code ; = ,} after the name (and its array sizes) keeps function declarations
     * ({@code T f(}), calls and unterminated lines ({@code #resource ... as bitmap px[][]}) out. A user type ({@code Ident}) followed by a name cannot start a valid expression statement,
     * so {@code CTrade trade;} / {@code MqlRates rates[];} are unambiguous; {@code a*b;} would match,
     * but that statement has no effect and MetaEditor warns about it.
     */
    public static int declarationNameIndex(@NotNull PsiBuilder b) {
        int n = 0;
        while (PRE_TYPES.contains(b.lookAhead(n))) {
            n++;
        }
        IElementType type = b.lookAhead(n);
        if (MQL4TokenSets.DATA_TYPES.contains(type)) {
            n++;
        } else if (type == IDENTIFIER) {
            n++;
            while (b.lookAhead(n) == COLON_COLON && b.lookAhead(n + 1) == IDENTIFIER) {
                n += 2;
            }
            if (b.lookAhead(n) == LT) {
                n = skipTemplateArgs(b, n);
                if (n < 0) {
                    return -1;
                }
            }
        } else {
            return -1;
        }
        if (DECLARATOR_PREFIX.contains(b.lookAhead(n))) {
            n++;
        }
        if (b.lookAhead(n) != IDENTIFIER) {
            return -1;
        }
        int after = skipArraySizes(b, n + 1);
        if (after < 0 || !AFTER_NAME.contains(b.lookAhead(after))) {
            return -1;
        }
        return n;
    }

    /** Index just past any {@code [...]} groups starting at {@code n}, or -1 if one doesn't close in reach. */
    private static int skipArraySizes(@NotNull PsiBuilder b, int n) {
        while (b.lookAhead(n) == L_SQUARE_BRACKET) {
            int depth = 0;
            int limit = n + MAX_ARRAY_SIZE_TOKENS;
            do {
                IElementType t = b.lookAhead(n);
                if (t == null || n >= limit || t == SEMICOLON || t == L_CURLY_BRACKET || t == R_CURLY_BRACKET) {
                    return -1;
                }
                if (t == L_SQUARE_BRACKET) {
                    depth++;
                } else if (t == R_SQUARE_BRACKET) {
                    depth--;
                }
                n++;
            } while (depth > 0);
        }
        return n;
    }

    /** Index just past the {@code <...>} starting at {@code lt}, or -1 if it isn't a plain template argument list. */
    private static int skipTemplateArgs(@NotNull PsiBuilder b, int lt) {
        int depth = 0;
        for (int n = lt; n < lt + MAX_TEMPLATE_ARG_TOKENS; n++) {
            IElementType t = b.lookAhead(n);
            if (t == null || !TEMPLATE_ARG_TOKENS.contains(t)) {
                return -1;
            }
            if (t == LT) {
                depth++;
            } else if (t == GT) {
                depth--;
            } else if (t == SH_RIGHT) {
                depth -= 2;
            }
            if (depth <= 0) {
                return depth == 0 ? n + 1 : -1;
            }
        }
        return -1;
    }

    public static boolean parseVarDeclaration(PsiBuilder b, int l) {
        if (!recursion_guard_(b, l, "parseVarDeclaration")) {
            return false;
        }
        int nameAt = declarationNameIndex(b);
        if (nameAt < 0) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        // modifiers, type (with any qualifier / template arguments) and a '*'/'&' before the first
        // name stay flat children of the statement, as the single type token always was
        for (int i = 0; i < nameAt; i++) {
            skipComments(b);
            b.advanceLexer();
        }
        skipComments(b);
        if (parseVarDefinitionList(b, l + 1) == ListEnd.INITIALIZER) {
            ParsingUtils.advanceLexerUntil(b, SEMICOLON, TokenAdvanceMode.ADVANCE);
        }
        m.done(VAR_DECLARATION_STATEMENT);
        return true;
    }

    /** How a {@link #parseVarDefinitionList} run ended. */
    public enum ListEnd {
        /** The terminating {@code ;} was consumed. */
        TERMINATED,
        /**
         * Stopped before the LAST name's initializer, which the caller consumes flat up to {@code ;}
         * ({@code int x = ...;} keeps its established shape, initializer tokens after the list).
         */
        INITIALIZER,
        /** Stopped at an unexpected token, left for the enclosing parser (nothing is swallowed). */
        ABORTED
    }

    /**
     * One or more {@code VAR_DEFINITION}s: {@code a}, {@code a[5][2]}, {@code *p}, separated by commas
     * and ending at {@code ;}. An initializer followed by another name ({@code int a = 1, b;}) stays
     * inside the list, as flat tokens, so the later names are still definitions.
     */
    public static ListEnd parseVarDefinitionList(PsiBuilder b, int l) {
        assert b.getTokenType() == IDENTIFIER;
        PsiBuilder.Marker m0 = b.mark();
        try {
            while (true) {
                PsiBuilder.Marker m1 = b.mark();
                if (DECLARATOR_PREFIX.contains(b.getTokenType())) {
                    b.advanceLexer(); // '*' | '&' of a later name: int *a, *b;
                }
                if (b.getTokenType() != IDENTIFIER) {
                    m1.drop();
                    return ListEnd.ABORTED;
                }
                b.advanceLexer(); // name
                skipComments(b);
                while (b.getTokenType() == L_SQUARE_BRACKET) {
                    if (!BracketBlockParsing.parseBracketsBlock(b, l + 1)) { // array size: buf[], m[2][3]
                        break;
                    }
                    skipComments(b);
                }
                IElementType t = b.getTokenType();
                if (t == SEMICOLON) {
                    b.advanceLexer();
                    m1.done(VAR_DEFINITION);
                    return ListEnd.TERMINATED;
                }
                if (t == COMMA) {
                    m1.done(VAR_DEFINITION);
                    b.advanceLexer(); // ','
                    skipComments(b);
                    continue;
                }
                if (t == EQ) {
                    b.advanceLexer();
                    m1.done(VAR_DEFINITION);
                    if (!initializerEndsWithComma(b)) {
                        return ListEnd.INITIALIZER;
                    }
                    consumeInitializer(b);
                    b.advanceLexer(); // ','
                    skipComments(b);
                    continue;
                }
                m1.done(VAR_DEFINITION);
                return ListEnd.ABORTED;
            }
        } finally {
            m0.done(VAR_DEFINITION_LIST);
        }
    }

    /**
     * True when the initializer at the current token ends at a top-level {@code ,} (another name
     * follows) rather than at {@code ;}. Lookahead only: the builder is rolled back.
     */
    private static boolean initializerEndsWithComma(@NotNull PsiBuilder b) {
        PsiBuilder.Marker probe = b.mark();
        try {
            return consumeInitializer(b) && b.getTokenType() == COMMA;
        } finally {
            probe.rollbackTo();
        }
    }

    /**
     * Consumes initializer tokens flat (no bracket blocks, matching the established initializer
     * shape) up to, not including, the top-level {@code ,} or {@code ;}. Returns false if it stopped
     * at anything else: an unmatched right bracket, a preprocessor line or end of file.
     */
    private static boolean consumeInitializer(@NotNull PsiBuilder b) {
        int depth = 0;
        while (!b.eof()) {
            IElementType t = b.getTokenType();
            if (depth == 0 && (t == COMMA || t == SEMICOLON)) {
                return true;
            }
            if (MQL4TokenSets.PREPROCESSOR.contains(t)) {
                return false;
            }
            if (t == L_ROUND_BRACKET || t == L_SQUARE_BRACKET || t == L_CURLY_BRACKET) {
                depth++;
            } else if (MQL4TokenSets.RIGHT_BRACKETS.contains(t)) {
                if (depth == 0) {
                    return false;
                }
                depth--;
            }
            b.advanceLexer();
        }
        return false;
    }

    private static void skipComments(PsiBuilder b) {
        //noinspection StatementWithEmptyBody
        while (com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment(b)) {
        }
    }

    /**
     * Var declaration inside another block. Like 1 section if for loop. Does not allow empty vars or pre-types
     */
    public static boolean parseEmbeddedVarDeclarationOrAssignmentOrFail(PsiBuilder b, int l, @NotNull IElementType sectionType, @NotNull IElementType assignmentSectionType) {
        if (!recursion_guard_(b, l, "parseEmbeddedVarDeclarationOrAssignment")) {
            return false;
        }
        boolean firstIsType = MQL4TokenSets.DATA_TYPES.contains(b.getTokenType());
        PsiBuilder.Marker m = b.mark();
        try {
            if (firstIsType) {
                b.advanceLexer();
            }
            //noinspection SimplifiableIfStatement
            if (firstIsType && !checkTokenOrFail(b, IDENTIFIER)) {
                return false;
            }
            return parseEmbeddedVarAssignmentsListOrFail(b, l + 1, assignmentSectionType, SEMICOLON);
        } finally {
            m.done(sectionType);
        }
    }

    public static boolean parseEmbeddedVarAssignmentsListOrFail(PsiBuilder b, int l, @NotNull IElementType sectionType, @NotNull IElementType stopToken) {
        if (!recursion_guard_(b, l, "parseEmbeddedVarAssignmentsList")) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        try {
            if (b.getTokenType() == stopToken) {
                return true;
            }
            while (true) {
                boolean ok = ParsingUtils.parseTokenOrFail(b, IDENTIFIER)
                        && ParsingUtils.parseTokenOrFail(b, EQ)
                        //TODO: && parseExpressionOrFail(b, l + 1)
                        ;
                if (!ok) {
                    return false;
                }
                if (b.getTokenType() == stopToken) {
                    return true;
                }
                if (!ParsingUtils.parseTokenOrFail(b, COMMA)) {
                    return false;
                }
            }
        } finally {
            m.done(sectionType);
        }

    }

}
