/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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
    // MQL4 files
    Icon File = IconLoader.getIcon("/icons/mql4.png", callingClassLoader());

    // Classes and structs
    Icon Class = AllIcons.Nodes.Class;
    Icon Struct = IconLoader.getIcon("/icons/struct.png", callingClassLoader());
    Icon Interface = AllIcons.Nodes.Interface;

    // Functions and methods
    Icon FunctionDeclaration = new LayeredIcon(AllIcons.Nodes.Function, AllIcons.Nodes.Symlink);
    Icon FunctionDefinition = AllIcons.Nodes.Function;
    Icon MethodDeclaration = new LayeredIcon(AllIcons.Nodes.Method, AllIcons.Nodes.Symlink);
    Icon MethodDefinition = AllIcons.Nodes.Method;

    @NotNull
    private static java.lang.Class<?> callingClassLoader() {
        return Objects.requireNonNull(ReflectionUtil.getGrandCallerClass());
    }
}
