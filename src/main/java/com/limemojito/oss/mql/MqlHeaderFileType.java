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

/**
 * File type for MQL header files ({@code .mqh}). Split out from {@link MQL4FileType} (which used to
 * also claim {@code .mqh}) so a header carries a STABLE, always-correct header icon at the FileType
 * level -- the platform's deferred-icon placeholder for a {@code .mqh} then already equals the final
 * icon, fixing the project-tree and editor-tab icon flash. Reuses {@link MQL4Language} so headers are
 * still parsed and inspected exactly as before; dialect is resolved per-project by {@link MqlDialect}.
 */
public final class MqlHeaderFileType extends LanguageFileType {

    public static final MqlHeaderFileType INSTANCE = new MqlHeaderFileType();

    public static final String HEADER_FILE_EXTENSION = "mqh";

    private MqlHeaderFileType() {
        super(MQL4Language.INSTANCE);
    }

    @NotNull
    @Override
    public String getName() {
        return "MQL Header";
    }

    /**
     * {@link LanguageFileType} defaults the display name to the language's display name ("MQL4"),
     * which would collide with {@link MQL4FileType}/{@link MQL5FileType} and trigger a
     * FileTypeManager duplicate-display-name warning. Override to keep it unique.
     */
    @NotNull
    @Override
    public String getDisplayName() {
        return "MQL Header";
    }

    @NotNull
    @Override
    public String getDescription() {
        return "MQL header file";
    }

    @NotNull
    @Override
    public String getDefaultExtension() {
        return HEADER_FILE_EXTENSION;
    }

    @Nullable
    @Override
    public Icon getIcon() {
        return MQL4Icons.HeaderFile;
    }
}
