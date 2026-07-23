/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.parser;

import com.intellij.lang.ASTNode;
import com.intellij.lang.LighterASTNode;
import com.intellij.lang.PsiBuilder;
import com.intellij.lang.PsiParser;
import com.intellij.psi.tree.IElementType;
import com.intellij.util.diff.FlyweightCapableTreeStructure;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.psi.MQL4Elements;

import static com.limemojito.oss.mql.parser.parsing.BracketBlockParsing.parseBracketsBlock;
import static com.limemojito.oss.mql.parser.parsing.ClassParsing.parseClassOrStruct;
import static com.limemojito.oss.mql.parser.parsing.CommentParsing.parseComment;
import static com.limemojito.oss.mql.parser.parsing.FunctionsParsing.parseFunction;
import static com.limemojito.oss.mql.parser.parsing.preprocessor.PreprocessorParsing.parsePreprocessorBlock;
import static com.limemojito.oss.mql.parser.parsing.statement.EnumParsing.parseEnum;
import static com.limemojito.oss.mql.parser.parsing.statement.StatementParsing.parseLocalVarDeclaration;

public class MQL4Parser implements PsiParser, MQL4Elements {

    @NotNull
    public ASTNode parse(@NotNull IElementType root, @NotNull PsiBuilder b) {
        doParse(root, b);
        return b.getTreeBuilt();
    }

    @NotNull
    public FlyweightCapableTreeStructure<LighterASTNode> parseLight(IElementType root, PsiBuilder builder) {
        doParse(root, builder);
        return builder.getLightTree();
    }

    private void doParse(@NotNull IElementType root, @NotNull PsiBuilder b) {
        PsiBuilder.Marker fileBlock = b.mark();
        while (!b.eof()) {
            boolean r = parseComment(b)
                    || parsePreprocessorBlock(b)
                    || parseFunction(b)
                    || parseEnum(b, 0)
                    || parseClassOrStruct(b, 0)
                    // Phase 4 (REVAMP_PLAN.md #3b): global variable declarations get the same
                    // named VAR_DECLARATION_STATEMENT/VAR_DEFINITION structure locals already get,
                    // so globals become resolvable/renamable named PSI too. Reuses the exact same
                    // narrow, tolerant, already-proven-safe gate used inside {} blocks.
                    || parseLocalVarDeclaration(b, 0)
                    || parseBracketsBlock(b, 0);
            if (!r) {
                b.advanceLexer();
            }
        }
        fileBlock.done(root);
    }
}
