/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql;

import com.intellij.icons.AllIcons;
import com.intellij.openapi.util.IconLoader;
import com.intellij.ui.LayeredIcon;
import com.intellij.util.IconUtil;
import com.intellij.util.ReflectionUtil;
import org.jetbrains.annotations.NotNull;

import javax.swing.*;
import java.util.Objects;

public interface MQL4Icons {
    // File type icons
    Icon File = IconLoader.getIcon("/icons/mql4.svg", callingClassLoader());
    Icon MQL5File = IconLoader.getIcon("/icons/mql5.svg", callingClassLoader());
    Icon HeaderFile = IconLoader.getIcon("/icons/mqh.svg", callingClassLoader());

    // Desaturated (gray) variants for files with problems
    Icon FileGray = IconUtil.desaturate(File);
    Icon MQL5FileGray = IconUtil.desaturate(MQL5File);
    Icon HeaderFileGray = IconUtil.desaturate(HeaderFile);

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

    @NotNull
    private static java.lang.Class<?> callingClassLoader() {
        return Objects.requireNonNull(ReflectionUtil.getGrandCallerClass());
    }
}
