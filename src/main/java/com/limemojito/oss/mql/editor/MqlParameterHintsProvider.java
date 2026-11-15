/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.codeInsight.hints.declarative.HintFormat;
import com.intellij.codeInsight.hints.declarative.InlayHintsCollector;
import com.intellij.codeInsight.hints.declarative.InlayHintsProvider;
import com.intellij.codeInsight.hints.declarative.InlayTreeSink;
import com.intellij.codeInsight.hints.declarative.InlineInlayPosition;
import com.intellij.codeInsight.hints.declarative.SharedBypassCollector;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.editor.parameterinfo.MqlCallSignatures;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import kotlin.Unit;

/**
 * Parameter-name inlay hints (Phase 3a): renders {@code OrderSend(sym, /*cmd:*&#47; OP_BUY, ...)}
 * by labelling each positional argument of a resolved call with its parameter name.
 *
 * <p>The callee signature is resolved through {@link MqlCallSignatures} -- the very same project
 * PSI + built-in {@link com.limemojito.oss.mql.doc.BuiltinSignatureCatalog} lookup that drives the
 * Ctrl-P parameter-info popup -- so a call gets hints exactly when it resolves to a known
 * signature. Unresolved calls (unknown names, member calls we cannot type-resolve) get none.</p>
 *
 * <p>Built on the declarative inlay API ({@code codeInsight.declarativeInlayProvider}): the older
 * {@code InlayParameterHintsProvider} lives in the {@code @ApiStatus.Experimental}
 * {@code com.intellij.codeInsight.hints} package. Toggle it under Settings | Editor | Inlay Hints |
 * Parameter names | MQL.</p>
 */
public class MqlParameterHintsProvider implements InlayHintsProvider {

    /** Variadic logging/UI calls have no fixed positional parameter names worth labelling. */
    private static final Set<String> NEVER_HINTED = Set.of("Print", "PrintFormat", "Alert", "Comment");

    /** A parameter-name label shown before the argument that starts at {@code offset}. */
    public record Hint(@NotNull String name, int offset) {
    }

    @NotNull
    @Override
    public InlayHintsCollector createCollector(@NotNull PsiFile file, @NotNull Editor editor) {
        return (SharedBypassCollector) (element, sink) -> addHints(element, sink);
    }

    /** Adds one {@code name:} inlay per {@link #computeHints hint} of {@code element}. */
    public static void addHints(@NotNull PsiElement element, @NotNull InlayTreeSink sink) {
        for (Hint hint : computeHints(element)) {
            sink.addPresentation(new InlineInlayPosition(hint.offset(), false, 0), null, null,
                    HintFormat.Companion.getDefault(), builder -> {
                        builder.text(hint.name() + ":", null);
                        return Unit.INSTANCE;
                    });
        }
    }

    /** The parameter-name hints of a call's {@code (...)} block; empty for any other element. */
    @NotNull
    public static List<Hint> computeHints(@NotNull PsiElement element) {
        if (!MqlCallSignatures.isCallArgsBlock(element)) {
            return List.of();
        }
        String name = MqlCallSignatures.callName(element);
        if (name == null || NEVER_HINTED.contains(name)) {
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

        List<Hint> hints = new ArrayList<>();
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
            // Don't restate what the code already says. The argument text can only equal a bare
            // parameter name when the slot is a single IDENTIFIER leaf matching it (a param name is
            // one identifier token; any multi-token slot carries an operator/space/bracket and so can
            // never equal it) -- so check that directly instead of rebuilding the slot's text.
            if (arg.nonTriviaCount() == 1
                    && arg.first() != null
                    && arg.first().getElementType() == MQL4Elements.IDENTIFIER
                    && paramName.equals(arg.first().getText())) {
                continue;
            }
            hints.add(new Hint(paramName, arg.startOffset));
        }
        return hints;
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
        ASTNode first = null;   // first non-trivia node in the current slot
        int count = 0;          // number of non-trivia nodes in the current slot
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
                args.add(new Argument(start, first, count));
                return args;
            }
            if (t == MQL4Elements.COMMA) {
                args.add(new Argument(start, first, count));
                start = -1;
                first = null;
                count = 0;
                continue;
            }
            if (MQL4TokenSets.COMMENTS_OR_WS.contains(t)) {
                continue;
            }
            if (start < 0) {
                start = child.getStartOffset();
            }
            if (first == null) {
                first = child;
            }
            count++;
        }
        // No closing paren (tolerant/broken AST): flush whatever we accumulated.
        if (started) {
            args.add(new Argument(start, first, count));
        }
        return args;
    }

    private record Argument(int startOffset, @Nullable ASTNode first, int nonTriviaCount) {
    }
}
