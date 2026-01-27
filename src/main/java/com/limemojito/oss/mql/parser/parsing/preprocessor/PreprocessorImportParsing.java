/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser.parsing.preprocessor;

import com.intellij.lang.PsiBuilder;
import com.intellij.psi.tree.IElementType;
import com.limemojito.oss.mql.psi.stub.MQL4StubElements;
import com.limemojito.oss.mql.parser.parsing.util.ParsingUtils;
import com.limemojito.oss.mql.parser.parsing.util.TokenAdvanceMode;
import com.limemojito.oss.mql.psi.MQL4Elements;

import static com.intellij.lang.parser.GeneratedParserUtilBase.enter_section_;
import static com.intellij.lang.parser.GeneratedParserUtilBase.exit_section_;
import static com.intellij.lang.parser.GeneratedParserUtilBase.nextTokenIs;
import static com.limemojito.oss.mql.parser.parsing.FunctionsParsing.FunctionParsingResult.Declaration;
import static com.limemojito.oss.mql.parser.parsing.FunctionsParsing.parseFunction;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingErrors.error;
import static com.limemojito.oss.mql.parser.parsing.util.ParsingUtils.advanceLexerUntil;
import static com.limemojito.oss.mql.parser.parsing.util.TokenAdvanceMode.ADVANCE;

public class PreprocessorImportParsing implements MQL4Elements {

    public static boolean parseImport(PsiBuilder b, int l) {
        if (!ParsingUtils.nextTokenIs(b, l, "parseImport", IMPORT_PP_KEYWORD)) {
            return false;
        }
        PsiBuilder.Marker m = enter_section_(b);
        int importOffset = b.getCurrentOffset();
        b.advanceLexer();
        try {
            if (ParsingUtils.containsEndOfLineOrFile(b, importOffset)) { // block is finished. Nothing to parse.
                return true;
            }
            // the only parameter must be string literal
            int literalOffset = b.getCurrentOffset();
            IElementType tt = b.getTokenType();
            if (tt != STRING_LITERAL) {
                error(b, "String literal is expected!");
                advanceLexerUntil(b, LINE_TERMINATOR, TokenAdvanceMode.DO_NOT_ADVANCE);
                return true;
            }
            b.advanceLexer();

            // check that there are no other tokens till the eol
            if (!ParsingUtils.containsEndOfLineOrFile(b, literalOffset)) {
                error(b, "New line is expected!");
                advanceLexerUntil(b, LINE_TERMINATOR, TokenAdvanceMode.DO_NOT_ADVANCE);
                return true;
            }
            // now parse function declaration until the next import block
            while (!nextTokenIs(b, IMPORT_PP_KEYWORD)) {
                forceParseDeclaration(b, l + 1);
            }
        } finally {
            exit_section_(b, m, PREPROCESSOR_IMPORT_BLOCK, true);
        }
        return true;
    }

    public static boolean forceParseDeclaration(PsiBuilder b, int l) {
        if (parseFunction(b, l, Declaration) == Declaration) {
            return true;
        }
        PsiBuilder.Marker m = enter_section_(b);
        error(b, "Function declaration expected!");
        advanceLexerUntil(b, SEMICOLON, ADVANCE);
        exit_section_(b, m, MQL4StubElements.FUNCTION_DECLARATION, true);
        return false;
    }

}
