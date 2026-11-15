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
            MQL4ClassElement inBody = PsiTreeUtil.getParentOfType(qualifier, MQL4ClassElement.class);
            return inBody != null ? inBody : MqlResolveUtil.enclosingClass(qualifier); // X::Method body
        }
        if (type == MQL4Elements.R_SQUARE_BRACKET) {
            // arr[i].m: an array's declared type is its element type
            PsiElement array = prevMeaningfulLeaf(matchingOpen(qualifier, MQL4Elements.L_SQUARE_BRACKET, MQL4Elements.R_SQUARE_BRACKET));
            MQL4ClassElement element = array == null ? null : resolveQualifierClass(array, chainDepth - 1);
            // row[i] on an object with operator[] (CRowComplex row) is a call, not an element access
            if (element != null && isIndexOperatorCall(array, element)) {
                // matrix[i].Set(...) on CMatrixInt: operator[] returns the row class
                String rowType = notPrimitive(indexOperatorReturnType(element, new java.util.HashSet<>()));
                return rowType == null ? null : MqlResolveUtil.findClassByName(rowType, qualifier.getProject(), qualifier);
            }
            return element;
        }
        if (type == MQL4Elements.R_ROUND_BRACKET) {
            // Get().m and obj.Get().m: the called function's return type
            PsiElement callee = prevMeaningfulLeaf(matchingOpen(qualifier, MQL4Elements.L_ROUND_BRACKET, MQL4Elements.R_ROUND_BRACKET));
            if (!isType(callee, MQL4Elements.IDENTIFIER)) {
                return null; // a cast or a parenthesized expression
            }
            for (com.intellij.psi.ResolveResult result : new MqlReference(callee).multiResolve(false)) {
                if (result.getElement() instanceof MQL4FunctionElement function) {
                    String returnType = notPrimitive(MqlPsiUtil.returnTypeName(function));
                    MQL4ClassElement c = returnType == null ? null : MqlResolveUtil.findClassByName(returnType, qualifier.getProject(), qualifier);
                    if (c != null) {
                        return c;
                    }
                }
            }
            return null;
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
                    MQL4ClassElement c = MqlResolveUtil.findClassByName(memberType, qualifier.getProject(), qualifier);
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
        return MqlResolveUtil.findClassByName(typeName, qualifier.getProject(), qualifier);
    }

    private static final java.util.regex.Pattern INDEX_OPERATOR = java.util.regex.Pattern.compile("\\boperator\\s*\\[\\s*\\]");

    /** {@code CRowInt *operator[](const int i)}: group 1 is the return type's name. */
    private static final java.util.regex.Pattern INDEX_OPERATOR_DECLARATION =
            java.util.regex.Pattern.compile("(\\w+)\\s*[*&]?\\s*\\boperator\\s*\\[\\s*\\]");

    /** The return type name of the {@code operator[]} {@code cls} declares or inherits, or null. */
    @Nullable
    private static String indexOperatorReturnType(@NotNull MQL4ClassElement cls, @NotNull java.util.Set<MQL4ClassElement> seen) {
        if (!seen.add(cls) || seen.size() > 16) {
            return null;
        }
        java.util.regex.Matcher m = INDEX_OPERATOR_DECLARATION.matcher(cls.getText());
        if (m.find()) {
            return m.group(1);
        }
        for (String base : MqlResolveUtil.baseClassNames(cls)) {
            MQL4ClassElement baseClass = MqlResolveUtil.findClassByName(base, cls.getProject(), cls);
            String type = baseClass == null ? null : indexOperatorReturnType(baseClass, seen);
            if (type != null) {
                return type;
            }
        }
        return null;
    }

    /**
     * True when {@code array[i]} calls {@code operator[]} of {@code type} rather than indexing an
     * array: the type has one and {@code array} isn't declared with {@code []}.
     */
    private static boolean isIndexOperatorCall(@NotNull PsiElement array, @NotNull MQL4ClassElement type) {
        if (!hasIndexOperator(type, new java.util.HashSet<>())) {
            return false;
        }
        if (array.getNode() == null || array.getNode().getElementType() != MQL4Elements.IDENTIFIER) {
            return true;
        }
        for (PsiElement declaration : MqlResolveUtil.resolve(array, array.getText())) {
            PsiElement owner = declaration instanceof MQL4FunctionArgElement || declaration instanceof MQL4VarDefinitionElement
                    ? declaration : declaration.getParent();
            if (owner != null && owner.getText().indexOf('[') >= 0) { // the definition, not its initializer
                return false; // CRow rows[]: rows[i] is an element
            }
        }
        return true;
    }

    /** True when {@code cls} or a class it derives from declares {@code operator[]}. */
    private static boolean hasIndexOperator(@NotNull MQL4ClassElement cls, @NotNull java.util.Set<MQL4ClassElement> seen) {
        if (!seen.add(cls) || seen.size() > 16) {
            return false;
        }
        if (INDEX_OPERATOR.matcher(cls.getText()).find()) {
            return true;
        }
        for (String base : MqlResolveUtil.baseClassNames(cls)) {
            MQL4ClassElement baseClass = MqlResolveUtil.findClassByName(base, cls.getProject(), cls);
            if (baseClass != null && hasIndexOperator(baseClass, seen)) {
                return true;
            }
        }
        return false;
    }

    /**
     * The declared type name of a member access's receiver, whether or not it is a project class:
     * a local, parameter or global ({@code dt} in {@code dt.hour}), an array element
     * ({@code rates[i].close}) or a field of a project class ({@code snap.when.hour}). Built-in
     * structures ({@code MqlDateTime}) have no PSI, so their members are checked by name.
     */
    @Nullable
    public static String resolveQualifierTypeName(@NotNull PsiElement qualifier) {
        IElementType type = qualifier.getNode() == null ? null : qualifier.getNode().getElementType();
        if (type == MQL4Elements.R_SQUARE_BRACKET) {
            PsiElement array = prevMeaningfulLeaf(matchingOpen(qualifier, MQL4Elements.L_SQUARE_BRACKET, MQL4Elements.R_SQUARE_BRACKET));
            if (array == null) {
                return null;
            }
            MQL4ClassElement element = resolveQualifierClass(array, MAX_CHAIN_DEPTH - 1);
            return element != null && isIndexOperatorCall(array, element)
                    ? indexOperatorReturnType(element, new java.util.HashSet<>()) : resolveQualifierTypeName(array);
        }
        if (type != MQL4Elements.IDENTIFIER) {
            return null;
        }
        PsiElement beforeQ = prevMeaningfulLeaf(qualifier);
        if (isType(beforeQ, MQL4Elements.DOT)) {
            PsiElement innerQualifier = prevMeaningfulLeaf(beforeQ);
            MQL4ClassElement innerClass = innerQualifier == null ? null : resolveQualifierClass(innerQualifier, MAX_CHAIN_DEPTH - 1);
            if (innerClass == null) {
                return null;
            }
            for (PsiElement member : MqlResolveUtil.resolveMemberInClassHierarchy(innerClass, qualifier.getText())) {
                String memberType = declaredTypeNameOf(member);
                if (memberType != null) {
                    return memberType;
                }
            }
            return null;
        }
        return declaredTypeNameOfQualifier(qualifier);
    }

    /**
     * Declared-type name of a plain qualifier identifier. The scoped lexical {@code Type name} scan
     * runs FIRST because it finds the NEAREST in-scope declaration — so a custom-typed local
     * ({@code CFoo v;}) correctly shadows an outer parameter of the same name ({@code void f(CBar &v)}).
     * The resolver-based path (which sees parameters -> {@link MQL4FunctionArgElement} and primitive
     * var-declarations, but not the bare-two-identifier custom local) is the fallback for when there
     * is no nearer lexical declaration.
     */
    @Nullable
    private static String declaredTypeNameOfQualifier(@NotNull PsiElement qualifier) {
        String name = qualifier.getText();
        String scanned = scanDeclaredTypeName(qualifier, name);
        if (scanned != null) {
            return scanned;
        }
        for (PsiElement target : MqlResolveUtil.resolve(qualifier, name)) {
            String typeName = declaredTypeNameOf(target);
            if (typeName != null) {
                return typeName;
            }
        }
        return null;
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
        if (typeName == null || typeName.isEmpty() || PRIMITIVE_TYPES.contains(typeName)
                || com.limemojito.oss.mql.MqlBuiltinTypes.MQL5_TYPES.contains(typeName)) {
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
            // The type token must be the FIRST meaningful token of the statement (after any &/*
            // modifiers). This anchors the match to a real `Type name` declaration and rejects a
            // mid-expression pair like `total = Count * n;` mistyping `n` as class `Count`.
            if (j != 0 || meaningful.get(j).getElementType() != MQL4Elements.IDENTIFIER) {
                continue;
            }
            return notPrimitive(meaningful.get(j).getText());
        }
        return null;
    }

    /** Bounds the backward scan for a matching bracket. */
    private static final int MAX_BRACKET_SCAN = 256;

    /** The bracket that opens {@code close}, scanning leaves backwards, or null. */
    @Nullable
    private static PsiElement matchingOpen(@NotNull PsiElement close, @NotNull IElementType open, @NotNull IElementType closeType) {
        int depth = 0;
        PsiElement e = close;
        for (int i = 0; e != null && i < MAX_BRACKET_SCAN; i++, e = prevMeaningfulLeaf(e)) {
            IElementType t = e.getNode().getElementType();
            if (t == closeType) {
                depth++;
            } else if (t == open && --depth == 0) {
                return e;
            }
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
