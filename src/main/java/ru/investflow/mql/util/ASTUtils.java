/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.util;

import com.intellij.lang.ASTNode;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import ru.investflow.mql.psi.MQL4TokenSets;

public class ASTUtils {

    @Nullable
    public static ASTNode findLastPrevByType(@NotNull ASTNode node, @NotNull IElementType type) {
        ASTNode prev = node;
        do {
            prev = prev.getTreePrev();
            if (prev != null && prev.getElementType() == type) {
                return prev;
            }
        } while (prev != null);
        return null;
    }

    @Nullable
    public static ASTNode findLastChildByType(@NotNull ASTNode node, @NotNull IElementType type) {
        ASTNode child = node.getLastChildNode();
        while (child != null) {
            if (child.getElementType() == type) {
                return child;
            }
            child = child.getTreePrev();
        }
        return null;
    }

    @Nullable
    public static ASTNode getPrevIgnoreCommentsAndWs(ASTNode node) {
        ASTNode prev = node;
        while (true) {
            prev = prev.getTreePrev();
            if (prev == null || !MQL4TokenSets.COMMENTS_OR_WS.contains(prev.getElementType())) {
                return prev;
            }
        }
    }
}
