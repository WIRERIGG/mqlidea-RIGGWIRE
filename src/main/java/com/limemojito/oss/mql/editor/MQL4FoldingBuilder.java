/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.lang.ASTNode;
import com.intellij.lang.folding.FoldingBuilder;
import com.intellij.lang.folding.FoldingDescriptor;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.DumbAware;
import com.intellij.openapi.util.Couple;
import com.intellij.openapi.util.TextRange;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.List;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.editor.folding.EnumFoldingDescriptor;
import com.limemojito.oss.mql.editor.folding.IncludeRunFoldingDescriptor;
import com.limemojito.oss.mql.editor.folding.RegionFoldingDescriptor;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

/**
 * MQL4 code folding: line/block comments, {@code {...}} code blocks, class bodies
 * ({@code CLASS_INNER_BLOCK}), enum bodies, {@code #region}/{@code #endregion} blocks and runs of
 * {@code >= 2} consecutive {@code #include} directives.
 */
public class MQL4FoldingBuilder implements FoldingBuilder, DumbAware {
    @NotNull
    @Override
    public FoldingDescriptor[] buildFoldRegions(@NotNull ASTNode node, @NotNull Document document) {
        final List<FoldingDescriptor> descriptors = new ArrayList<>();
        collectDescriptorsRecursively(node, document, descriptors);
        return descriptors.toArray(new FoldingDescriptor[0]);
    }

    private static void collectDescriptorsRecursively(@NotNull ASTNode node, @NotNull Document document, @NotNull List<FoldingDescriptor> descriptors) {
        ProgressManager.checkCanceled();
        IElementType type = node.getElementType();
        if (type == MQL4Elements.BLOCK_COMMENT) {
            descriptors.add(new FoldingDescriptor(node, node.getTextRange()));
        } else if (type == MQL4Elements.LINE_COMMENT) {
            // Process each LINE_COMMENT run ONCE: emit only at the run's first leaf and skip the rest
            // (each leaf otherwise re-scanned to both ends of the run and emitted a duplicate-range
            // descriptor — O(run^2)). The run boundary here is exactly the one
            // expandLineCommentsRange computes, so the surviving descriptor is byte-identical to the
            // first-leaf descriptor the old loop produced; the collapsed duplicates were the same
            // visible region.
            if (isLineCommentRunStart(node)) {
                Couple<PsiElement> commentRange = expandLineCommentsRange(node.getPsi());
                int startOffset = commentRange.getFirst().getTextRange().getStartOffset();
                int endOffset = commentRange.getSecond().getTextRange().getEndOffset() - 1;
                if (document.getLineNumber(startOffset) != document.getLineNumber(endOffset)) {
                    descriptors.add(new FoldingDescriptor(node, new TextRange(startOffset, endOffset)));
                }
            }
        } else if (type == MQL4Elements.BRACKETS_BLOCK && node.getFirstChildNode().getElementType() == MQL4Elements.L_CURLY_BRACKET) {
            if (!isNestedBlock(node)) {
                int startOffset = node.getFirstChildNode().getTextRange().getStartOffset();
                int endOffset = node.getLastChildNode().getTextRange().getEndOffset() - 1;
                if (document.getLineNumber(startOffset) != document.getLineNumber(endOffset)) {
                    descriptors.add(new FoldingDescriptor(node, new TextRange(startOffset, endOffset)));
                }
            }
        } else if (type == MQL4Elements.CLASS_INNER_BLOCK) {
            // P3: the class body is a CLASS_INNER_BLOCK, not a BRACKETS_BLOCK, so it wasn't foldable.
            ASTNode lBrace = node.findChildByType(MQL4Elements.L_CURLY_BRACKET);
            ASTNode rBrace = node.findChildByType(MQL4Elements.R_CURLY_BRACKET);
            if (lBrace != null && rBrace != null) {
                int startOffset = lBrace.getTextRange().getStartOffset();
                int endOffset = rBrace.getTextRange().getEndOffset() - 1;
                if (document.getLineNumber(startOffset) != document.getLineNumber(endOffset)) {
                    descriptors.add(new FoldingDescriptor(node, new TextRange(startOffset, endOffset)));
                }
            }
        } else if (type == MQL4Elements.ENUM_STATEMENT) {
            if (!isNestedBlock(node)) {
                //todo: do not fold if contains errors?
                descriptors.add(new EnumFoldingDescriptor(node));
            }
        }
        // Both #region/#endregion and runs of #include need sibling context (they aren't
        // single composite nodes), so scan this node's own children once per level rather than
        // per-child -- the recursive walk below already visits every level exactly once. Children
        // are walked via getFirstChildNode()/getTreeNext() to avoid the per-level array allocation
        // of getChildren(null).
        collectIncludeRunFolds(node, descriptors);
        collectRegionFolds(node, document, descriptors);
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            collectDescriptorsRecursively(child, document, descriptors);
        }
    }

    /**
     * True when {@code node} is the FIRST leaf of its {@code LINE_COMMENT} run, using the same run
     * boundary as {@link #findFurthestSiblingOfSameType}: a run continues across whitespace with no
     * embedded blank line and is broken by a blank-line whitespace, any non-comment/non-whitespace
     * token, or the start of the tree level. O(1) amortised (scans back only over the whitespace
     * separating it from the previous meaningful sibling), so a whole run costs O(run), not O(run^2).
     */
    private static boolean isLineCommentRunStart(@NotNull ASTNode node) {
        for (ASTNode prev = node.getTreePrev(); prev != null; prev = prev.getTreePrev()) {
            IElementType t = prev.getElementType();
            if (t == MQL4Elements.LINE_COMMENT) {
                return false; // an earlier member of the same run precedes this leaf
            }
            if (t == MQL4Elements.WHITE_SPACE) {
                if (prev.getText().indexOf('\n', 1) != -1) {
                    return true; // blank-line whitespace breaks the run (matches the sibling scan)
                }
                // indentation/single-newline whitespace: keep scanning back
            } else {
                return true; // any other token ends the run backward
            }
        }
        return true; // reached the start of this tree level
    }

    /**
     * Collapses a run of {@code >= 2} consecutive {@code PREPROCESSOR_INCLUDE_BLOCK} siblings
     * (ignoring whitespace/line-terminator gaps between them) into one fold.
     */
    private static void collectIncludeRunFolds(@NotNull ASTNode parent, @NotNull List<FoldingDescriptor> descriptors) {
        ASTNode child = parent.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() != MQL4Elements.PREPROCESSOR_INCLUDE_BLOCK) {
                child = child.getTreeNext();
                continue;
            }
            ASTNode first = child;
            ASTNode last = child;
            int count = 1;
            ASTNode j = child.getTreeNext();
            while (j != null) {
                IElementType t = j.getElementType();
                if (t == MQL4Elements.PREPROCESSOR_INCLUDE_BLOCK) {
                    count++;
                    last = j;
                    j = j.getTreeNext();
                } else if (t == MQL4Elements.WHITE_SPACE || t == MQL4Elements.LINE_TERMINATOR) {
                    j = j.getTreeNext();
                } else {
                    break;
                }
            }
            if (count >= 2) {
                TextRange range = new TextRange(first.getTextRange().getStartOffset(), last.getTextRange().getEndOffset());
                descriptors.add(new IncludeRunFoldingDescriptor(first, range, count));
            }
            child = j;
        }
    }

    /**
     * Matches {@code #region}/{@code #endregion} pairs among {@code children} (a single sibling
     * level) via a stack so nested regions fold independently; an unmatched {@code #endregion} (no
     * open region on the stack) or an unmatched trailing {@code #region} (never closed) is skipped
     * rather than folded.
     * <p/>
     * Neither directive is a first-class lexer token (see {@link RegionFoldingDescriptor}): a
     * {@code #region} start is recognised as a {@code BAD_CHARACTER('#')} leaf immediately
     * followed by an {@code IDENTIFIER("region")} leaf (ditto {@code "endregion"}); the region name
     * is whatever raw source text follows on the rest of that line.
     */
    private static void collectRegionFolds(@NotNull ASTNode parent, @NotNull Document document, @NotNull List<FoldingDescriptor> descriptors) {
        Deque<int[]> startOffsetStack = new ArrayDeque<>();
        Deque<String> nameStack = new ArrayDeque<>();
        ASTNode current = parent.getFirstChildNode();
        while (current != null) {
            ASTNode next = current.getTreeNext();
            if (next == null) {
                break; // need a (current, next) pair -- mirrors the old `i < length - 1` bound
            }
            if (!isHash(current) || next.getElementType() != MQL4Elements.IDENTIFIER) {
                current = next; // advance by one
                continue;
            }
            String keyword = next.getText();
            if ("region".equals(keyword)) {
                int nameStart = next.getTextRange().getEndOffset();
                String name = restOfLine(document, nameStart);
                startOffsetStack.push(new int[]{current.getTextRange().getStartOffset()});
                nameStack.push(name);
                current = next.getTreeNext(); // advance by two
            } else if ("endregion".equals(keyword)) {
                if (!startOffsetStack.isEmpty()) {
                    int startOffset = startOffsetStack.pop()[0];
                    String name = nameStack.pop();
                    int endOffset = next.getTextRange().getEndOffset();
                    if (document.getLineNumber(startOffset) != document.getLineNumber(endOffset - 1)) {
                        descriptors.add(new RegionFoldingDescriptor(current, new TextRange(startOffset, endOffset), name));
                    }
                }
                current = next.getTreeNext(); // advance by two
            } else {
                current = next; // advance by one
            }
        }
        // Any #region left on the stack here has no matching #endregion at this sibling level --
        // gracefully skipped (never added to descriptors).
    }

    private static boolean isHash(@NotNull ASTNode node) {
        return node.getElementType() == MQL4Elements.BAD_CHARACTER && "#".equals(node.getText());
    }

    @NotNull
    private static String restOfLine(@NotNull Document document, int offset) {
        if (offset >= document.getTextLength()) {
            return "";
        }
        int line = document.getLineNumber(offset);
        int lineEnd = document.getLineEndOffset(line);
        return document.getText(new TextRange(offset, Math.max(offset, lineEnd))).trim();
    }

    private static boolean isNestedBlock(@NotNull ASTNode node) {
        return findTopLevelOfType(node, MQL4Elements.BRACKETS_BLOCK) != null;
    }

    @Nullable
    private static ASTNode findTopLevelOfType(@NotNull ASTNode node, @NotNull IElementType type) {
        ASTNode parent = node.getTreeParent();
        while (parent != null) {
            if (parent.getElementType() == type) {
                return parent;
            }
            parent = parent.getTreeParent();
        }
        return null;
    }

    @Nullable
    @Override
    public String getPlaceholderText(@NotNull ASTNode node) {
        IElementType type = node.getElementType();
        if (type == MQL4Elements.LINE_COMMENT) {
            return "//...";
        } else if (type == MQL4Elements.BLOCK_COMMENT) {
            return "/*...*/";
        }
        return "...";
    }

    @Override
    public boolean isCollapsedByDefault(@NotNull ASTNode node) {
        return false;
    }

    @NotNull
    public static Couple<PsiElement> expandLineCommentsRange(@NotNull PsiElement anchor) {
        return Couple.of(findFurthestSiblingOfSameType(anchor, false), findFurthestSiblingOfSameType(anchor, true));
    }

    /**
     * Find the furthest sibling element with the same type as given anchor.
     * <p/>
     * Ignore white spaces for any type of element except {@link MQL4Elements#LINE_COMMENT}
     * where non indentation white space (that has new line in the middle) will stop the search.
     *
     * @param anchor element to start from
     * @param after  whether to scan through sibling elements forward or backward
     * @return described element or anchor if search stops immediately
     */
    @NotNull
    public static PsiElement findFurthestSiblingOfSameType(@NotNull PsiElement anchor, boolean after) {
        ASTNode node = anchor.getNode();
        // Compare by node type to distinguish between different types of comments
        IElementType expectedType = node.getElementType();
        ASTNode lastSeen = node;
        while (node != null) {
            IElementType elementType = node.getElementType();
            if (elementType == expectedType) {
                lastSeen = node;
            } else if (elementType == MQL4Elements.WHITE_SPACE) {
                if (expectedType == MQL4Elements.LINE_COMMENT && node.getText().indexOf('\n', 1) != -1) {
                    break;
                }
            } else if (!MQL4TokenSets.COMMENTS.contains(elementType) || MQL4TokenSets.COMMENTS.contains(expectedType)) {
                break;
            }
            node = after ? node.getTreeNext() : node.getTreePrev();
        }
        return lastSeen.getPsi();
    }
}
