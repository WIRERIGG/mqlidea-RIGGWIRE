/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing;

import com.intellij.lang.PsiBuilder;
import com.intellij.psi.tree.IElementType;
import com.limemojito.oss.mql.psi.MQL4Elements;

import static com.intellij.lang.parser.GeneratedParserUtilBase.recursion_guard_;
import static com.limemojito.oss.mql.parser.parsing.BracketBlockParsing.parseBracketsBlock;
import static com.limemojito.oss.mql.parser.parsing.ClassParsing.parseClassOrStruct;
import static com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment;
import static com.limemojito.oss.mql.parser.parsing.FunctionsParsing.parseFunction;
import static com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorParsing.parsePreprocessorBlock;
import static com.limemojito.oss.mql.parser.parsing.statement.EnumParsing.parseEnum;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseLocalVarDeclaration;

/** File-level declarations, shared by the file and by {@code namespace} bodies. */
public class TopLevelParsing implements MQL4Elements {

    /** Parses one file-level item; false when nothing matched (the caller then skips a token). */
    public static boolean parseTopLevelItem(PsiBuilder b, int l) {
        return parseComment(b)
                || parsePreprocessorBlock(b)
                || parseNamespace(b, l)
                || parseInputGroup(b)
                || parseFunction(b)
                || parseEnum(b, l)
                || parseClassOrStruct(b, l)
                // Phase 4 (REVAMP_PLAN.md #3b): global variable declarations get the same
                // named VAR_DECLARATION_STATEMENT/VAR_DEFINITION structure locals already get,
                // so globals become resolvable/renamable named PSI too. Reuses the exact same
                // narrow, tolerant, already-proven-safe gate used inside {} blocks.
                || parseLocalVarDeclaration(b, l)
                || parseBracketsBlock(b, l);
    }

    /**
     * Form: namespace Name { top-level items }. The body is a NAMESPACE_BODY, not a code block, so
     * functions, classes, enums and globals inside get the same PSI as at file level.
     */
    private static boolean parseNamespace(PsiBuilder b, int l) {
        if (b.getTokenType() != NAMESPACE_KEYWORD || b.lookAhead(1) != IDENTIFIER || b.lookAhead(2) != L_CURLY_BRACKET) {
            return false;
        }
        if (!recursion_guard_(b, l, "parseNamespace")) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'namespace'
        b.advanceLexer(); // name
        PsiBuilder.Marker body = b.mark();
        b.advanceLexer(); // '{'
        while (!b.eof() && b.getTokenType() != R_CURLY_BRACKET) {
            if (!parseTopLevelItem(b, l + 1)) {
                b.advanceLexer();
            }
        }
        if (b.getTokenType() == R_CURLY_BRACKET) {
            b.advanceLexer(); // '}'
        }
        body.done(NAMESPACE_BODY);
        m.done(NAMESPACE_BLOCK);
        return true;
    }

    /**
     * Form: input group "Title" [;]. A heading in the inputs dialog, not a variable. {@code group}
     * isn't reserved ({@code int group = 1;} compiles), so it is recognized by text here.
     */
    private static boolean parseInputGroup(PsiBuilder b) {
        IElementType t = b.getTokenType();
        if ((t != INPUT_KEYWORD && t != SINPUT_KEYWORD) || b.lookAhead(1) != IDENTIFIER || b.lookAhead(2) != STRING_LITERAL) {
            return false;
        }
        PsiBuilder.Marker m = b.mark();
        b.advanceLexer(); // 'input'
        if (!"group".equals(b.getTokenText())) {
            m.rollbackTo();
            return false;
        }
        b.remapCurrentToken(GROUP_KEYWORD);
        b.advanceLexer(); // 'group'
        b.advanceLexer(); // "Title"
        if (b.getTokenType() == SEMICOLON) {
            b.advanceLexer();
        }
        m.done(INPUT_GROUP);
        return true;
    }
}
