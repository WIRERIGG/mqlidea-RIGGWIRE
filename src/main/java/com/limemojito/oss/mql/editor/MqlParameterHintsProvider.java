/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.hints.HintInfo;
import com.intellij.codeInsight.hints.InlayInfo;
import com.intellij.codeInsight.hints.InlayParameterHintsProvider;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Language;
import com.limemojito.oss.mql.editor.parameterinfo.MqlCallSignatures;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

/**
 * Parameter-name inlay hints (Phase 3a): renders {@code OrderSend(sym, /*cmd:*&#47; OP_BUY, ...)}
 * by labelling each positional argument of a resolved call with its parameter name.
 *
 * <p>The callee signature is resolved through {@link MqlCallSignatures} -- the very same project
 * PSI + built-in {@link com.limemojito.oss.mql.doc.BuiltinSignatureCatalog} lookup that drives the
 * Ctrl-P parameter-info popup -- so a call gets hints exactly when it resolves to a known
 * signature. Unresolved calls (unknown names, member calls we cannot type-resolve) get none.</p>
 */
public class MqlParameterHintsProvider implements InlayParameterHintsProvider {

    @NotNull
    @Override
    public List<InlayInfo> getParameterHints(@NotNull PsiElement element) {
        if (!MqlCallSignatures.isCallArgsBlock(element)) {
            return List.of();
        }
        String name = MqlCallSignatures.callName(element);
        if (name == null) {
            return List.of();
        }
        Object[] items = MqlCallSignatures.resolveItems(name, element.getProject());
        if (items == null || items.length == 0) {
            return List.of();
        }
        List<String> rawParams = MqlCallSignatures.rawParams(items[0]);
        if (rawParams.isEmpty()) {
            return List.of();
        }
        // Optional: skip trivial single-parameter calls -- the name adds little there.
        if (rawParams.size() == 1) {
            return List.of();
        }

        List<Argument> args = topLevelArguments(element);
        if (args.isEmpty()) {
            return List.of();
        }

        List<InlayInfo> hints = new ArrayList<>();
        int count = Math.min(args.size(), rawParams.size());
        for (int i = 0; i < count; i++) {
            ProgressManager.checkCanceled();
            Argument arg = args.get(i);
            if (arg.startOffset < 0) {
                continue; // empty positional slot (e.g. a trailing comma)
            }
            String paramName = MqlCallSignatures.parameterName(rawParams.get(i));
            if (paramName == null || paramName.isEmpty()) {
                continue;
            }
            // Don't restate what the code already says.
            if (paramName.equals(arg.text)) {
                continue;
            }
            hints.add(new InlayInfo(paramName, arg.startOffset));
        }
        return hints;
    }

    @Nullable
    @Override
    public HintInfo getHintInfo(@NotNull PsiElement element) {
        if (!MqlCallSignatures.isCallArgsBlock(element)) {
            return null;
        }
        String name = MqlCallSignatures.callName(element);
        if (name == null) {
            return null;
        }
        Object[] items = MqlCallSignatures.resolveItems(name, element.getProject());
        if (items == null || items.length == 0) {
            return null;
        }
        List<String> paramNames = new ArrayList<>();
        for (String raw : MqlCallSignatures.rawParams(items[0])) {
            String pn = MqlCallSignatures.parameterName(raw);
            paramNames.add(pn == null ? "" : pn);
        }
        return new HintInfo.MethodInfo(name, paramNames, MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public Set<String> getDefaultBlackList() {
        // Variadic logging/UI calls have no fixed positional parameter names worth labelling.
        return Set.of("Print", "PrintFormat", "Alert", "Comment");
    }

    // ---- argument extraction -----------------------------------------------------------------

    /**
     * The top-level positional arguments of a {@code (...)} block, one entry per comma-separated
     * slot (an empty slot yields {@code startOffset == -1}). Commas nested inside a child bracket
     * block belong to a nested call and are not counted, because only direct-child {@code COMMA}
     * nodes of this block separate its own arguments.
     */
    @NotNull
    private static List<Argument> topLevelArguments(@NotNull PsiElement block) {
        List<Argument> args = new ArrayList<>();
        ASTNode node = block.getNode();
        boolean started = false;
        int start = -1;
        StringBuilder text = new StringBuilder();
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (!started) {
                if (t == MQL4Elements.L_ROUND_BRACKET) {
                    started = true;
                }
                continue;
            }
            if (t == MQL4Elements.R_ROUND_BRACKET) {
                args.add(new Argument(start, text.toString().trim()));
                start = -1;
                text.setLength(0);
                return args;
            }
            if (t == MQL4Elements.COMMA) {
                args.add(new Argument(start, text.toString().trim()));
                start = -1;
                text.setLength(0);
                continue;
            }
            if (MQL4TokenSets.COMMENTS_OR_WS.contains(t)) {
                if (start >= 0) {
                    text.append(child.getText());
                }
                continue;
            }
            if (start < 0) {
                start = child.getStartOffset();
            }
            text.append(child.getText());
        }
        // No closing paren (tolerant/broken AST): flush whatever we accumulated.
        if (started) {
            args.add(new Argument(start, text.toString().trim()));
        }
        return args;
    }

    private record Argument(int startOffset, @NotNull String text) {
    }
}
