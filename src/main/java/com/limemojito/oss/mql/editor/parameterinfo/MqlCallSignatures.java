/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.parameterinfo;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.search.GlobalSearchScope;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.doc.BuiltinSignature;
import com.limemojito.oss.mql.doc.BuiltinSignatureCatalog;
import com.limemojito.oss.mql.index.MQL4FunctionNameIndex;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Shared call-signature resolution factored out of {@link MQL4ParameterInfoHandler} so the
 * parameter-info popup (Ctrl-P) and the parameter-name inlay hints
 * ({@link com.limemojito.oss.mql.editor.MqlParameterHintsProvider}) resolve a call's target
 * signature and parameter names exactly the same way, from a single place.
 *
 * <p>A call site's argument list, per the tolerant flat statement AST, is a {@code BRACKETS_BLOCK}
 * whose first child is {@code (} and whose previous non-trivial sibling is the callee
 * {@code IDENTIFIER}. Resolution prefers project function declarations/definitions of that name
 * (via {@link MQL4FunctionNameIndex}) and falls back to the bundled built-in
 * {@link BuiltinSignatureCatalog}.</p>
 */
public final class MqlCallSignatures {

    /** Any identifier token (last one in a param declaration is its name). */
    private static final Pattern IDENTIFIER = Pattern.compile("[A-Za-z_][A-Za-z0-9_]*");

    private MqlCallSignatures() {
    }

    /**
     * {@code true} when {@code element} is the {@code (...)} argument block of a call:
     * a {@code BRACKETS_BLOCK} opening with {@code (} whose previous non-trivial sibling is an
     * identifier (the callee name).
     */
    public static boolean isCallArgsBlock(@NotNull PsiElement element) {
        ASTNode node = element.getNode();
        if (node == null || node.getElementType() != MQL4Elements.BRACKETS_BLOCK) {
            return false;
        }
        ASTNode first = node.getFirstChildNode();
        if (first == null || first.getElementType() != MQL4Elements.L_ROUND_BRACKET) {
            return false;
        }
        PsiElement prev = prevNonTrivialSibling(element);
        return prev != null && prev.getNode() != null && prev.getNode().getElementType() == MQL4Elements.IDENTIFIER;
    }

    @Nullable
    public static PsiElement prevNonTrivialSibling(@NotNull PsiElement element) {
        PsiElement prev = element.getPrevSibling();
        while (prev != null && prev.getNode() != null && MQL4TokenSets.COMMENTS_OR_WS.contains(prev.getNode().getElementType())) {
            prev = prev.getPrevSibling();
        }
        return prev;
    }

    /** The callee name of a call args block, or {@code null}. */
    @Nullable
    public static String callName(@NotNull PsiElement callArgs) {
        PsiElement nameElement = prevNonTrivialSibling(callArgs);
        return nameElement == null ? null : nameElement.getText();
    }

    /**
     * Signature items for a callee name: matching project function
     * declarations/definitions, else a single built-in signature, else {@code null}. Mirrors the
     * ordering the parameter-info popup relies on (project functions win over built-ins).
     */
    @Nullable
    public static Object[] resolveItems(@NotNull String name, @NotNull Project project) {
        var projectFunctions = MQL4FunctionNameIndex.getInstance().get(name, project, GlobalSearchScope.allScope(project));
        List<MQL4FunctionElement> matching = new ArrayList<>();
        for (MQL4FunctionElement f : projectFunctions) {
            if (name.equals(f.getFunctionName())) {
                matching.add(f);
            }
        }
        if (!matching.isEmpty()) {
            return matching.toArray();
        }
        BuiltinSignature builtin = BuiltinSignatureCatalog.get(name);
        return builtin == null ? null : new Object[]{builtin};
    }

    /** Raw parameter declaration strings for a resolved item (function element or built-in signature). */
    @NotNull
    public static List<String> rawParams(@Nullable Object item) {
        if (item instanceof MQL4FunctionElement function) {
            return splitTopLevelParams(function.getSignature());
        }
        if (item instanceof BuiltinSignature sig) {
            return sig.params == null ? List.of() : sig.params;
        }
        return List.of();
    }

    /** Splits a raw FUNCTION_ARGS_LIST text ("int a, string b=NULL") on top-level commas only. */
    @NotNull
    public static List<String> splitTopLevelParams(@NotNull String argsText) {
        List<String> parts = new ArrayList<>();
        String trimmed = argsText.trim();
        if (trimmed.isEmpty()) {
            return parts;
        }
        int depth = 0;
        int start = 0;
        for (int i = 0; i < trimmed.length(); i++) {
            char c = trimmed.charAt(i);
            if (c == '(' || c == '[') {
                depth++;
            } else if (c == ')' || c == ']') {
                depth--;
            } else if (c == ',' && depth == 0) {
                parts.add(trimmed.substring(start, i).trim());
                start = i + 1;
            }
        }
        String last = trimmed.substring(start).trim();
        if (!last.isEmpty()) {
            parts.add(last);
        }
        return parts;
    }

    /**
     * The bare parameter name from a raw declaration: strips any default value, array brackets and
     * type/qualifier tokens, keeping the last identifier. {@code "string comment=NULL"} -&gt;
     * {@code "comment"}, {@code "const double &price[]"} -&gt; {@code "price"}. Returns {@code null}
     * for a nameless/variadic entry (e.g. {@code "..."} or {@code "void"} only).
     */
    @Nullable
    public static String parameterName(@Nullable String rawParamDecl) {
        if (rawParamDecl == null) {
            return null;
        }
        String p = rawParamDecl.trim();
        int eq = p.indexOf('=');
        if (eq >= 0) {
            p = p.substring(0, eq);
        }
        // drop array dimensions so "array[]" -> "array"
        p = p.replaceAll("\\[[^\\]]*\\]", " ");
        String last = null;
        Matcher m = IDENTIFIER.matcher(p);
        while (m.find()) {
            last = m.group();
        }
        // a bare type keyword with no name (e.g. "void") is not a usable parameter name
        if (last == null || "void".equals(last)) {
            return null;
        }
        return last;
    }
}
