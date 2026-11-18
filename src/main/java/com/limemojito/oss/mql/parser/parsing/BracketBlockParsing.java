/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing;

import com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorParsing;
import com.intellij.lang.PsiBuilder;
import com.intellij.psi.tree.IElementType;
import java.util.Stack;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.parser.parsing.statement.VarDeclarationStatement;
import com.limemojito.oss.mql.parser.parsing.util.ParsingErrors;
import com.limemojito.oss.mql.parser.parsing.util.ParsingScope;
import com.limemojito.oss.mql.parser.parsing.util.ParsingUtils;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import static com.intellij.lang.parser.GeneratedParserUtilBase.recursion_guard_;
import static com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment;
import static com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorIfDefParsing.parseDefine;
import static com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorIfDefParsing.parseUndef;
import static com.limemojito.oss.mql.parser.parsing.statement.EnumParsing.parseEnum;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseEmptyStatement;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseStatement;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.NO_MATCHING_CLOSING_BRACKET;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.advanceWithError;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.error;

public class BracketBlockParsing implements MQL4Elements {

    //TODO: Bracket blocks do not support #ifdef / #define parsing -> need global solution to fix this problem

    public static boolean parseBracketsBlock(PsiBuilder b, int l) {
        return parseBracketsBlock(b, l, false);
    }

    public static boolean parseBracketsBlock(PsiBuilder b, int l, boolean doNotParseContent) {
        return parseBracketsBlock(b, l, doNotParseContent, false);
    }

    /**
     * A {@code for} statement's {@code (...)} header. Same as a plain round-bracket block, except an
     * init-clause declaration ({@code for(int i=0; ...)}) is parsed as a real
     * {@code VAR_DECLARATION_STATEMENT}, so the loop variable is a named definition.
     */
    public static boolean parseForHeader(PsiBuilder b, int l) {
        return b.getTokenType() == L_ROUND_BRACKET && parseBracketsBlock(b, l, false, true);
    }

    private static boolean parseBracketsBlock(PsiBuilder b, int l, boolean doNotParseContent, boolean forHeader) {
        if (!ParsingUtils.nextTokenIn(b, l, "parseBracketBlock", MQL4TokenSets.BRACKETS)) {
            return false;
        }
        if (!recursion_guard_(b, l, "parseBracketsBlock")) {
            return false;
        }
        IElementType lBracket = b.getTokenType();
        assert lBracket != null;
        if (MQL4TokenSets.RIGHT_BRACKETS.contains(lBracket)) {
            advanceWithError(b, ParsingErrors.UNEXPECTED_TOKEN);
            return false;
        }

        PsiBuilder.Marker block = b.mark(); // starting new bracket section
        if (!hasMatchingClosingBracket(b, lBracket)) { // must check it here to set error on the correct position.
            error(b, NO_MATCHING_CLOSING_BRACKET);
        }
        b.advanceLexer(); // left bracket
        if (forHeader) {
            // init clause, through its ';'; a for-init is never a prototype, so CIter it(list) declares it
            VarDeclarationStatement.parseVarDeclaration(b, l + 1, true);
        }

        boolean codeBlock = lBracket == L_CURLY_BRACKET;
        if (codeBlock) {
            ParsingScope.pushScope(b, ParsingScope.CODE_BLOCK);
        }
        try {
            IElementType rBracket = MQL4TokenSets.getRightBracketFor(lBracket);
            while (!b.eof()) { // now parse sub-blocks one by one. Stop on closing bracket
                IElementType t = b.rawLookup(0);
                assert t != null;
                if (t == rBracket) {
                    b.advanceLexer(); // right bracket
                    return true;
                }
                if (MQL4TokenSets.RIGHT_BRACKETS.contains(t)) { // different kind of right bracket
                    advanceWithError(b, ParsingErrors.UNEXPECTED_TOKEN);
                    continue;
                }
                boolean res;
                if (doNotParseContent) {
                    res = parseBracketsBlock(b, l + 1, true);
                } else if (codeBlock) {
                    // {} code block: parse real statements. parseStatement is tolerant — it either
                    // consumes a statement or returns false so the advanceLexer() fallback below
                    // keeps the old behavior for anything unrecognized.
                    res = parseEnum(b, l + 1)
                            || parseDefine(b)
                            || parseUndef(b)
                            || parseConditionalDirective(b)
                            || parseStatement(b, l + 1)
                            || parseBracketsBlock(b, l + 1, false)
                            || parseEmptyStatement(b)
                            || parseComment(b);
                } else {
                    res = parseEnum(b, l + 1)
                            || parseDefine(b)
                            || parseUndef(b)
                            || parseBracketsBlock(b, l + 1, false)
                            || parseEmptyStatement(b)
                            || parseComment(b);
                }
                if (!res) { // if not parsed -> consume the element
                    b.advanceLexer();
                }
            }
            return true;
        } finally {
            if (codeBlock) {
                ParsingScope.popScope(b);
            }
            block.done(BRACKETS_BLOCK);
        }
    }

    /**
     * {@code #ifdef NAME} / {@code #ifndef NAME} inside a code block: the keyword and the name on its
     * line stay flat tokens, as at file level. Without this the name started the next statement, so
     * {@code #ifdef DEBUG} followed by {@code string t = ...;} read as one expression and lost the
     * declaration of {@code t}.
     */
    private static boolean parseConditionalDirective(@NotNull PsiBuilder b) {
        IElementType t = b.getTokenType();
        if (t != IFDEF_PP_KEYWORD && t != IFNDEF_PP_KEYWORD) {
            return false;
        }
        int end = b.getCurrentOffset() + (b.getTokenText() == null ? 0 : b.getTokenText().length());
        b.advanceLexer(); // '#ifdef' | '#ifndef'
        if (b.getTokenType() == IDENTIFIER
                && !PreprocessorParsing.hasLineBreaks(b, end, b.getCurrentOffset())) {
            b.advanceLexer(); // the condition name
        }
        return true;
    }

    private static boolean hasMatchingClosingBracket(@NotNull PsiBuilder b, @NotNull IElementType lBracket) {
        IElementType rBracket = MQL4TokenSets.getRightBracketFor(lBracket);
        Stack<IElementType> lStack = new Stack<>();
        for (int i = 1; ; i++) {
            IElementType e = b.rawLookup(i);
            if (e == null) { // right bracket not found.
                return false;
            }
            if (!MQL4TokenSets.BRACKETS.contains(e)) { // ignore non-bracket elements
                continue;
            }
            if (MQL4TokenSets.LEFT_BRACKETS.contains(e)) { // new bracket block
                lStack.push(e);
                continue;
            }
            // e is a right bracket here.
            if (e == rBracket && lStack.isEmpty()) { // the bracket we need
                return true;
            }
            // pop bracket for well-formed nested block
            if (!lStack.isEmpty() && lStack.peek() == MQL4TokenSets.getLeftBracketFor(e)) {
                lStack.pop();
            } // else the error will be handled when corresponding nested block is parsed
        }
    }

}
