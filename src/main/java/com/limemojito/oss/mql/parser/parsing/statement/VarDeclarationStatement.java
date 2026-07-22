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
import com.limemojito.oss.mql.parser.parsing.util.ParsingErrors;
import com.limemojito.oss.mql.parser.parsing.util.ParsingUtils;
import com.limemojito.oss.mql.parser.parsing.util.TokenAdvanceMode;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import static com.intellij.lang.parser.GeneratedParserUtilBase.recursion_guard_;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.error;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingUtils.checkTokenOrFail;

public class VarDeclarationStatement implements MQL4Elements {

    private static final TokenSet PRE_TYPES = TokenSet.create(CONST_KEYWORD, EXTERN_KEYWORD, INPUT_KEYWORD, SINPUT_KEYWORD, STATIC_KEYWORD);

    public static boolean parseVarDeclaration(PsiBuilder b, int l) {
        if (!recursion_guard_(b, l, "parseVarDeclaration")) {
            return false;
        }
        int n = 0;
        if (PRE_TYPES.contains(b.lookAhead(n))) {
            n++;
        }
        boolean firstIsType = MQL4TokenSets.DATA_TYPES.contains(b.lookAhead(n));
        if (!(firstIsType && b.lookAhead(n + 1) == IDENTIFIER)) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        if (n == 1) {
            skipComments(b);
            b.advanceLexer(); // pre-type
        }
        skipComments(b);
        b.advanceLexer(); // type
        skipComments(b);
        boolean ok = parseVarDefinitionList(b, l + 1);
        if (!ok) {
            ParsingUtils.advanceLexerUntil(b, SEMICOLON, TokenAdvanceMode.ADVANCE);
        }
        m.done(VAR_DECLARATION_STATEMENT);
        return true;
    }

    public static boolean parseVarDefinitionList(PsiBuilder b, int l) {
        assert b.getTokenType() == IDENTIFIER;
        PsiBuilder.Marker m0 = b.mark();
        try {
            boolean ok = true;
            do {
                PsiBuilder.Marker m1 = b.mark();
                try {
                    b.advanceLexer();
                    skipComments(b);
                    if (b.getTokenType() == SEMICOLON) {
                        b.advanceLexer();
                        break;
                    }
                    if (b.getTokenType() == COMMA) {
                        continue;
                    }
                    if (b.getTokenType() == EQ) {
                        b.advanceLexer();
                        ok = false;//TODO: parseExpressionOrFail(b, l + 1);
                        if (ok && b.getTokenType() == SEMICOLON) {
                            b.advanceLexer();
                            break;
                        }
                    } else {
                        error(b, ParsingErrors.UNEXPECTED_TOKEN);
                        ok = false;
                    }
                } finally {
                    m1.done(VAR_DEFINITION);
                }
            } while (ok && b.getTokenType() == IDENTIFIER);
            return ok;
        } finally {
            m0.done(VAR_DEFINITION_LIST);
        }
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
