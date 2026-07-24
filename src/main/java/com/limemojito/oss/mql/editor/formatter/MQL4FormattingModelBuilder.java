/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.formatter;

import com.intellij.formatting.FormattingContext;
import com.intellij.formatting.FormattingModel;
import com.intellij.formatting.FormattingModelBuilder;
import com.intellij.formatting.FormattingModelProvider;
import com.intellij.formatting.SpacingBuilder;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiFile;
import com.intellij.psi.codeStyle.CodeStyleSettings;
import com.intellij.psi.codeStyle.CommonCodeStyleSettings;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.MQL4Elements;

/**
 * Phase 7 (REVAMP_PLAN.md #Phase 7) formatter entry point: builds the {@link MQL4Block} tree
 * (indentation) and the {@link SpacingBuilder} rules (basic, conservative spacing) for a file.
 *
 * <p>Spacing rules cover: comma, semicolon, assignment/equality/relational/logical operators
 * (deliberately <b>excluding</b> {@code + - * / % & | ^ ~ !} -- in this grammar's flat statement
 * AST those tokens are ambiguous between a binary operator and a unary/reference/pointer-ish
 * marker -- e.g. {@code -1}, {@code Type &param}, {@code Type *param} -- and forcing spacing
 * around them risks mangling code we can't structurally tell apart from a plain token stream; see
 * REVAMP_PLAN.md Phase 7's "keep it conservative" constraint), control-keyword-before-condition
 * parentheses, call/declaration parentheses, and space-before-brace.</p>
 */
public final class MQL4FormattingModelBuilder implements FormattingModelBuilder, MQL4Elements {

    @Override
    public @NotNull FormattingModel createModel(@NotNull FormattingContext context) {
        PsiFile file = context.getContainingFile();
        CodeStyleSettings settings = context.getCodeStyleSettings();
        ASTNode root = file.getNode();
        SpacingBuilder spacingBuilder = createSpacingBuilder(settings);
        MQL4Block rootBlock = new MQL4Block(root, settings, spacingBuilder);
        return FormattingModelProvider.createFormattingModelForPsiFile(file, rootBlock, settings);
    }

    @NotNull
    private static SpacingBuilder createSpacingBuilder(@NotNull CodeStyleSettings settings) {
        CommonCodeStyleSettings common = settings.getCommonSettings(MQL4Language.INSTANCE);

        TokenSet assignmentOps = TokenSet.create(
                EQ, PLUS_EQ, MINUS_EQ, MUL_EQ, DIV_EQ, MOD_EQ,
                AND_EQ, OR_EQ, XOR_EQ, TILDA_EQ, POW_EQ, SH_LEFT_EQ, SH_RIGHT_EQ, USH_RIGHT_EQ);
        TokenSet logicalOps = TokenSet.create(BOOL_AND, BOOL_OR);
        TokenSet equalityOps = TokenSet.create(EQ_EQ, NOT_EQ);
        TokenSet relationalOps = TokenSet.create(LT, GT, LESS_EQ, GT_EQ);
        TokenSet bracketsBlockSet = TokenSet.create(BRACKETS_BLOCK);

        return new SpacingBuilder(settings, MQL4Language.INSTANCE)
                .after(COMMA).spaceIf(common.SPACE_AFTER_COMMA)
                .before(COMMA).spaceIf(common.SPACE_BEFORE_COMMA)
                .before(SEMICOLON).spaceIf(false)
                .around(assignmentOps).spaceIf(common.SPACE_AROUND_ASSIGNMENT_OPERATORS)
                .around(logicalOps).spaceIf(common.SPACE_AROUND_LOGICAL_OPERATORS)
                .around(equalityOps).spaceIf(common.SPACE_AROUND_EQUALITY_OPERATORS)
                .around(relationalOps).spaceIf(common.SPACE_AROUND_RELATIONAL_OPERATORS)
                // control-keyword '(' condition -- the '(' itself is the first token of the
                // BRACKETS_BLOCK sibling that follows the keyword, never a direct sibling token,
                // so each rule targets the BRACKETS_BLOCK as a whole (see MQL4Block's javadoc).
                .between(TokenSet.create(IF_KEYWORD), bracketsBlockSet).spaceIf(common.SPACE_BEFORE_IF_PARENTHESES)
                .between(TokenSet.create(FOR_KEYWORD), bracketsBlockSet).spaceIf(common.SPACE_BEFORE_FOR_PARENTHESES)
                .between(TokenSet.create(WHILE_KEYWORD), bracketsBlockSet).spaceIf(common.SPACE_BEFORE_WHILE_PARENTHESES)
                .between(TokenSet.create(SWITCH_KEYWORD), bracketsBlockSet).spaceIf(common.SPACE_BEFORE_SWITCH_PARENTHESES)
                // call args: IDENTIFIER directly followed by a (...) BRACKETS_BLOCK.
                .between(TokenSet.create(IDENTIFIER), bracketsBlockSet).spaceIf(common.SPACE_BEFORE_METHOD_CALL_PARENTHESES)
                // function/constructor/destructor declaration parens are raw sibling tokens
                // (not wrapped in a BRACKETS_BLOCK) -- see FunctionsParsing.
                .between(TokenSet.create(IDENTIFIER), TokenSet.create(L_ROUND_BRACKET)).spaceIf(common.SPACE_BEFORE_METHOD_PARENTHESES)
                // class/struct/interface body brace: a genuine direct sibling token on the CLASS
                // node (unlike a code block's brace, which MQL4Block.getSpacing handles specially).
                .before(L_CURLY_BRACKET).spaceIf(true);
    }
}
