/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.openapi.project.Project;
import com.intellij.openapi.projectRoots.ProjectJdkTable;
import com.intellij.openapi.projectRoots.Sdk;
import com.intellij.openapi.roots.ProjectRootManager;
import com.intellij.openapi.util.io.FileUtil;
import com.intellij.openapi.vfs.LocalFileSystem;
import com.intellij.openapi.vfs.VirtualFile;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.sdk.MQL4SdkType;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

/**
 * Best-effort discovery of MQL4/MQL5 "Include" root directories, for resolving
 * {@code #include <Angle/Bracket.mqh>} (see {@link MqlIncludeFileReferenceSet}). Angle-bracket
 * includes are resolved against the MetaTrader/MetaEditor SDK home, not the project directory.
 *
 * <p>Discovery order: (1) the project's configured {@link MQL4SdkType} SDK, if any; (2) a short
 * list of well-known install locations (this Mac's Wine bridge layout, plus common Windows/Wine
 * paths) as a zero-configuration fallback. This mirrors {@code MQL4SdkType.suggestHomePath()} but
 * doesn't replace the proper Settings-driven SDK-home story that Phase 1's compiler service /
 * Phase 8 settings pass owns -- this is intentionally a light heuristic so Ctrl-click on a
 * Standard-Library include works out of the box, not a full SDK configuration UI.</p>
 */
public final class MqlIncludeRoots {

    private MqlIncludeRoots() {
    }

    @NotNull
    public static List<VirtualFile> candidateIncludeRoots(@NotNull Project project) {
        List<VirtualFile> roots = new ArrayList<>();
        LocalFileSystem lfs = LocalFileSystem.getInstance();

        for (String home : sdkHomes(project)) {
            addIfDirectory(roots, lfs, home + "/MQL5/Include");
            addIfDirectory(roots, lfs, home + "/MQL4/Include");
        }

        String userHome = System.getProperty("user.home");
        if (userHome != null) {
            // This Mac's Wine bridge layout (~/.claude/skills/mt5-wine-bridge/SKILL.md).
            String wineHome = userHome + "/Library/Application Support/net.metaquotes.wine.metatrader5"
                    + "/drive_c/Program Files/MetaTrader 5";
            addIfDirectory(roots, lfs, wineHome + "/MQL5/Include");
            addIfDirectory(roots, lfs, wineHome + "/MQL4/Include");
            // Generic Wine prefix fallback.
            String genericWine = userHome + "/.wine/drive_c/Program Files (x86)/MetaTrader 5";
            addIfDirectory(roots, lfs, genericWine + "/MQL5/Include");
            addIfDirectory(roots, lfs, genericWine + "/MQL4/Include");
        }
        addIfDirectory(roots, lfs, "C:/Program Files/MetaTrader 5/MQL5/Include");
        addIfDirectory(roots, lfs, "C:/Program Files (x86)/MetaTrader 5/MQL4/Include");

        return roots;
    }

    @NotNull
    private static List<String> sdkHomes(@NotNull Project project) {
        List<String> homes = new ArrayList<>();
        Sdk projectSdk = ProjectRootManager.getInstance(project).getProjectSdk();
        if (projectSdk != null && projectSdk.getSdkType() instanceof MQL4SdkType) {
            String home = projectSdk.getHomePath();
            if (home != null) {
                homes.add(home);
            }
        }
        for (Sdk sdk : ProjectJdkTable.getInstance().getAllJdks()) {
            if (sdk.getSdkType() instanceof MQL4SdkType && sdk.getHomePath() != null) {
                homes.add(sdk.getHomePath());
            }
        }
        return homes;
    }

    private static void addIfDirectory(@NotNull List<VirtualFile> roots, @NotNull LocalFileSystem lfs, @NotNull String path) {
        File dir = new File(FileUtil.toSystemDependentName(path));
        if (!dir.isDirectory()) {
            return;
        }
        VirtualFile vf = lfs.findFileByIoFile(dir);
        if (vf != null && !roots.contains(vf)) {
            roots.add(vf);
        }
    }
}
