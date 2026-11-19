/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing;

import com.limemojito.oss.mql.parser.parsing.statement.VarDeclarationStatement;
import com.intellij.lang.PsiBuilder;
import com.intellij.lang.PsiBuilder.Marker;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.parser.parsing.util.ParsingErrors;
import com.limemojito.oss.mql.parser.parsing.util.ParsingScope;
import com.limemojito.oss.mql.psi.MQL4Elements;

import static com.limemojito.oss.mql.parser.parsing.BracketBlockParsing.parseBracketsBlock;
import static com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment;
import static com.limemojito.oss.mql.parser.parsing.FunctionsParsing.parseFunction;
import static com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorParsing.parsePreprocessorBlock;
import static com.limemojito.oss.mql.parser.parsing.statement.EnumParsing.parseEnum;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseEmptyStatement;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseLocalVarDeclaration;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.error;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingUtils.advanceLexerUntil;
import static com.limemojito.oss.mql.psi.MQL4TokenSets.CLASS_STRUCT_INTERFACE;

public class ClassParsing implements MQL4Elements {

    public static final TokenSet ON_ERROR_CLASS_ADVANCE_TOKENS = TokenSet.create(R_CURLY_BRACKET);
    public static final TokenSet ON_ERROR_CLASS_DO_NOT_ADVANCE_TOKENS = TokenSet.create(SEMICOLON);

    /**
     * Form: [abstract] (class|struct|interface|union) name [pack(n)] [final] [pack(n)] [: inheritance] { }
     */
    /**
     * A class, struct or interface, then any variables declared after its body
     * ({@code struct Settings { ... } sets;}): those follow as their own VAR_DECLARATION_STATEMENT
     * beside the CLASS node, so at file level they are globals like {@code Settings sets;}.
     */
    public static boolean parseClassOrStruct(PsiBuilder b, int l) {
        if (!parseClassOrStructNode(b, l)) {
            return false;
        }
        if (previousTokenIs(b, R_CURLY_BRACKET) && b.getTokenType() == IDENTIFIER
                && TRAILING_DECLARATOR_FOLLOW.contains(b.lookAhead(1))) {
            Marker statement = b.mark();
            if (VarDeclarationStatement.parseVarDefinitionList(b, l + 1) == VarDeclarationStatement.ListEnd.INITIALIZER) {
                b.advanceLexer(); // ';' after the last initializer
            }
            statement.done(VAR_DECLARATION_STATEMENT);
        }
        return true;
    }

    /** What may follow the first name of {@code } name;}: {@code ;}, {@code ,}, {@code [} or {@code =}. */
    private static final TokenSet TRAILING_DECLARATOR_FOLLOW = TokenSet.create(SEMICOLON, COMMA, L_SQUARE_BRACKET, EQ);

    private static boolean previousTokenIs(PsiBuilder b, IElementType type) {
        for (int i = -1; ; i--) {
            IElementType t = b.rawLookup(i);
            if (t == null || !com.limemojito.oss.mql.psi.MQL4TokenSets.COMMENTS_OR_WS.contains(t)) {
                return t == type;
            }
        }
    }

    private static boolean parseClassOrStructNode(PsiBuilder b, int l) {
        if (isUnionStart(b)) {
            return parseUnion(b, l);
        }
        IElementType t1 = b.getTokenType();
        boolean hasAbstract = false;
        if (t1 == MQL4Elements.ABSTRACT_KEYWORD) {
            IElementType next = b.lookAhead(1);
            if (CLASS_STRUCT_INTERFACE.contains(next)) {
                hasAbstract = true;
                t1 = next;
            } else {
                return false;
            }
        }
        if (!CLASS_STRUCT_INTERFACE.contains(t1)) {
            return false;
        }
        Marker m = b.mark();
        try {
            if (hasAbstract) {
                b.advanceLexer(); // 'abstract'
            }
            b.advanceLexer(); // 'class|struct'
            IElementType t2 = b.getTokenType();
            if (t2 != IDENTIFIER) {
                error(b, (t1 == CLASS_KEYWORD ? "Class" : t1 == STRUCT_KEYWORD ? "Struct" : "Interface") + " name is expected");
                b.mark().done(MQL4Elements.CLASS_INNER_BLOCK);
                return true;
            }
            b.advanceLexer(); // name

            parsePackSpecifier(b, l);
            if (b.getTokenType() == MQL4Elements.FINAL_KEYWORD) {
                b.advanceLexer(); // 'final'
                parsePackSpecifier(b, l);
            }

            IElementType t3 = b.getTokenType();
            if (t3 == SEMICOLON) {
                return true; // class declaration;
            }
            if (t3 == COLON) {
                b.advanceLexer(); // ':'
                if (!parseInheritanceList(b, l)) {
                    advanceLexerUntil(b, ON_ERROR_CLASS_ADVANCE_TOKENS, ON_ERROR_CLASS_DO_NOT_ADVANCE_TOKENS);
                    return true;
                }
            }
            if (b.getTokenType() != L_CURLY_BRACKET) {
                error(b, ParsingErrors.UNEXPECTED_TOKEN);
                b.mark().done(MQL4Elements.CLASS_INNER_BLOCK);
                return true;
            }
            b.advanceLexer(); // '{'
            if (!parseClassInnerBlock(b, l)) {
                advanceLexerUntil(b, ON_ERROR_CLASS_ADVANCE_TOKENS, ON_ERROR_CLASS_DO_NOT_ADVANCE_TOKENS);
                return true;
            }
            b.advanceLexer(); // '}'
        } finally {
            m.done(MQL4Elements.CLASS);
        }
        return true;
    }

    /**
     * {@code union Name} followed by its body, {@code pack(n)} or {@code ;}. {@code union} is reserved
     * in MQL5 but not in MQL4, so the lexer returns an IDENTIFIER and it is recognized here by text.
     */
    private static boolean isUnionStart(PsiBuilder b) {
        if (b.getTokenType() != IDENTIFIER || !"union".equals(b.getTokenText()) || b.lookAhead(1) != IDENTIFIER) {
            return false;
        }
        IElementType after = b.lookAhead(2);
        return after == L_CURLY_BRACKET || after == SEMICOLON || after == IDENTIFIER; // IDENTIFIER: pack(n)
    }

    /** Form: union name [pack(n)] { members } -- a CLASS node of kind Union (no inheritance, MQL5 reference). */
    private static boolean parseUnion(PsiBuilder b, int l) {
        Marker m = b.mark();
        try {
            b.remapCurrentToken(UNION_KEYWORD);
            b.advanceLexer(); // 'union'
            b.advanceLexer(); // name
            parsePackSpecifier(b, l);
            if (b.getTokenType() == SEMICOLON) {
                return true; // forward declaration
            }
            if (b.getTokenType() != L_CURLY_BRACKET) {
                error(b, ParsingErrors.UNEXPECTED_TOKEN);
                b.mark().done(MQL4Elements.CLASS_INNER_BLOCK);
                return true;
            }
            b.advanceLexer(); // '{'
            if (!parseClassInnerBlock(b, l)) {
                advanceLexerUntil(b, ON_ERROR_CLASS_ADVANCE_TOKENS, ON_ERROR_CLASS_DO_NOT_ADVANCE_TOKENS);
                return true;
            }
            b.advanceLexer(); // '}'
        } finally {
            m.done(MQL4Elements.CLASS);
        }
        return true;
    }

    /**
     * The alignment specifier {@code pack(n)} after a class, struct or union name (either side of
     * {@code final}). {@code pack} is not a reserved word in MQL5 ({@code int pack = 1;} compiles),
     * so it is matched by its text in this one position (and remapped to PACK_KEYWORD there) and left
     * an IDENTIFIER everywhere else.
     */
    private static void parsePackSpecifier(PsiBuilder b, int l) {
        if (b.getTokenType() == IDENTIFIER && "pack".equals(b.getTokenText())
                && b.lookAhead(1) == L_ROUND_BRACKET) {
            b.remapCurrentToken(PACK_KEYWORD);
            b.advanceLexer(); // 'pack'
            parseBracketsBlock(b, l + 1); // (n)
        }
    }

    /**
     * List = [Element]* {
     * Element = [Access] Identifier [,]
     */
    private static boolean parseInheritanceList(PsiBuilder b, int l) {
        int nItems = 0;
        PsiBuilder.Marker list = b.mark();
        try {
            while (true) {
                PsiBuilder.Marker inArg = b.mark();
                try {
                    IElementType t1 = b.getTokenType();
                    if (t1 == PRIVATE_KEYWORD || t1 == PROTECTED_KEYWORD || t1 == PUBLIC_KEYWORD) {
                        b.advanceLexer(); // 'private'
                    }
                    if (!TypesParsing.parseUserDataType(b, l)) {
                        error(b, ParsingErrors.UNEXPECTED_TOKEN);
                        return false;
                    }
                    nItems++;

                    IElementType t3 = b.getTokenType();
                    if (t3 == L_CURLY_BRACKET) {
                        break;
                    }
                    if (t3 != COMMA) {
                        error(b, ParsingErrors.UNEXPECTED_TOKEN);
                        return false;
                    }
                } finally {
                    inArg.done(MQL4Elements.CLASS_INHERITANCE_ITEM);
                }
                b.advanceLexer(); // ','
            }
        } finally {
            list.done(MQL4Elements.CLASS_INHERITANCE_LIST);
        }
        if (nItems == 0) {
            error(b, ParsingErrors.UNEXPECTED_TOKEN);
            return false;
        }
        return true;
    }

    /**
     * Form: as of today: set of anything until '}'
     */
    private static boolean parseClassInnerBlock(PsiBuilder b, int l) {
        Marker classInnerBlock = b.mark();
        ParsingScope.pushScope(b, ParsingScope.CLASS);
        try {
            while (b.getTokenType() != R_CURLY_BRACKET && !b.eof()) {
                boolean r = parseEmptyStatement(b)
                        || parseComment(b)
                        || parsePreprocessorBlock(b)
                        || TopLevelParsing.parseTemplateHeader(b)
                        || parseFunction(b)
                        || parseEnum(b, l + 1)
                        || parseClassOrStruct(b, l + 1)
                        // Phase 4 (REVAMP_PLAN.md #3b): class/struct member field declarations get
                        // named VAR_DEFINITION PSI too, using the same narrow/tolerant gate as
                        // locals and globals.
                        || parseLocalVarDeclaration(b, l + 1)
                        || parseBracketsBlock(b, l + 1);
                if (!r) {
                    b.advanceLexer();
                }
            }
            return !b.eof();
        } finally {
            classInnerBlock.done(CLASS_INNER_BLOCK);
            ParsingScope.popScope(b);
        }
    }

}
