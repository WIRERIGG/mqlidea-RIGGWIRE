/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.parameterinfo;

import com.intellij.lang.ASTNode;
import com.intellij.lang.parameterInfo.CreateParameterInfoContext;
import com.intellij.lang.parameterInfo.ParameterInfoContext;
import com.intellij.lang.parameterInfo.ParameterInfoHandler;
import com.intellij.lang.parameterInfo.ParameterInfoUIContext;
import com.intellij.lang.parameterInfo.UpdateParameterInfoContext;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
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

/**
 * Signature-help popup ("Ctrl-P") for a call's argument list (REVAMP_PLAN.md Phase 6, deliverable
 * 4): {@code Foo(bar, |)} shows {@code Foo}'s full signature with the current parameter
 * highlighted, from the project PSI ({@link MQL4FunctionElement#getSignature()}) for user
 * functions, or from {@link BuiltinSignatureCatalog} for built-ins.
 *
 * <p>The call site's argument list is, per the tolerant flat statement AST, just a
 * {@code BRACKETS_BLOCK} whose first child is {@code (} and whose previous sibling is the
 * function-name {@code IDENTIFIER} -- exactly the shape {@link com.limemojito.oss.mql.doc.MQL4DocumentationProvider}
 * already relies on to show docs when the caret sits on the opening paren.</p>
 */
public class MQL4ParameterInfoHandler implements ParameterInfoHandler<PsiElement, Object> {

    @Nullable
    @Override
    public PsiElement findElementForParameterInfo(@NotNull CreateParameterInfoContext context) {
        PsiElement callArgs = findEnclosingCallArgs(context);
        if (callArgs == null) {
            return null;
        }
        Object[] items = itemsFor(callArgs, context.getProject());
        if (items == null || items.length == 0) {
            return null;
        }
        context.setItemsToShow(items);
        return callArgs;
    }

    @Override
    public void showParameterInfo(@NotNull PsiElement element, @NotNull CreateParameterInfoContext context) {
        context.showHint(element, element.getTextRange().getStartOffset(), this);
    }

    @Nullable
    @Override
    public PsiElement findElementForUpdatingParameterInfo(@NotNull UpdateParameterInfoContext context) {
        return findEnclosingCallArgs(context);
    }

    @Override
    public void updateParameterInfo(@NotNull PsiElement callArgs, @NotNull UpdateParameterInfoContext context) {
        if (!isCallArgsBlock(callArgs)) {
            context.removeHint();
            return;
        }
        context.setCurrentParameter(currentParameterIndex(callArgs, context.getOffset()));
    }

    @Override
    public void updateUI(Object item, @NotNull ParameterInfoUIContext context) {
        List<String> params;
        String returnType = null;
        if (item instanceof MQL4FunctionElement function) {
            params = splitTopLevelParams(function.getSignature());
        } else if (item instanceof BuiltinSignature sig) {
            params = sig.params == null ? List.of() : sig.params;
            returnType = sig.returnType;
        } else {
            return;
        }

        String prefix = (returnType == null || returnType.isEmpty()) ? "" : returnType + " ";
        if (params.isEmpty()) {
            context.setupUIComponentPresentation(prefix.isEmpty() ? "<no parameters>" : prefix + "()",
                    0, 0, false, false, false, context.getDefaultParameterColor());
            return;
        }

        StringBuilder text = new StringBuilder(prefix);
        int highlightStart = -1;
        int highlightEnd = -1;
        int current = context.getCurrentParameterIndex();
        for (int i = 0; i < params.size(); i++) {
            if (i > 0) {
                text.append(", ");
            }
            if (i == current) {
                highlightStart = text.length();
            }
            text.append(params.get(i));
            if (i == current) {
                highlightEnd = text.length();
            }
        }
        if (highlightStart < 0) {
            highlightStart = 0;
            highlightEnd = 0;
        }
        context.setupUIComponentPresentation(text.toString(), highlightStart, highlightEnd, false, false, false, context.getDefaultParameterColor());
    }

    // ---- shared lookup -----------------------------------------------------------------------

    @Nullable
    private PsiElement findEnclosingCallArgs(@NotNull ParameterInfoContext context) {
        PsiFile file = context.getFile();
        int offset = context.getOffset();
        PsiElement at = file.findElementAt(offset);
        if (at == null && offset > 0) {
            at = file.findElementAt(offset - 1);
        }
        PsiElement candidate = at;
        while (candidate != null) {
            if (isCallArgsBlock(candidate)) {
                return candidate;
            }
            candidate = candidate.getParent();
        }
        return null;
    }

    private boolean isCallArgsBlock(@NotNull PsiElement element) {
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
    private static PsiElement prevNonTrivialSibling(@NotNull PsiElement element) {
        PsiElement prev = element.getPrevSibling();
        while (prev != null && prev.getNode() != null && MQL4TokenSets.COMMENTS_OR_WS.contains(prev.getNode().getElementType())) {
            prev = prev.getPrevSibling();
        }
        return prev;
    }

    /** Project function declarations/definitions with this name, else the built-in signature, else {@code null}. */
    @Nullable
    private Object[] itemsFor(@NotNull PsiElement callArgs, @NotNull Project project) {
        PsiElement nameElement = prevNonTrivialSibling(callArgs);
        if (nameElement == null) {
            return null;
        }
        String name = nameElement.getText();
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

    private int currentParameterIndex(@NotNull PsiElement callArgs, int offset) {
        int index = 0;
        for (ASTNode child = callArgs.getNode().getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (child.getStartOffset() >= offset) {
                break;
            }
            if (child.getElementType() == MQL4Elements.COMMA) {
                index++;
            }
        }
        return index;
    }

    /** Splits a raw FUNCTION_ARGS_LIST text ("int a, string b=NULL") on top-level commas only. */
    @NotNull
    private static List<String> splitTopLevelParams(@NotNull String argsText) {
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
}
