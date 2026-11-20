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

    /** Keywords that can't appear in an initializer: meeting one means the {@code ;} is missing. */
    private static final TokenSet STATEMENT_KEYWORDS = TokenSet.create(IF_KEYWORD, ELSE_KEYWORD, FOR_KEYWORD,
            WHILE_KEYWORD, DO_KEYWORD, SWITCH_KEYWORD, RETURN_KEYWORD, BREAK_KEYWORD, CONTINUE_KEYWORD,
            CASE_KEYWORD, DEFAULT_KEYWORD);

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
        return declarationNameIndex(b, false);
    }

    /**
     * As {@link #declarationNameIndex(PsiBuilder)}; with {@code constructorArgs} (code blocks only)
     * a user type's name may also take constructor arguments, {@code CFoo f(1, 2);} or
     * {@code CArrayList<int> list(n);}. At the top level and in class bodies that shape is a
     * function prototype, so it isn't accepted there. A built-in type never takes them:
     * {@code int f(int);} in a body is a prototype.
     */
    public static int declarationNameIndex(@NotNull PsiBuilder b, boolean constructorArgs) {
        int n = 0;
        while (PRE_TYPES.contains(b.lookAhead(n))) {
            n++;
        }
        IElementType type = b.lookAhead(n);
        boolean userType = type == IDENTIFIER;
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
        while (b.lookAhead(n) == STATIC_KEYWORD || b.lookAhead(n) == CONST_KEYWORD) {
            n++; // a modifier after the type: datetime static last = 0;
        }
        if (DECLARATOR_PREFIX.contains(b.lookAhead(n))) {
            n++;
        }
        if (b.lookAhead(n) != IDENTIFIER) {
            return -1;
        }
        int after = skipArraySizes(b, n + 1);
        if (after >= 0 && constructorArgs && userType && b.lookAhead(after) == L_ROUND_BRACKET
                && sameLine(b, 0, n)) { // MACRO_WITHOUT_SEMICOLON <newline> Call(x); is not a declaration
            after = skipConstructorArgs(b, after);
        }
        if (after < 0 || !AFTER_NAME.contains(b.lookAhead(after))) {
            return -1;
        }
        return n;
    }

    /** True when no line break separates lookahead tokens {@code from} and {@code to}. */
    private static boolean sameLine(@NotNull PsiBuilder b, int from, int to) {
        int fromOffset = -1;
        int seen = 0;
        for (int raw = 0; raw < 4 * MAX_TEMPLATE_ARG_TOKENS; raw++) {
            IElementType t = b.rawLookup(raw);
            if (t == null) {
                return false;
            }
            if (com.limemojito.oss.mql.parser.MQL4ParserDefinition.WHITE_SPACES.contains(t) || MQL4TokenSets.COMMENTS.contains(t)) {
                continue;
            }
            if (seen == from) {
                fromOffset = b.rawTokenTypeStart(raw);
            }
            if (seen == to) {
                int toOffset = b.rawTokenTypeStart(raw);
                return fromOffset >= 0 && b.getOriginalText().subSequence(fromOffset, toOffset).chars().noneMatch(c -> c == '\n');
            }
            seen++;
        }
        return false;
    }

    private static final int MAX_CONSTRUCTOR_ARG_TOKENS = 256;

    /** Index just past the {@code (...)} starting at {@code lp}, or -1 if it doesn't close within the statement. */
    private static int skipConstructorArgs(@NotNull PsiBuilder b, int lp) {
        int depth = 0;
        for (int n = lp; n < lp + MAX_CONSTRUCTOR_ARG_TOKENS; n++) {
            IElementType t = b.lookAhead(n);
            if (t == null || t == SEMICOLON || t == L_CURLY_BRACKET || t == R_CURLY_BRACKET) {
                return -1;
            }
            if (t == L_ROUND_BRACKET) {
                depth++;
            } else if (t == R_ROUND_BRACKET && --depth == 0) {
                return n + 1;
            }
        }
        return -1;
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
        return parseVarDeclaration(b, l, false);
    }

    /** {@code constructorArgs}: in a code block, where {@code CFoo f(1);} declares {@code f}. */
    public static boolean parseVarDeclaration(PsiBuilder b, int l, boolean constructorArgs) {
        if (!recursion_guard_(b, l, "parseVarDeclaration")) {
            return false;
        }
        int nameAt = declarationNameIndex(b, constructorArgs);
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
            b.advanceLexer(); // ';' after the last initializer
        }
        m.done(VAR_DECLARATION_STATEMENT);
        return true;
    }

    /** How a {@link #parseVarDefinitionList} run ended. */
    public enum ListEnd {
        /** The terminating {@code ;} was consumed. */
        TERMINATED,
        /**
         * The LAST name's initializer was consumed flat after the list ({@code int x = ...;} keeps its
         * established shape, initializer tokens after the list), stopping at the {@code ;}, which the
         * caller consumes.
         */
        INITIALIZER,
        /** As {@link #INITIALIZER}, but the initializer is unfinished and stopped where {@link #consumeInitializer} stops. */
        UNFINISHED,
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
        boolean listDone = false;
        try {
            while (true) {
                PsiBuilder.Marker m1 = b.mark();
                if (b.getTokenType() == CONST_KEYWORD) {
                    b.advanceLexer(); // a later name's own const: for(int i = 0, const end = n; ...)
                }
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
                if (t == EQ || t == L_ROUND_BRACKET) {
                    if (t == EQ) {
                        b.advanceLexer();
                    }
                    m1.done(VAR_DEFINITION);
                    // constructor arguments, CFoo f(1, 2), are consumed like an initializer
                    // One pass over the initializer: when it ends at ',' another name follows and it
                    // stays inside the list; otherwise the list ends before it (doneBefore), giving
                    // the same tree as stopping first and consuming it afterwards.
                    PsiBuilder.Marker initializer = b.mark();
                    boolean finished = consumeInitializer(b);
                    if (finished && b.getTokenType() == COMMA) {
                        initializer.drop();
                        b.advanceLexer(); // ','
                        skipComments(b);
                        continue;
                    }
                    m0.doneBefore(VAR_DEFINITION_LIST, initializer);
                    initializer.drop();
                    listDone = true;
                    return finished ? ListEnd.INITIALIZER : ListEnd.UNFINISHED;
                }
                m1.done(VAR_DEFINITION);
                return ListEnd.ABORTED;
            }
        } finally {
            if (!listDone) {
                m0.done(VAR_DEFINITION_LIST);
            }
        }
    }

    private static final TokenSet TYPE_ARGUMENT_TOKENS = TokenSet.orSet(MQL4TokenSets.DATA_TYPES, TokenSet.create(
            IDENTIFIER, COMMA, MUL, AND, COLON_COLON, CONST_KEYWORD, LT, GT, SH_RIGHT));

    /**
     * When the current {@code IDENTIFIER} starts {@code Name<types>(}, the number of tokens up to and including
     * the closing {@code >}; else 0. Only type tokens may sit between the angle brackets, so a comparison
     * ({@code a < b}) isn't taken for one.
     */
    private static int templateArgumentsEnd(@NotNull PsiBuilder b) {
        if (b.lookAhead(1) != LT) {
            return 0;
        }
        int angles = 0;
        for (int k = 1; k < 48; k++) {
            IElementType a = b.lookAhead(k);
            if (a == null || !TYPE_ARGUMENT_TOKENS.contains(a)) {
                return 0;
            }
            if (a == LT) {
                angles++;
            } else if (a == GT || a == SH_RIGHT) {
                angles -= a == GT ? 1 : 2; // CStack<CArray<int>>: '>>' closes two
                if (angles <= 0) {
                    return angles == 0 && b.lookAhead(k + 1) == L_ROUND_BRACKET ? k + 1 : 0;
                }
            }
        }
        return 0;
    }

    /**
     * Consumes initializer tokens flat (no bracket blocks, matching the established initializer
     * shape) up to, not including, the top-level {@code ,} or {@code ;}. Returns false, leaving the
     * stop token for the enclosing parser, when the initializer is unfinished: at an unmatched right
     * bracket ({@code for(int i = 0)} or a missing {@code ;} before {@code }}), a statement keyword,
     * a {@code {} that isn't the initializer's first token, or a preprocessor line at the top level
     * (one inside {@code {1, #ifdef X 2, #endif 3}} is part of the initializer), or end of file.
     */
    private static boolean consumeInitializer(@NotNull PsiBuilder b) {
        int depth = 0;
        boolean first = true;
        while (!b.eof()) {
            IElementType t = b.getTokenType();
            if (depth == 0) {
                if (t == COMMA || t == SEMICOLON) {
                    return true;
                }
                if (STATEMENT_KEYWORDS.contains(t) || MQL4TokenSets.PREPROCESSOR.contains(t)
                        || (t == L_CURLY_BRACKET && !first)) {
                    return false;
                }
            }
            first = false;
            int typeArgs = t == IDENTIFIER ? templateArgumentsEnd(b) : 0;
            if (typeArgs > 0) {
                // F<int, CFoo *>(x), new CPair<TKey,TValue>(k, v): the type arguments' ',' doesn't end the initializer
                for (int k = 0; k < typeArgs; k++) {
                    b.advanceLexer();
                }
                continue;
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
