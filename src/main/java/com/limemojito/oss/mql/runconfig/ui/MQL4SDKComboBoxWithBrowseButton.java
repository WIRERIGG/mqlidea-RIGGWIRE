/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.runconfig.ui;

import com.intellij.openapi.fileChooser.FileChooser;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.projectRoots.Sdk;
import com.intellij.openapi.projectRoots.impl.SdkConfigurationUtil;
import com.intellij.openapi.ui.ComponentWithBrowseButton;
import com.intellij.openapi.vfs.VirtualFile;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.sdk.MQL4SdkType;

/**
 * SDK combo box with a browse button that registers a new MQL SDK from a chosen home folder. Built on
 * {@link ComponentWithBrowseButton} and the SDK type's own home chooser (which validates the folder)
 * instead of the deprecated {@code ComboboxWithBrowseButton} and {@code SdkConfigurationUtil.selectSdkHome}.
 */
public class MQL4SDKComboBoxWithBrowseButton extends ComponentWithBrowseButton<MQL4SDKComboBox> {

    @NotNull
    public final MQL4SDKComboBox comboBox;

    public Project project;

    public MQL4SDKComboBoxWithBrowseButton() {
        super(new MQL4SDKComboBox(), null);
        this.comboBox = getChildComponent();

        addActionListener(e -> {
            VirtualFile home = FileChooser.chooseFile(MQL4SdkType.INSTANCE.getHomeChooserDescriptor(), this, project, null);
            if (home == null) {
                return;
            }
            Sdk sdk = SdkConfigurationUtil.createAndAddSDK(home.getPath(), MQL4SdkType.INSTANCE);
            if (sdk == null) {
                return;
            }
            comboBox.addItem(sdk);
            comboBox.setSelectedSdk(sdk);
        });
    }
}
