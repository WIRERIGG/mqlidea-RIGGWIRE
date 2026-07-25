/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.icons.AllIcons;
import com.intellij.openapi.util.IconLoader;
import com.intellij.ui.LayeredIcon;
import com.intellij.util.ReflectionUtil;
import org.jetbrains.annotations.NotNull;

import javax.swing.*;
import java.util.Objects;

public interface MQL4Icons {
    // File type icons -- these are the STABLE base icons a file's FileType.getIcon() returns, so the
    // first painted (DeferredIcon placeholder) icon already equals the final one: no wrong->right flash.
    Icon File = IconLoader.getIcon("/icons/mql4.svg", callingClassLoader());
    Icon MQL5File = IconLoader.getIcon("/icons/mql5.svg", callingClassLoader());
    Icon HeaderFile = IconLoader.getIcon("/icons/mqh.svg", callingClassLoader());

    // Problem-state variants: the SAME base icon plus a warning badge overlay (never a different base
    // icon), so a file that gains/loses problems only adds/removes the badge -- the base never swaps.
    Icon FileProblem = withWarningBadge(File);
    Icon MQL5FileProblem = withWarningBadge(MQL5File);
    Icon HeaderFileProblem = withWarningBadge(HeaderFile);

    // Classes and structs
    Icon Class = AllIcons.Nodes.Class;
    Icon Struct = IconLoader.getIcon("/icons/struct.svg", callingClassLoader());
    Icon Interface = AllIcons.Nodes.Interface;

    // Functions and methods
    Icon FunctionDeclaration = createLayeredIcon(AllIcons.Nodes.Function);
    Icon FunctionDefinition = AllIcons.Nodes.Function;
    Icon MethodDeclaration = createLayeredIcon(AllIcons.Nodes.Method);
    Icon MethodDefinition = AllIcons.Nodes.Method;

    @NotNull
    private static Icon createLayeredIcon(@NotNull Icon base) {
        LayeredIcon icon = new LayeredIcon(2);
        icon.setIcon(base, 0);
        icon.setIcon(AllIcons.Nodes.Symlink, 1);
        return icon;
    }

    /** Base file icon overlaid with a small warning badge in the bottom-right corner. */
    @NotNull
    private static Icon withWarningBadge(@NotNull Icon base) {
        LayeredIcon icon = new LayeredIcon(2);
        icon.setIcon(base, 0);
        icon.setIcon(AllIcons.Nodes.WarningMark, 1, SwingConstants.SOUTH_EAST);
        return icon;
    }

    @NotNull
    private static java.lang.Class<?> callingClassLoader() {
        return Objects.requireNonNull(ReflectionUtil.getGrandCallerClass());
    }
}
