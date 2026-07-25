/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiWhiteSpace;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Phase 5 keystone: member-access resolution (REVAMP_PLAN.md). Given the member IDENTIFIER of a
 * {@code receiver.member} access, works out the receiver's class type (a project class only --
 * declared-type + bounded inheritance/chain walk, NOT full expression type inference) and resolves
 * the member (field or method) inside it. Anything unresolved yields an empty list so
 * {@link MqlReference} falls back to today's no-target behavior (no regression on free identifiers,
 * no wrong jumps).
 *
 * <p>Receiver typing covers the three shapes the tolerant MQL parser actually produces:</p>
 * <ol>
 *     <li>a by-ref/pointer/value parameter {@code CFoo &v} -- {@code v} resolves to a
 *     {@link MQL4FunctionArgElement} whose declared type is a project class;</li>
 *     <li>a local {@code CFoo v;} -- the parser leaves this as a bare two-identifier
 *     EXPRESSION_STATEMENT (custom types don't hit the primitive-only var-declaration gate), so the
 *     type is found by a scoped lexical {@code Type name} scan;</li>
 *     <li>{@code this.member} inside a method -- the enclosing {@link MQL4ClassElement} directly.</li>
 * </ol>
 * Simple {@code a.b.c} chains are supported by re-typing each hop (bounded depth); they only
 * resolve as far as intermediate members have a discoverable declared type.
 */
public final class MqlTypeResolver {

    private MqlTypeResolver() {
    }

    /** Bounds {@code a.b.c.d} chain re-typing so a pathological chain can't recurse unbounded. */
    public static final int MAX_CHAIN_DEPTH = 4;

    /** Built-in primitive type spellings -- these are never a project class, so never a receiver type. */
    private static final Set<String> PRIMITIVE_TYPES = Set.of(
            "void", "bool", "char", "uchar", "short", "ushort", "int", "uint",
            "long", "ulong", "float", "double", "string", "color", "datetime",
            "class", "struct", "interface", "enum");

    /**
     * Resolve {@code receiver.member}: {@code memberLeaf} is the member IDENTIFIER, whose previous
     * meaningful leaf must be a {@code DOT}. Returns the member declaration(s), or an empty list if
     * the receiver's type doesn't resolve to a project class or the member isn't found in it.
     */
    @NotNull
    public static List<PsiElement> resolveMember(@NotNull PsiElement memberLeaf) {
        PsiElement dot = prevMeaningfulLeaf(memberLeaf);
        if (!isType(dot, MQL4Elements.DOT)) {
            return Collections.emptyList();
        }
        PsiElement qualifier = prevMeaningfulLeaf(dot);
        if (qualifier == null) {
            return Collections.emptyList();
        }
        MQL4ClassElement receiverClass = resolveQualifierClass(qualifier, MAX_CHAIN_DEPTH);
        if (receiverClass == null) {
            return Collections.emptyList();
        }
        return MqlResolveUtil.resolveMemberInClassHierarchy(receiverClass, memberLeaf.getText());
    }

    /** Convenience overload with the default chain-depth bound (used by dot-completion). */
    @Nullable
    public static MQL4ClassElement resolveQualifierClass(@NotNull PsiElement qualifier) {
        return resolveQualifierClass(qualifier, MAX_CHAIN_DEPTH);
    }

    /**
     * The class type of a receiver qualifier leaf: {@code this}, a chained member ({@code a.b} when
     * resolving {@code .c}), or a free local/parameter identifier whose declared type is a project
     * class. {@code null} when it isn't a resolvable project-class-typed receiver.
     */
    @Nullable
    public static MQL4ClassElement resolveQualifierClass(@NotNull PsiElement qualifier, int chainDepth) {
        if (chainDepth <= 0 || qualifier.getNode() == null) {
            return null;
        }
        IElementType type = qualifier.getNode().getElementType();
        if (type == MQL4Elements.THIS_KEYWORD) {
            return PsiTreeUtil.getParentOfType(qualifier, MQL4ClassElement.class);
        }
        if (type != MQL4Elements.IDENTIFIER) {
            return null;
        }
        // Chained receiver: the qualifier is itself the member side of an inner `x.qualifier` access.
        PsiElement beforeQ = prevMeaningfulLeaf(qualifier);
        if (isType(beforeQ, MQL4Elements.DOT)) {
            PsiElement innerQualifier = prevMeaningfulLeaf(beforeQ);
            if (innerQualifier == null) {
                return null;
            }
            MQL4ClassElement innerClass = resolveQualifierClass(innerQualifier, chainDepth - 1);
            if (innerClass == null) {
                return null;
            }
            for (PsiElement member : MqlResolveUtil.resolveMemberInClassHierarchy(innerClass, qualifier.getText())) {
                String memberType = declaredTypeNameOf(member);
                if (memberType != null) {
                    MQL4ClassElement c = MqlResolveUtil.findClassByName(memberType, qualifier.getProject());
                    if (c != null) {
                        return c;
                    }
                }
            }
            return null;
        }
        // Free receiver: a plain local/parameter identifier.
        String typeName = declaredTypeNameOfQualifier(qualifier);
        if (typeName == null) {
            return null;
        }
        return MqlResolveUtil.findClassByName(typeName, qualifier.getProject());
    }

    /**
     * Declared-type name of a plain qualifier identifier: first via the normal resolver (catches a
     * parameter -> {@link MQL4FunctionArgElement}, or a primitive-typed variable), then falling back
     * to a scoped lexical {@code Type name} scan for the common custom-typed local
     * ({@code CFoo v;}) that the parser doesn't wrap in a declaration node.
     */
    @Nullable
    private static String declaredTypeNameOfQualifier(@NotNull PsiElement qualifier) {
        String name = qualifier.getText();
        for (PsiElement target : MqlResolveUtil.resolve(qualifier, name)) {
            String typeName = declaredTypeNameOf(target);
            if (typeName != null) {
                return typeName;
            }
        }
        return scanDeclaredTypeName(qualifier, name);
    }

    @Nullable
    private static String declaredTypeNameOf(@NotNull PsiElement declaration) {
        if (declaration instanceof MQL4FunctionArgElement arg) {
            return notPrimitive(arg.getDeclaredTypeName());
        }
        if (declaration instanceof MQL4VarDefinitionElement var) {
            return notPrimitive(var.getDeclaredTypeName());
        }
        return null;
    }

    @Nullable
    private static String notPrimitive(@Nullable String typeName) {
        if (typeName == null || typeName.isEmpty() || PRIMITIVE_TYPES.contains(typeName)) {
            return null;
        }
        return typeName;
    }

    /**
     * Scoped lexical scan for a {@code Type name} declaration of {@code name}, walking outward
     * through the enclosing code blocks / function exactly like the local resolver's scope walk.
     * Matches the parser's bare-two-identifier shape for a custom-typed declaration and returns the
     * leading type identifier's text (never a primitive keyword, which the parser wraps instead).
     */
    @Nullable
    private static String scanDeclaredTypeName(@NotNull PsiElement usage, @NotNull String name) {
        PsiElement parent = usage.getParent();
        while (parent != null) {
            ASTNode node = parent.getNode();
            if (node != null && MqlPsiUtil.isCodeBlock(parent)) {
                String typeName = scanBlockForDeclaration(node, name);
                if (typeName != null) {
                    return typeName;
                }
            }
            parent = parent.getParent();
        }
        return null;
    }

    @Nullable
    private static String scanBlockForDeclaration(@NotNull ASTNode block, @NotNull String name) {
        for (ASTNode statement = block.getFirstChildNode(); statement != null; statement = statement.getTreeNext()) {
            IElementType t = statement.getElementType();
            if (t == MQL4Elements.EXPRESSION_STATEMENT || t == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                String typeName = scanStatementForDeclaration(statement, name);
                if (typeName != null) {
                    return typeName;
                }
            }
        }
        return null;
    }

    /**
     * Looks inside one statement for {@code Type [&|*] name}: an IDENTIFIER equal to {@code name}
     * immediately preceded (skipping a single {@code &}/{@code *}) by an IDENTIFIER type that is not
     * itself the member side of a {@code .} access. Returns the type text, or {@code null}.
     */
    @Nullable
    private static String scanStatementForDeclaration(@NotNull ASTNode statement, @NotNull String name) {
        List<ASTNode> meaningful = new ArrayList<>();
        for (ASTNode child = statement.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (!MQL4TokenSets.COMMENTS_OR_WS.contains(child.getElementType())) {
                meaningful.add(child);
            }
        }
        for (int i = 1; i < meaningful.size(); i++) {
            ASTNode cur = meaningful.get(i);
            if (cur.getElementType() != MQL4Elements.IDENTIFIER || !name.equals(cur.getText())) {
                continue;
            }
            int j = i - 1;
            while (j >= 0 && (meaningful.get(j).getElementType() == MQL4Elements.AND
                    || meaningful.get(j).getElementType() == MQL4Elements.MUL)) {
                j--;
            }
            if (j < 0 || meaningful.get(j).getElementType() != MQL4Elements.IDENTIFIER) {
                continue;
            }
            // Reject `a.name` (member access) being mistaken for a `Type name` declaration.
            if (j >= 1 && meaningful.get(j - 1).getElementType() == MQL4Elements.DOT) {
                continue;
            }
            return notPrimitive(meaningful.get(j).getText());
        }
        return null;
    }

    private static boolean isType(@Nullable PsiElement element, @NotNull IElementType type) {
        return element != null && element.getNode() != null && element.getNode().getElementType() == type;
    }

    /** Previous leaf, skipping whitespace (mirrors the completion providers' own helper). */
    @Nullable
    public static PsiElement prevMeaningfulLeaf(@Nullable PsiElement element) {
        PsiElement e = element == null ? null : PsiTreeUtil.prevLeaf(element);
        while (e instanceof PsiWhiteSpace) {
            e = PsiTreeUtil.prevLeaf(e);
        }
        return e;
    }
}
