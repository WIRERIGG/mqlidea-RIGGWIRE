/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.navigation.ItemPresentation;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.roots.AdditionalLibraryRootsProvider;
import com.intellij.openapi.roots.SyntheticLibrary;
import com.intellij.openapi.vfs.VirtualFile;
import com.limemojito.oss.mql.MQL4Icons;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.Icon;
import java.util.Collection;
import java.util.List;

/**
 * Makes the MetaTrader {@code MQL5/Include} and {@code MQL4/Include} folders a library, so the stub
 * indexes cover them. Without it, {@code #include <Trade/Trade.mqh>} opens the file but nothing it
 * declares ({@code CTrade}, an MQLTA header's enum constants) resolves, because those headers sit
 * outside the project.
 */
public final class MqlIncludeLibraryProvider extends AdditionalLibraryRootsProvider {

    @NotNull
    @Override
    public Collection<SyntheticLibrary> getAdditionalProjectLibraries(@NotNull Project project) {
        List<VirtualFile> roots = MqlIncludeRoots.computeCandidateIncludeRoots(project);
        return roots.isEmpty() ? List.of() : List.of(new IncludeLibrary(roots));
    }

    @NotNull
    @Override
    public Collection<VirtualFile> getRootsToWatch(@NotNull Project project) {
        return MqlIncludeRoots.computeCandidateIncludeRoots(project);
    }

    private static final class IncludeLibrary extends SyntheticLibrary implements ItemPresentation {
        private final List<VirtualFile> roots;

        IncludeLibrary(@NotNull List<VirtualFile> roots) {
            this.roots = List.copyOf(roots);
        }

        @NotNull
        @Override
        public Collection<VirtualFile> getSourceRoots() {
            return roots;
        }

        @Override
        public boolean equals(Object o) {
            return o instanceof IncludeLibrary other && roots.equals(other.roots);
        }

        @Override
        public int hashCode() {
            return roots.hashCode();
        }

        @Override
        public String getPresentableText() {
            return "MetaTrader Include";
        }

        @Nullable
        @Override
        public Icon getIcon(boolean unused) {
            return MQL4Icons.HeaderFile;
        }
    }
}
