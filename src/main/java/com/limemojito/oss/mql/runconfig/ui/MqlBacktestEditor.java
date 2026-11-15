/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig.ui;

import com.intellij.openapi.fileChooser.FileChooserDescriptorFactory;
import com.intellij.openapi.options.SettingsEditor;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.ui.ComboBox;
import com.intellij.openapi.ui.TextFieldWithBrowseButton;
import com.intellij.ui.components.JBTextField;
import com.intellij.util.ui.FormBuilder;
import com.limemojito.oss.mql.runconfig.MqlBacktestConfiguration;
import org.jetbrains.annotations.NotNull;

import javax.swing.JComponent;

public class MqlBacktestEditor extends SettingsEditor<MqlBacktestConfiguration> {

    private static final String[] MODELS = {
            "0: Every tick", "1: 1 minute OHLC", "2: Open prices only", "3: Math calculations", "4: Every tick based on real ticks"};

    private final JBTextField expert = new JBTextField();
    private final JBTextField symbol = new JBTextField();
    private final JBTextField from = new JBTextField();
    private final JBTextField to = new JBTextField();
    private final ComboBox<String> model = new ComboBox<>(MODELS);
    private final JBTextField period = new JBTextField();
    private final JBTextField deposit = new JBTextField();
    private final TextFieldWithBrowseButton inputs = new TextFieldWithBrowseButton();
    private final JBTextField timeout = new JBTextField();

    public MqlBacktestEditor(@NotNull Project project) {
        inputs.addBrowseFolderListener(project, FileChooserDescriptorFactory.singleFile()
                .withTitle("EA Inputs").withDescription("A MetaTrader .set file, or Name=Value lines"));
        expert.getEmptyText().setText("the bridge's EA (RIGGWIRE\\RIGGWIRE_FINAL.ex5 or MT5_EA_NAME)");
        period.getEmptyText().setText("M5");
        deposit.getEmptyText().setText("100000");
        timeout.getEmptyText().setText("by tick model");
        from.getEmptyText().setText("YYYY.MM.DD");
        to.getEmptyText().setText("YYYY.MM.DD");
    }

    @Override
    protected void resetEditorFrom(@NotNull MqlBacktestConfiguration c) {
        expert.setText(c.expert);
        symbol.setText(c.symbol);
        from.setText(c.from);
        to.setText(c.to);
        model.setSelectedIndex(c.model >= 0 && c.model < MODELS.length ? c.model : 1);
        period.setText(c.period);
        deposit.setText(c.deposit);
        inputs.setText(c.inputsFile);
        timeout.setText(c.timeout);
    }

    @Override
    protected void applyEditorTo(@NotNull MqlBacktestConfiguration c) {
        c.expert = expert.getText().trim();
        c.symbol = symbol.getText().trim();
        c.from = from.getText().trim();
        c.to = to.getText().trim();
        c.model = model.getSelectedIndex();
        c.period = period.getText().trim();
        c.deposit = deposit.getText().trim();
        c.inputsFile = inputs.getText().trim();
        c.timeout = timeout.getText().trim();
    }

    @NotNull
    @Override
    protected JComponent createEditor() {
        return FormBuilder.createFormBuilder()
                .addLabeledComponent("EA (.ex5 under MQL5\\Experts):", expert)
                .addLabeledComponent("Symbol:", symbol)
                .addLabeledComponent("From:", from)
                .addLabeledComponent("To:", to)
                .addLabeledComponent("Tick model:", model)
                .addLabeledComponent("Timeframe:", period)
                .addLabeledComponent("Deposit:", deposit)
                .addLabeledComponent("Inputs (.set):", inputs)
                .addLabeledComponent("Timeout (seconds):", timeout)
                .addComponentFillVertically(new javax.swing.JPanel(), 0)
                .getPanel();
    }
}
