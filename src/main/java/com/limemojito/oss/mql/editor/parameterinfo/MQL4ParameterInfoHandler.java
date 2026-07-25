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
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.doc.BuiltinSignature;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;

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
            params = MqlCallSignatures.splitTopLevelParams(function.getSignature());
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
        return MqlCallSignatures.isCallArgsBlock(element);
    }

    /** Project function declarations/definitions with this name, else the built-in signature, else {@code null}. */
    @Nullable
    private Object[] itemsFor(@NotNull PsiElement callArgs, @NotNull Project project) {
        String name = MqlCallSignatures.callName(callArgs);
        return name == null ? null : MqlCallSignatures.resolveItems(name, project);
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
}
