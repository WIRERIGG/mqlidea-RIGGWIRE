/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.settings;

import com.intellij.openapi.options.Configurable;
import com.intellij.openapi.ui.ComboBox;
import com.intellij.util.FileContentUtil;
import com.intellij.util.ui.JBUI;
import com.limemojito.oss.mql.healing.ai.ApiKeyStorage;

import java.awt.FlowLayout;
import java.awt.GridBagConstraints;
import java.awt.GridBagLayout;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JComponent;
import javax.swing.JLabel;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JSeparator;
import javax.swing.JSpinner;
import javax.swing.JTextField;
import javax.swing.SpinnerNumberModel;
import org.jetbrains.annotations.Nls;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

//todo: SearchableConfigurable,
public class MQL4PluginSettingsPanel extends JPanel implements Configurable {

    @NotNull
    private final JComboBox<String> docsLangCombo;

    @NotNull
    private final JComboBox<String> errorAnalysisCombo;

    @NotNull
    private final MQL4PluginSettings settings;

    // AI Healing fields
    private final JPasswordField grokApiKeyField;
    private final JPasswordField claudeApiKeyField;
    private final JComboBox<String> grokModelCombo;
    private final JComboBox<String> claudeModelCombo;
    private final JSpinner healingDelaySpinner;
    private final JSpinner healingConcurrencySpinner;
    private final JCheckBox autoHealCheckbox;
    private final JCheckBox useClaudeCliCheckbox;
    private final JTextField claudeCliPathField;

    public MQL4PluginSettingsPanel() {
        this.settings = MQL4PluginSettings.getInstance();

        setLayout(new FlowLayout(FlowLayout.LEFT));

        JPanel form = new JPanel(new GridBagLayout());
        form.setLayout(new GridBagLayout());
        add(form);

        GridBagConstraints gc = new GridBagConstraints();
        gc.fill = GridBagConstraints.HORIZONTAL;
        gc.insets = JBUI.insets(10);

        gc.gridx = 0;
        gc.gridy = 0;
        form.add(new JLabel("Docs language: "), gc);

        gc.gridx = 1;
        gc.gridy = 0;
        docsLangCombo = new ComboBox<>(new String[]{"Russian", "English"});
        docsLangCombo.setSelectedIndex(settings.isUseEnDocs() ? 1 : 0);
        form.add(docsLangCombo, gc);

        gc.gridx = 0;
        gc.gridy = 1;
        form.add(new JLabel("Error analysis: "), gc);

        gc.gridx = 1;
        gc.gridy = 1;
        errorAnalysisCombo = new ComboBox<>(new String[]{"On", "Off"});
        errorAnalysisCombo.setSelectedIndex(settings.performErrorAnalysis() ? 0 : 1);
        form.add(errorAnalysisCombo, gc);

        // Separator
        gc.gridx = 0;
        gc.gridy = 2;
        gc.gridwidth = 2;
        form.add(new JSeparator(), gc);
        gc.gridwidth = 1;

        // AI Healing section header
        gc.gridx = 0;
        gc.gridy = 3;
        gc.gridwidth = 2;
        JLabel healingHeader = new JLabel("AI Code Healing");
        healingHeader.setFont(healingHeader.getFont().deriveFont(java.awt.Font.BOLD));
        form.add(healingHeader, gc);
        gc.gridwidth = 1;

        // Grok API Key
        gc.gridx = 0;
        gc.gridy = 4;
        form.add(new JLabel("Grok API Key: "), gc);

        gc.gridx = 1;
        gc.gridy = 4;
        grokApiKeyField = new JPasswordField(30);
        String existingGrokKey = ApiKeyStorage.getApiKey(ApiKeyStorage.GROK_KEY);
        if (existingGrokKey != null) {
            grokApiKeyField.setText(existingGrokKey);
        }
        form.add(grokApiKeyField, gc);

        // Grok Model
        gc.gridx = 0;
        gc.gridy = 5;
        form.add(new JLabel("Grok Model: "), gc);

        gc.gridx = 1;
        gc.gridy = 5;
        grokModelCombo = new ComboBox<>(new String[]{"grok-2", "grok-2-mini", "grok-3"});
        grokModelCombo.setSelectedItem(settings.getGrokModel());
        form.add(grokModelCombo, gc);

        // Claude API Key
        gc.gridx = 0;
        gc.gridy = 6;
        form.add(new JLabel("Claude API Key: "), gc);

        gc.gridx = 1;
        gc.gridy = 6;
        claudeApiKeyField = new JPasswordField(30);
        String existingClaudeKey = ApiKeyStorage.getApiKey(ApiKeyStorage.CLAUDE_KEY);
        if (existingClaudeKey != null) {
            claudeApiKeyField.setText(existingClaudeKey);
        }
        form.add(claudeApiKeyField, gc);

        // Claude Model
        gc.gridx = 0;
        gc.gridy = 7;
        form.add(new JLabel("Claude Model: "), gc);

        gc.gridx = 1;
        gc.gridy = 7;
        claudeModelCombo = new ComboBox<>(new String[]{
                "claude-sonnet-4-5-20250929",
                "claude-haiku-4-5-20251001",
                "claude-opus-4-6"
        });
        claudeModelCombo.setSelectedItem(settings.getClaudeModel());
        form.add(claudeModelCombo, gc);

        // Claude Code CLI toggle — when on, the Claude API key above is not required
        gc.gridx = 0;
        gc.gridy = 8;
        gc.gridwidth = 2;
        useClaudeCliCheckbox = new JCheckBox(
                "Power healing with Claude Code CLI (claude -p) — uses your Claude Code login instead of an API key",
                settings.isUseClaudeCli());
        useClaudeCliCheckbox.setToolTipText(
                "When enabled, the Claude API key above is unused for healing (Grok still needs its key).");
        form.add(useClaudeCliCheckbox, gc);
        gc.gridwidth = 1;

        // Claude CLI path
        gc.gridx = 0;
        gc.gridy = 9;
        form.add(new JLabel("Claude CLI path (blank = auto-detect): "), gc);

        gc.gridx = 1;
        gc.gridy = 9;
        claudeCliPathField = new JTextField(30);
        claudeCliPathField.setText(settings.getClaudeCliPath() != null ? settings.getClaudeCliPath() : "");
        form.add(claudeCliPathField, gc);

        // Grey out the (unused) Claude API key field while the CLI powers healing
        claudeApiKeyField.setEnabled(!useClaudeCliCheckbox.isSelected());
        claudeCliPathField.setEnabled(useClaudeCliCheckbox.isSelected());
        useClaudeCliCheckbox.addItemListener(e -> {
            claudeApiKeyField.setEnabled(!useClaudeCliCheckbox.isSelected());
            claudeCliPathField.setEnabled(useClaudeCliCheckbox.isSelected());
        });

        // Healing Delay
        gc.gridx = 0;
        gc.gridy = 10;
        form.add(new JLabel("Healing interval (minutes): "), gc);

        gc.gridx = 1;
        gc.gridy = 10;
        healingDelaySpinner = new JSpinner(new SpinnerNumberModel(
                settings.getHealingDelayMinutes(), 1, 60, 1));
        form.add(healingDelaySpinner, gc);

        // Healing concurrency (CLI mode worker pool size)
        gc.gridx = 0;
        gc.gridy = 11;
        form.add(new JLabel("Parallel Claude sessions (1-8): "), gc);

        gc.gridx = 1;
        gc.gridy = 11;
        healingConcurrencySpinner = new JSpinner(new SpinnerNumberModel(
                settings.getHealingConcurrency(), 1, 8, 1));
        form.add(healingConcurrencySpinner, gc);

        // Auto-heal checkbox
        gc.gridx = 0;
        gc.gridy = 12;
        gc.gridwidth = 2;
        autoHealCheckbox = new JCheckBox("Enable automatic AI healing", settings.isAutoHealEnabled());
        form.add(autoHealCheckbox, gc);
        gc.gridwidth = 1;
    }

    @Nls
    @Override
    public String getDisplayName() {
        return "MQL4";
    }

    @Nullable
    @Override
    public String getHelpTopic() {
        return null;
    }

    /**
     * Returns the user interface component for editing the configuration.
     *
     * @return the component instance.
     */
    @Nullable
    @Override
    public JComponent createComponent() {
        return this;
    }

    /**
     * Checks if the settings in the user interface component were modified by the user and
     * need to be saved.
     *
     * @return true if the settings were modified, false otherwise.
     */
    @Override
    public boolean isModified() {
        return docsLangCombo.getSelectedIndex() != (settings.isUseEnDocs() ? 1 : 0)
                || isErrorAnalysisFlagChanged()
                || isHealingSettingsChanged();
    }

    private boolean isErrorAnalysisFlagChanged() {
        return errorAnalysisCombo.getSelectedIndex() != (settings.performErrorAnalysis() ? 0 : 1);
    }

    private boolean isHealingSettingsChanged() {
        int spinnerValue = (Integer) healingDelaySpinner.getValue();
        String grokModel = (String) grokModelCombo.getSelectedItem();
        String claudeModel = (String) claudeModelCombo.getSelectedItem();

        return spinnerValue != settings.getHealingDelayMinutes()
                || (Integer) healingConcurrencySpinner.getValue() != settings.getHealingConcurrency()
                || autoHealCheckbox.isSelected() != settings.isAutoHealEnabled()
                || useClaudeCliCheckbox.isSelected() != settings.isUseClaudeCli()
                || !claudeCliPathField.getText().trim().equals(storedClaudeCliPath())
                || (grokModel != null && !grokModel.equals(settings.getGrokModel()))
                || (claudeModel != null && !claudeModel.equals(settings.getClaudeModel()))
                || isApiKeyChanged(grokApiKeyField, ApiKeyStorage.GROK_KEY)
                || isApiKeyChanged(claudeApiKeyField, ApiKeyStorage.CLAUDE_KEY);
    }

    @NotNull
    private String storedClaudeCliPath() {
        String stored = settings.getClaudeCliPath();
        return stored != null ? stored : "";
    }

    private static boolean isApiKeyChanged(@NotNull JPasswordField field, @NotNull String keyName) {
        String current = new String(field.getPassword());
        String stored = ApiKeyStorage.getApiKey(keyName);
        return !current.equals(stored != null ? stored : "");
    }

    /**
     * Store the settings from configurable to other components.
     */
    @Override
    public void apply() {
        settings.setUseEnDocs(docsLangCombo.getSelectedIndex() == 1);
        if (isErrorAnalysisFlagChanged()) {
            FileContentUtil.reparseOpenedFiles();
        }
        settings.setPerformErrorAnalysis(errorAnalysisCombo.getSelectedIndex() == 0);

        // Save healing settings
        settings.setHealingDelayMinutes((Integer) healingDelaySpinner.getValue());
        settings.setHealingConcurrency((Integer) healingConcurrencySpinner.getValue());
        settings.setAutoHealEnabled(autoHealCheckbox.isSelected());
        settings.setUseClaudeCli(useClaudeCliCheckbox.isSelected());
        settings.setClaudeCliPath(claudeCliPathField.getText().trim());

        String grokModel = (String) grokModelCombo.getSelectedItem();
        if (grokModel != null) settings.setGrokModel(grokModel);

        String claudeModel = (String) claudeModelCombo.getSelectedItem();
        if (claudeModel != null) settings.setClaudeModel(claudeModel);

        // Save API keys
        String grokKey = new String(grokApiKeyField.getPassword());
        ApiKeyStorage.setApiKey(ApiKeyStorage.GROK_KEY, grokKey.isBlank() ? null : grokKey);

        String claudeKey = new String(claudeApiKeyField.getPassword());
        ApiKeyStorage.setApiKey(ApiKeyStorage.CLAUDE_KEY, claudeKey.isBlank() ? null : claudeKey);
    }

    /**
     * Load settings from other components to configurable.
     */
    @Override
    public void reset() {
        docsLangCombo.setSelectedIndex(settings.isUseEnDocs() ? 1 : 0);
        errorAnalysisCombo.setSelectedIndex(settings.performErrorAnalysis() ? 0 : 1);

        healingDelaySpinner.setValue(settings.getHealingDelayMinutes());
        healingConcurrencySpinner.setValue(settings.getHealingConcurrency());
        autoHealCheckbox.setSelected(settings.isAutoHealEnabled());
        useClaudeCliCheckbox.setSelected(settings.isUseClaudeCli());
        claudeCliPathField.setText(storedClaudeCliPath());
        claudeApiKeyField.setEnabled(!settings.isUseClaudeCli());
        claudeCliPathField.setEnabled(settings.isUseClaudeCli());
        grokModelCombo.setSelectedItem(settings.getGrokModel());
        claudeModelCombo.setSelectedItem(settings.getClaudeModel());

        String grokKey = ApiKeyStorage.getApiKey(ApiKeyStorage.GROK_KEY);
        grokApiKeyField.setText(grokKey != null ? grokKey : "");

        String claudeKey = ApiKeyStorage.getApiKey(ApiKeyStorage.CLAUDE_KEY);
        claudeApiKeyField.setText(claudeKey != null ? claudeKey : "");
    }
}
