/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.openapi.editor.DefaultLanguageHighlighterColors;
import com.intellij.openapi.editor.HighlighterColors;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.fileTypes.SyntaxHighlighter;
import com.intellij.openapi.options.colors.AttributesDescriptor;
import com.intellij.openapi.options.colors.ColorDescriptor;
import com.intellij.openapi.options.colors.ColorSettingsPage;
import com.limemojito.oss.mql.MQL4Icons;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.Icon;
import java.util.Map;

/**
 * Registers MQL under Settings &gt; Editor &gt; Color Scheme so every colour the highlighter and the
 * semantic annotator use (keywords, built-in functions/constants, comments, strings, event handlers,
 * input parameters, …) is user-customisable and discoverable — previously none were exposed.
 */
public final class MQL4ColorSettingsPage implements ColorSettingsPage {

    private static final AttributesDescriptor[] DESCRIPTORS = new AttributesDescriptor[]{
            new AttributesDescriptor("Keyword", DefaultLanguageHighlighterColors.KEYWORD),
            new AttributesDescriptor("Identifier", DefaultLanguageHighlighterColors.IDENTIFIER),
            new AttributesDescriptor("Built-in function", DefaultLanguageHighlighterColors.STATIC_METHOD),
            new AttributesDescriptor("Built-in constant", DefaultLanguageHighlighterColors.CONSTANT),
            new AttributesDescriptor("Number", DefaultLanguageHighlighterColors.NUMBER),
            new AttributesDescriptor("String", DefaultLanguageHighlighterColors.STRING),
            new AttributesDescriptor("Operator", DefaultLanguageHighlighterColors.OPERATION_SIGN),
            new AttributesDescriptor("Preprocessor directive", DefaultLanguageHighlighterColors.METADATA),
            new AttributesDescriptor("Line comment", DefaultLanguageHighlighterColors.LINE_COMMENT),
            new AttributesDescriptor("Block comment", DefaultLanguageHighlighterColors.BLOCK_COMMENT),
            new AttributesDescriptor("Bad character", HighlighterColors.BAD_CHARACTER),
            // Semantic (annotator) keys:
            new AttributesDescriptor("Semantic//Event handler name", MQL4Annotator.EVENT_HANDLER_NAME),
            new AttributesDescriptor("Semantic//Input parameter", MQL4Annotator.INPUT_PARAMETER),
    };

    // Maps the <tags> in the demo text to the semantic descriptor keys.
    private static final Map<String, TextAttributesKey> ADDITIONAL_TAGS = Map.of(
            "eventHandler", MQL4Annotator.EVENT_HANDLER_NAME,
            "input", MQL4Annotator.INPUT_PARAMETER
    );

    @Override
    public @Nullable Icon getIcon() {
        return MQL4Icons.File;
    }

    @Override
    public @NotNull SyntaxHighlighter getHighlighter() {
        return new MQL4SyntaxHighlighter();
    }

    @Override
    public @NotNull String getDemoText() {
        return """
                //--- Expert Advisor sample
                #property strict
                #include <Trade/Trade.mqh>

                input double <input>LotSize</input> = 0.1;   // risk per trade
                int handle = INVALID_HANDLE;

                int <eventHandler>OnInit</eventHandler>()
                {
                    handle = iMA(_Symbol, PERIOD_M5, 14, 0, MODE_EMA, PRICE_CLOSE);
                    if(handle == INVALID_HANDLE)
                        return INIT_FAILED;
                    return INIT_SUCCEEDED;
                }

                void <eventHandler>OnTick</eventHandler>()
                {
                    double buffer[];
                    if(CopyBuffer(handle, 0, 0, 1, buffer) > 0)
                        Print("EMA = ", buffer[0]);
                }
                """;
    }

    @Override
    public @Nullable Map<String, TextAttributesKey> getAdditionalHighlightingTagToDescriptorMap() {
        return ADDITIONAL_TAGS;
    }

    @Override
    public AttributesDescriptor @NotNull [] getAttributeDescriptors() {
        return DESCRIPTORS;
    }

    @Override
    public ColorDescriptor @NotNull [] getColorDescriptors() {
        return ColorDescriptor.EMPTY_ARRAY;
    }

    @Override
    public @NotNull String getDisplayName() {
        return "MQL";
    }
}
