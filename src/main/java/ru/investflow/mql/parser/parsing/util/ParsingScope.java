/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package ru.investflow.mql.parser.parsing.util;

import com.intellij.lang.PsiBuilder;
import com.intellij.openapi.util.Key;
import org.jetbrains.annotations.NotNull;

import java.util.Stack;

public enum ParsingScope {
    TOP_LEVEL,
    CLASS,
    CODE_BLOCK;

    private static final Key<Stack<ParsingScope>> KEY = new Key<>("ParsingScope");

    public static ParsingScope getScope(@NotNull PsiBuilder b) {
        Stack<ParsingScope> stack = getScopeStack(b);
        return stack == null || stack.isEmpty() ? TOP_LEVEL : stack.peek();
    }

    public static void popScope(@NotNull PsiBuilder b) {
        Stack<ParsingScope> stack = getScopeStack(b);
        stack.pop();
    }

    public static void pushScope(@NotNull PsiBuilder b, @NotNull ParsingScope scope) {
        assert scope != TOP_LEVEL;
        Stack<ParsingScope> stack = getScopeStack(b);
        if (stack == null) {
            stack = new Stack<>();
            b.putUserData(KEY, stack);
        }
        stack.push(scope);
    }

    private static Stack<ParsingScope> getScopeStack(@NotNull PsiBuilder b) {
        return b.getUserData(KEY);
    }
}
