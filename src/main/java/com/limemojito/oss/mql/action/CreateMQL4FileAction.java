/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.action;

import com.intellij.ide.actions.CreateFileAction;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL4Icons;
import com.limemojito.oss.mql.MQL4PluginResources;

/**
 * The "New MQL4 File" action.
 */
public class CreateMQL4FileAction extends CreateFileAction {
    public CreateMQL4FileAction() {
        super(()->MQL4PluginResources.message("action.New-MQL-File.text"),()-> MQL4PluginResources.message("action.New-MQL-File.description"), ()->MQL4Icons.File);
    }

    @Override
    protected String getDefaultExtension() {
        return MQL4FileType.SOURCE_FILE_EXTENSION;
    }
}
