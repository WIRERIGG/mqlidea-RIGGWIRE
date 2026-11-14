/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.PsiTreeUtil;
import com.limemojito.oss.mql.MqlBuiltinFunctions;
import com.limemojito.oss.mql.MqlBuiltinTypes;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.function.Consumer;

/** What the "undeclared identifier" inspections share: which identifiers they look at, and built-ins. */
final class UndeclaredNames {

    /** Blocks whose identifiers aren't checked: macro bodies and #import declarations can name anything. */
    private static final TokenSet SKIPPED_BLOCKS = TokenSet.create(MQL4Elements.PREPROCESSOR_DEFINE_BLOCK,
            MQL4Elements.PREPROCESSOR_IMPORT_BLOCK, MQL4Elements.OPERATOR_NAME, MQL4Elements.PREPROCESSOR_PROPERTY_BLOCK,
            MQL4Elements.PREPROCESSOR_INCLUDE_BLOCK, MQL4Elements.PREPROCESSOR_UNDEF_BLOCK, MQL4Elements.TYPE_TEMPLATE_BLOCK);

    /** A name after one of these is a declaration ({@code int x}, {@code class C}, {@code enum E}). */
    private static final TokenSet DECLARING = TokenSet.orSet(MQL4TokenSets.DATA_TYPES, TokenSet.create(
            MQL4Elements.IDENTIFIER, MQL4Elements.TILDA, MQL4Elements.UNION_KEYWORD, MQL4Elements.TYPENAME_KEYWORD));

    /** After a {@code *} or {@code &} declarator, these end a declared name: {@code T *p = ...}, {@code f(T &a, ...)}. */
    private static final TokenSet AFTER_DECLARED_NAME = TokenSet.create(MQL4Elements.EQ, MQL4Elements.COMMA,
            MQL4Elements.R_ROUND_BRACKET, MQL4Elements.SEMICOLON, MQL4Elements.L_SQUARE_BRACKET);

    private UndeclaredNames() {
    }

    /** A missing header could declare any name, so a file with one isn't checked at all. */
    static boolean hasUnresolvedInclude(@NotNull PsiFile file) {
        for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(file, MQL4PreprocessorIncludeBlock.class)) {
            if (include.resolveIncludedFile() == null) {
                return true;
            }
        }
        return false;
    }

    /** Every IDENTIFIER outside the skipped blocks and the {@code #ifdef}/{@code #ifndef} condition names. */
    static void forEachIdentifier(@NotNull PsiFile file, @NotNull Consumer<ASTNode> action) {
        visit(file.getNode(), action);
    }

    private static void visit(@NotNull ASTNode node, @NotNull Consumer<ASTNode> action) {
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType type = child.getElementType();
            if (SKIPPED_BLOCKS.contains(type)) {
                continue;
            }
            if (type == MQL4Elements.IDENTIFIER) {
                IElementType prev = prevType(child);
                if (prev != MQL4Elements.IFDEF_PP_KEYWORD && prev != MQL4Elements.IFNDEF_PP_KEYWORD) {
                    action.accept(child);
                }
            } else if (child.getFirstChildNode() != null) {
                visit(child, action);
            }
        }
    }

    static boolean isBuiltin(@NotNull String name) {
        return MQL4DocumentationProvider.getEntryByText(name) != null || MqlBuiltinFunctions.isBuiltinName(name)
                || MqlBuiltinTypes.MQL5_TYPES.contains(name) || "offsetof".equals(name);
    }

    /**
     * True for the name a declaration introduces rather than a use: a function, parameter, variable,
     * class or enum name ({@code int x}, {@code CFoo obj(1)}, {@code T *p = NULL}, {@code ~CFoo()}).
     */
    static boolean isDeclarationName(@NotNull ASTNode identifier) {
        PsiElement psi = identifier.getPsi();
        for (PsiElement owner = psi.getParent(); owner != null && !(owner instanceof PsiFile); owner = owner.getParent()) {
            if (owner instanceof PsiNameIdentifierOwner named && named.getNameIdentifier() != null) {
                if (named.getNameIdentifier().getNode() == identifier) {
                    return true;
                }
                break;
            }
        }
        ASTNode parent = identifier.getTreeParent();
        if (parent != null && parent.getElementType() == MQL4Elements.VAR_DEFINITION) {
            return true;
        }
        IElementType prev = prevType(identifier);
        if (prev != null && DECLARING.contains(prev)) {
            return true;
        }
        if (prev == MQL4Elements.MUL || prev == MQL4Elements.AND) {
            ASTNode declarator = prevNode(identifier);
            IElementType beforeDeclarator = declarator == null ? null : prevType(declarator);
            IElementType next = nextType(identifier);
            return beforeDeclarator != null && DECLARING.contains(beforeDeclarator)
                    && (next == null || AFTER_DECLARED_NAME.contains(next));
        }
        return false;
    }

    @Nullable
    static IElementType prevType(@NotNull ASTNode node) {
        ASTNode prev = prevNode(node);
        return prev == null ? null : prev.getElementType();
    }

    @Nullable
    private static ASTNode prevNode(@NotNull ASTNode node) {
        PsiElement prev = PsiTreeUtil.prevVisibleLeaf(node.getPsi());
        while (prev != null && MQL4TokenSets.COMMENTS_OR_WS.contains(prev.getNode().getElementType())) {
            prev = PsiTreeUtil.prevVisibleLeaf(prev);
        }
        return prev == null ? null : prev.getNode();
    }

    @Nullable
    private static IElementType nextType(@NotNull ASTNode node) {
        PsiElement next = PsiTreeUtil.nextVisibleLeaf(node.getPsi());
        while (next != null && MQL4TokenSets.COMMENTS_OR_WS.contains(next.getNode().getElementType())) {
            next = PsiTreeUtil.nextVisibleLeaf(next);
        }
        return next == null ? null : next.getNode().getElementType();
    }
}
