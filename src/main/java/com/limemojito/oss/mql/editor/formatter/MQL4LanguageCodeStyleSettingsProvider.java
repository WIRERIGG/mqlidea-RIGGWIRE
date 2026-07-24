/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.formatter;

import com.intellij.lang.Language;
import com.intellij.psi.codeStyle.CodeStyleSettingsCustomizable;
import com.intellij.psi.codeStyle.CommonCodeStyleSettings;
import com.intellij.psi.codeStyle.LanguageCodeStyleSettingsProvider;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.MQL4Language;

/**
 * Phase 7 (REVAMP_PLAN.md #Phase 7): Settings &gt; Code Style &gt; MQL4 page -- indent size plus the
 * conservative set of spacing toggles {@link MQL4FormattingModelBuilder} actually consults.
 *
 * <p>Defaults: 4-space indent, 8-space continuation indent, spaces (not tabs) -- a
 * MetaEditor-compatible baseline (MetaEditor's own default is a same-width-ish, space-based
 * indent; 4 was picked per REVAMP_PLAN.md Phase 7 absent a reference corpus dictating otherwise).
 * Every spacing toggle below defaults to what MetaEditor's own auto-formatting produces:
 * spaces after commas, spaces around assignment/comparison/logical operators, a space between a
 * control keyword and its condition's opening parenthesis, and no space before a call's or a
 * function declaration's opening parenthesis.</p>
 */
public final class MQL4LanguageCodeStyleSettingsProvider extends LanguageCodeStyleSettingsProvider {

    private static final String SAMPLE_CODE =
            "void OnTick()\n" +
            "{\n" +
            "   double bid=SymbolInfoDouble(_Symbol,SYMBOL_BID);\n" +
            "   if(bid>0)\n" +
            "   {\n" +
            "      for(int i=0;i<OrdersTotal();i++)\n" +
            "      {\n" +
            "         OrderSelect(i,SELECT_BY_POS);\n" +
            "      }\n" +
            "   }\n" +
            "}\n";

    @NotNull
    @Override
    public Language getLanguage() {
        return MQL4Language.INSTANCE;
    }

    @Override
    public String getCodeSample(@NotNull SettingsType settingsType) {
        return SAMPLE_CODE;
    }

    @Override
    public void customizeSettings(@NotNull CodeStyleSettingsCustomizable consumer, @NotNull SettingsType settingsType) {
        if (settingsType == SettingsType.SPACING_SETTINGS) {
            consumer.showStandardOptions(
                    "SPACE_AFTER_COMMA",
                    "SPACE_BEFORE_COMMA",
                    "SPACE_AROUND_ASSIGNMENT_OPERATORS",
                    "SPACE_AROUND_LOGICAL_OPERATORS",
                    "SPACE_AROUND_EQUALITY_OPERATORS",
                    "SPACE_AROUND_RELATIONAL_OPERATORS",
                    "SPACE_BEFORE_IF_PARENTHESES",
                    "SPACE_BEFORE_WHILE_PARENTHESES",
                    "SPACE_BEFORE_FOR_PARENTHESES",
                    "SPACE_BEFORE_SWITCH_PARENTHESES",
                    "SPACE_BEFORE_METHOD_CALL_PARENTHESES",
                    "SPACE_BEFORE_METHOD_PARENTHESES"
            );
        } else if (settingsType == SettingsType.BLANK_LINES_SETTINGS) {
            consumer.showStandardOptions("KEEP_BLANK_LINES_IN_CODE");
        }
    }

    @Override
    protected void customizeDefaults(@NotNull CommonCodeStyleSettings commonSettings,
                                      @NotNull CommonCodeStyleSettings.IndentOptions indentOptions) {
        indentOptions.INDENT_SIZE = 4;
        indentOptions.CONTINUATION_INDENT_SIZE = 8;
        indentOptions.TAB_SIZE = 4;
        indentOptions.USE_TAB_CHARACTER = false;

        commonSettings.SPACE_AFTER_COMMA = true;
        commonSettings.SPACE_BEFORE_COMMA = false;
        commonSettings.SPACE_AROUND_ASSIGNMENT_OPERATORS = true;
        commonSettings.SPACE_AROUND_LOGICAL_OPERATORS = true;
        commonSettings.SPACE_AROUND_EQUALITY_OPERATORS = true;
        commonSettings.SPACE_AROUND_RELATIONAL_OPERATORS = true;
        commonSettings.SPACE_BEFORE_IF_PARENTHESES = true;
        commonSettings.SPACE_BEFORE_WHILE_PARENTHESES = true;
        commonSettings.SPACE_BEFORE_FOR_PARENTHESES = true;
        commonSettings.SPACE_BEFORE_SWITCH_PARENTHESES = true;
        commonSettings.SPACE_BEFORE_METHOD_CALL_PARENTHESES = false;
        commonSettings.SPACE_BEFORE_METHOD_PARENTHESES = false;
    }
}
