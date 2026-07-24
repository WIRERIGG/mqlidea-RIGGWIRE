/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.formatter;

import com.intellij.formatting.Block;
import com.intellij.formatting.ChildAttributes;
import com.intellij.formatting.Indent;
import com.intellij.formatting.Spacing;
import com.intellij.formatting.SpacingBuilder;
import com.intellij.lang.ASTNode;
import com.intellij.psi.TokenType;
import com.intellij.psi.codeStyle.CodeStyleSettings;
import com.intellij.psi.codeStyle.CommonCodeStyleSettings;
import com.intellij.psi.formatter.common.AbstractBlock;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import java.util.ArrayList;
import java.util.List;

/**
 * Formatting {@link Block} over the MQL4/MQL5 AST. This mirrors the structural idioms documented
 * on {@code com.limemojito.oss.mql.inspection.StatementAst}: a {@code BRACKETS_BLOCK} node is used
 * for both {@code {...}} code blocks and {@code (...)} groups (condition / call args), and the two
 * are told apart by their first child token ({@code '{'} vs {@code '('}).
 *
 * <h2>Indent policy (conservative -- indentation only, no reflow/wrapping)</h2>
 * <ul>
 *   <li>Inside a {@code {...}} {@code BRACKETS_BLOCK} (a real code block): the braces themselves
 *       stay at the block's own level; every other child (statement, comment) gets one normal
 *       indent. Nested {@code {...}} blocks stack, so indentation accumulates with nesting depth
 *       (an {@code if} inside a function inside a class ends up three levels deep).</li>
 *   <li>Inside a {@code CLASS_INNER_BLOCK} (the body of a class/struct/interface -- note its
 *       surrounding {@code {}} tokens are siblings on the owning {@code CLASS} node, not children
 *       of this wrapper): every child gets one normal indent, for the same reason.</li>
 *   <li>The brace-less single-statement body of a control-flow statement
 *       ({@code if (x)}<br>{@code &nbsp;&nbsp;&nbsp;return;}) gets one normal indent: the parser
 *       models the body as a direct child of the {@code IF/FOR/WHILE/DO_STATEMENT} node (see
 *       {@link #isBraceLessBody}), so this needs no control-flow analysis. An {@code else if}
 *       continuation stays aligned with the outer {@code if}.</li>
 *   <li>Everywhere else (condition/argument {@code (...)} groups, declarations, the file root, ...):
 *       no extra indent. This plugin does not reflow or wrap expressions -- see REVAMP_PLAN.md
 *       Phase 7's "keep it conservative" constraint.</li>
 * </ul>
 */
final class MQL4Block extends AbstractBlock implements MQL4Elements {

    // Control-flow statement nodes whose brace-less single-statement body should be indented.
    private static final TokenSet CONTROL_FLOW_STATEMENTS =
            TokenSet.create(IF_STATEMENT, FOR_STATEMENT, WHILE_STATEMENT, DO_STATEMENT, SWITCH_STATEMENT);
    // Keyword tokens that appear as direct children of a control-flow statement (they, the
    // condition group and a braced body stay at the statement's own level, never indented).
    private static final TokenSet CONTROL_KEYWORDS =
            TokenSet.create(IF_KEYWORD, ELSE_KEYWORD, FOR_KEYWORD, WHILE_KEYWORD, DO_KEYWORD, SWITCH_KEYWORD);

    private final CodeStyleSettings settings;
    private final SpacingBuilder spacingBuilder;

    MQL4Block(@NotNull ASTNode node, @NotNull CodeStyleSettings settings, @NotNull SpacingBuilder spacingBuilder) {
        super(node, null, null);
        this.settings = settings;
        this.spacingBuilder = spacingBuilder;
    }

    @Override
    protected List<Block> buildChildren() {
        List<Block> blocks = new ArrayList<>();
        for (ASTNode child = myNode.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType type = child.getElementType();
            if (type == TokenType.WHITE_SPACE || type == LINE_TERMINATOR) {
                continue; // whitespace is not modeled as a block -- Spacing recreates it
            }
            if (child.getTextRange().isEmpty()) {
                continue; // defensive: some error-recovery marker nodes can be empty
            }
            blocks.add(new MQL4Block(child, settings, spacingBuilder));
        }
        return blocks;
    }

    @Override
    public Indent getIndent() {
        ASTNode parent = myNode.getTreeParent();
        if (parent == null) {
            return Indent.getNoneIndent();
        }
        IElementType parentType = parent.getElementType();
        if (parentType == BRACKETS_BLOCK && isCodeBlock(parent)) {
            IElementType myType = myNode.getElementType();
            if (myType == L_CURLY_BRACKET || myType == R_CURLY_BRACKET) {
                return Indent.getNoneIndent();
            }
            return Indent.getNormalIndent();
        }
        if (parentType == CLASS_INNER_BLOCK) {
            return Indent.getNormalIndent();
        }
        if (CONTROL_FLOW_STATEMENTS.contains(parentType) && isBraceLessBody()) {
            return Indent.getNormalIndent();
        }
        return Indent.getNoneIndent();
    }

    /**
     * True when this node is the brace-less single-statement body of its enclosing control-flow
     * statement — {@code if (c) <this>;}, {@code else <this>}, {@code for (…) <this>;},
     * {@code while (…) <this>;}, {@code do <this> while(…);} — and so should be indented one level.
     * <p>
     * Excluded (they stay at the control statement's own level): the control keyword(s); the
     * condition/braced-body {@code BRACKETS_BLOCK} (a {@code (…)} group is inline, a {@code {…}} body
     * is indented by its own children via the code-block rule); the do-while trailing {@code ';'};
     * and an {@code else if} continuation — an {@code IF_STATEMENT} directly after an
     * {@code ELSE_KEYWORD} aligns with the outer {@code if} rather than indenting like a nested body.
     */
    private boolean isBraceLessBody() {
        IElementType myType = myNode.getElementType();
        if (CONTROL_KEYWORDS.contains(myType) || myType == BRACKETS_BLOCK || myType == SEMICOLON) {
            return false;
        }
        if (myType == IF_STATEMENT && prevNonTriviaType(myNode) == ELSE_KEYWORD) {
            return false; // `else if` — keep aligned with the outer if
        }
        return true;
    }

    /** Element type of the nearest preceding non-whitespace/non-comment sibling, or null. */
    @Nullable
    private static IElementType prevNonTriviaType(@NotNull ASTNode node) {
        for (ASTNode prev = node.getTreePrev(); prev != null; prev = prev.getTreePrev()) {
            IElementType t = prev.getElementType();
            if (t == TokenType.WHITE_SPACE || t == LINE_TERMINATOR || MQL4TokenSets.COMMENTS_OR_WS.contains(t)) {
                continue;
            }
            return t;
        }
        return null;
    }

    @Nullable
    @Override
    public Spacing getSpacing(@Nullable Block child1, Block child2) {
        if (child1 instanceof MQL4Block && child2 instanceof MQL4Block) {
            ASTNode rightNode = ((MQL4Block) child2).getNode();
            if (isCodeBlock(rightNode)) {
                // The '{' of a nested code block is the first token *inside* that block's own
                // Block, so it never shows up as a direct sibling for a plain token-pair spacing
                // rule below -- handle it here instead. Don't force a line break (Allman-style
                // braces on their own line are left alone), but require exactly one space when
                // the brace is on the same line as what precedes it.
                CommonCodeStyleSettings common = settings.getCommonSettings(MQL4Language.INSTANCE);
                return Spacing.createSpacing(1, 1, 0, true, common.KEEP_BLANK_LINES_IN_CODE);
            }
        }
        return spacingBuilder.getSpacing(this, child1, child2);
    }

    @Override
    public ChildAttributes getChildAttributes(int newChildIndex) {
        IElementType myType = myNode.getElementType();
        if (myType == CLASS_INNER_BLOCK || (myType == BRACKETS_BLOCK && isCodeBlock(myNode))) {
            return new ChildAttributes(Indent.getNormalIndent(), null);
        }
        return new ChildAttributes(Indent.getNoneIndent(), null);
    }

    @Override
    public boolean isLeaf() {
        return myNode.getFirstChildNode() == null;
    }

    /** True for a {@code BRACKETS_BLOCK} node that is a {@code {...}} code block (first child is '{'). */
    static boolean isCodeBlock(@NotNull ASTNode bracketsBlock) {
        if (bracketsBlock.getElementType() != BRACKETS_BLOCK) {
            return false;
        }
        ASTNode first = bracketsBlock.getFirstChildNode();
        return first != null && first.getElementType() == L_CURLY_BRACKET;
    }
}
