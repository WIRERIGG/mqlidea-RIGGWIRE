/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.openapi.fileTypes.LanguageFileType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.*;

/* Each file in IDEA has type. This is type for MQL4 Language sources. */
public class MQL5FileType extends LanguageFileType {

    public static final MQL5FileType INSTANCE = new MQL5FileType();

    public static final String SOURCE_FILE_EXTENSION = "mq5";

    public static final String HEADER_FILE_EXTENSION = "mqh";

    /** A small hack to enable basic support for MQL5 using the MQL4 specs. */
    private MQL5FileType() {
        super(MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public String getName() {
        return "MQL5 File";
    }

    @NotNull
    @Override
    public String getDescription() {
        return "MQL5 language file";
    }

    @NotNull
    @Override
    public String getDefaultExtension() {
        return SOURCE_FILE_EXTENSION;
    }

    @Nullable
    @Override
    public Icon getIcon() {
        return MQL4Icons.MQL5File;
    }
}
