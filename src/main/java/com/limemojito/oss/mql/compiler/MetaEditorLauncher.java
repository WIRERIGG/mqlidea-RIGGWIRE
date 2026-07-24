/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.compiler;

import com.intellij.execution.configurations.GeneralCommandLine;
import com.intellij.openapi.projectRoots.ProjectJdkTable;
import com.intellij.openapi.projectRoots.Sdk;
import com.limemojito.oss.mql.sdk.MQL4SdkType;
import com.limemojito.oss.mql.util.OSUtils;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.io.File;
import java.util.Arrays;

/**
 * Windows launcher: runs the configured MQL4/MQL5 SDK's {@code metaeditor64.exe} (falling back to
 * the 32-bit {@code metaeditor.exe}) directly &mdash; no Wine involved. Requires an SDK of type
 * {@link MQL4SdkType} to be registered (Project Structure &gt; SDKs); {@link #findMetaEditorExe()}
 * mirrors the lookup {@code MQL4RunCompilerConfiguration.getSdk()} already does for the run
 * configuration, generalized here to "any configured MQL4 SDK" since the compiler service has no
 * specific run configuration to read an SDK name from.
 */
public final class MetaEditorLauncher implements MqlCompilerLauncher {

    @Override
    @NotNull
    public String name() {
        return "MetaEditor";
    }

    @Override
    @Nullable
    public GeneralCommandLine commandFor(@NotNull File source) {
        if (!OSUtils.isWindowsOS()) {
            return null; // this launcher shells out to the native .exe directly; only meaningful on Windows
        }
        File exe = findMetaEditorExe();
        if (exe == null) {
            return null;
        }
        return new GeneralCommandLine(exe.getAbsolutePath())
                .withParameters("/compile:" + source.getAbsolutePath(), "/log")
                .withParentEnvironmentType(GeneralCommandLine.ParentEnvironmentType.CONSOLE);
    }

    /**
     * Finds {@code metaeditor64.exe}/{@code metaeditor.exe} under any SDK of type {@link MQL4SdkType}
     * registered in {@link ProjectJdkTable} (the table is application-wide, matching how
     * {@code MQL4RunCompilerConfiguration.getSdk()} resolves SDKs today). Package-visible so
     * {@link WineLauncher} can reuse the same exe discovery for its explicit-Wine strategy.
     */
    @Nullable
    static File findMetaEditorExe() {
        Sdk sdk = findMql4Sdk();
        if (sdk == null) {
            return null;
        }
        String home = sdk.getHomePath();
        if (home == null) {
            return null;
        }
        File exe64 = new File(home, "metaeditor64.exe");
        if (exe64.isFile()) {
            return exe64;
        }
        File exe32 = new File(home, "metaeditor.exe");
        return exe32.isFile() ? exe32 : null;
    }

    @Nullable
    private static Sdk findMql4Sdk() {
        return Arrays.stream(ProjectJdkTable.getInstance().getAllJdks())
                .filter(s -> s.getSdkType() instanceof MQL4SdkType)
                .findFirst()
                .orElse(null);
    }
}
