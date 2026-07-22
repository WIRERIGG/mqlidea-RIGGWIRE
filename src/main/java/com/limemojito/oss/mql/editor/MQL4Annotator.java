/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.lang.ASTNode;
import com.intellij.lang.annotation.AnnotationHolder;
import com.intellij.lang.annotation.Annotator;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.psi.PsiElement;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.Set;

public class MQL4Annotator implements Annotator {

    private static final Set<String> MQL5_EVENT_HANDLERS = Set.of(
            "OnInit", "OnDeinit", "OnTick", "OnTimer", "OnTrade",
            "OnTradeTransaction", "OnBookEvent", "OnChartEvent",
            "OnCalculate", "OnTester", "OnTesterInit", "OnTesterDeinit",
            "OnTesterPass", "OnStart"
    );

    public static final TextAttributesKey EVENT_HANDLER_NAME = TextAttributesKey.createTextAttributesKey(
            "MQL5_EVENT_HANDLER", DefaultLanguageHighlighterColors.FUNCTION_DECLARATION);

    public static final TextAttributesKey INPUT_PARAMETER = TextAttributesKey.createTextAttributesKey(
            "MQL5_INPUT_PARAMETER", DefaultLanguageHighlighterColors.INSTANCE_FIELD);

    @Override
    public void annotate(@NotNull PsiElement element, @NotNull AnnotationHolder holder) {
        if (element instanceof MQL4FunctionElement func) {
            annotateEventHandler(func, holder);
        } else if (element.getNode().getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
            annotateInputParameter(element, holder);
        }
    }

    private void annotateEventHandler(@NotNull MQL4FunctionElement func, @NotNull AnnotationHolder holder) {
        String name = func.getFunctionName();
        if (name == null || !MQL5_EVENT_HANDLERS.contains(name)) return;

        ASTNode nameNode = func.getNode().findChildByType(MQL4Elements.IDENTIFIER);
        if (nameNode == null) return;

        holder.newSilentAnnotation(HighlightSeverity.INFORMATION)
                .range(nameNode)
                .textAttributes(EVENT_HANDLER_NAME)
                .create();
    }

    private void annotateInputParameter(@NotNull PsiElement varDecl, @NotNull AnnotationHolder holder) {
        ASTNode node = varDecl.getNode();
        ASTNode child = node.getFirstChildNode();
        boolean isInput = false;
        while (child != null) {
            if (child.getElementType() == MQL4Elements.INPUT_KEYWORD
                    || child.getElementType() == MQL4Elements.SINPUT_KEYWORD) {
                isInput = true;
                break;
            }
            child = child.getTreeNext();
        }
        if (!isInput) return;

        ASTNode defList = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (defList == null) return;
        ASTNode def = defList.findChildByType(MQL4Elements.VAR_DEFINITION);
        if (def == null) return;
        ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
        if (id == null) return;

        holder.newSilentAnnotation(HighlightSeverity.INFORMATION)
                .range(id)
                .textAttributes(INPUT_PARAMETER)
                .create();
    }
}
