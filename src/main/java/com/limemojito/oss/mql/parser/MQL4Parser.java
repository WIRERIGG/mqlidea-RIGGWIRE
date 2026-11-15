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

import static com.limemojito.oss.mql.parser.parsing.TopLevelParsing.parseTopLevelItem;

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
            if (!parseTopLevelItem(b, 0)) {
                b.advanceLexer();
            }
        }
        fileBlock.done(root);
    }
}
