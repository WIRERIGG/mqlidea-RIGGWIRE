/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.lang.ASTNode;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Scans raw text inside BRACKETS_BLOCK nodes to find function calls,
 * identifier usage, and patterns. Filters out matches inside comments
 * and string literals.
 */
public final class BracketBlockTokenWalker {

    // Static final patterns for constant regexes
    private static final Pattern ARRAY_ACCESS_PATTERN = Pattern.compile("\\w+\\s*\\[");
    private static final Pattern LOOP_PATTERN = Pattern.compile("\\b(for|while|do)\\b");
    private static final Pattern STRING_LITERAL_PATTERN = Pattern.compile("\"([^\"]*)\"");

    // Caches for dynamic name-based patterns
    private static final ConcurrentHashMap<String, Pattern> FUNC_CALL_CACHE = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Pattern> IDENTIFIER_CACHE = new ConcurrentHashMap<>();

    // Caches for arbitrary user-supplied regex patterns
    private static final ConcurrentHashMap<String, Pattern> REGEX_CACHE = new ConcurrentHashMap<>();
    private static final ConcurrentHashMap<String, Pattern> REGEX_CI_CACHE = new ConcurrentHashMap<>();

    private BracketBlockTokenWalker() {
    }

    private static Pattern getFuncCallPattern(@NotNull String funcName) {
        return FUNC_CALL_CACHE.computeIfAbsent(funcName,
                name -> Pattern.compile("\\b" + Pattern.quote(name) + "\\s*\\("));
    }

    private static Pattern getIdentifierPattern(@NotNull String name) {
        return IDENTIFIER_CACHE.computeIfAbsent(name,
                n -> Pattern.compile("\\b" + Pattern.quote(n) + "\\b"));
    }

    private static Pattern getCachedPattern(@NotNull String regex) {
        return REGEX_CACHE.computeIfAbsent(regex, Pattern::compile);
    }

    private static Pattern getCachedPatternCI(@NotNull String regex) {
        return REGEX_CI_CACHE.computeIfAbsent(regex,
                r -> Pattern.compile(r, Pattern.CASE_INSENSITIVE));
    }

    public static boolean containsFunctionCall(@Nullable ASTNode block, @NotNull String funcName) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        return getFuncCallPattern(funcName).matcher(text).find();
    }

    public static boolean containsIdentifier(@Nullable ASTNode block, @NotNull String name) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        return getIdentifierPattern(name).matcher(text).find();
    }

    public static int countFunctionCalls(@Nullable ASTNode block, @NotNull String funcName) {
        if (block == null) return 0;
        String text = stripCommentsAndStrings(block.getText());
        Matcher m = getFuncCallPattern(funcName).matcher(text);
        int count = 0;
        while (m.find()) count++;
        return count;
    }

    public static boolean containsAnyFunctionCall(@Nullable ASTNode block, @NotNull Iterable<String> funcNames) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        for (String funcName : funcNames) {
            if (getFuncCallPattern(funcName).matcher(text).find()) {
                return true;
            }
        }
        return false;
    }

    public static boolean containsPattern(@Nullable ASTNode block, @NotNull String regex) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        return getCachedPattern(regex).matcher(text).find();
    }

    public static boolean containsStringLiteralMatching(@Nullable ASTNode block, @NotNull String regex) {
        if (block == null) return false;
        String text = block.getText();
        Matcher m = STRING_LITERAL_PATTERN.matcher(text);
        Pattern p = getCachedPatternCI(regex);
        while (m.find()) {
            if (p.matcher(m.group(1)).find()) {
                return true;
            }
        }
        return false;
    }

    public static boolean containsFunctionCallInLoop(@Nullable ASTNode block, @NotNull String funcName) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        Pattern callPattern = getFuncCallPattern(funcName);
        Matcher loopMatcher = LOOP_PATTERN.matcher(text);
        while (loopMatcher.find()) {
            int loopStart = loopMatcher.start();
            int braceStart = text.indexOf('{', loopStart);
            if (braceStart < 0) continue;
            int braceEnd = findMatchingBrace(text, braceStart);
            if (braceEnd < 0) continue;
            String loopBody = text.substring(braceStart, braceEnd + 1);
            if (callPattern.matcher(loopBody).find()) {
                return true;
            }
        }
        return false;
    }

    public static boolean containsPatternInLoop(@Nullable ASTNode block, @NotNull String regex) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        Pattern targetPattern = getCachedPattern(regex);
        Matcher loopMatcher = LOOP_PATTERN.matcher(text);
        while (loopMatcher.find()) {
            int loopStart = loopMatcher.start();
            int braceStart = text.indexOf('{', loopStart);
            if (braceStart < 0) continue;
            int braceEnd = findMatchingBrace(text, braceStart);
            if (braceEnd < 0) continue;
            String loopBody = text.substring(braceStart, braceEnd + 1);
            if (targetPattern.matcher(loopBody).find()) {
                return true;
            }
        }
        return false;
    }

    public static boolean containsArrayAccess(@Nullable ASTNode block) {
        if (block == null) return false;
        String text = stripCommentsAndStrings(block.getText());
        return ARRAY_ACCESS_PATTERN.matcher(text).find();
    }

    @NotNull
    static String stripCommentsAndStrings(@NotNull String text) {
        StringBuilder sb = new StringBuilder(text.length());
        int i = 0;
        while (i < text.length()) {
            char c = text.charAt(i);
            if (c == '/' && i + 1 < text.length()) {
                char next = text.charAt(i + 1);
                if (next == '/') {
                    while (i < text.length() && text.charAt(i) != '\n') i++;
                    continue;
                } else if (next == '*') {
                    i += 2;
                    while (i + 1 < text.length() && !(text.charAt(i) == '*' && text.charAt(i + 1) == '/')) i++;
                    i += 2;
                    continue;
                }
            }
            if (c == '"') {
                i++;
                while (i < text.length()) {
                    if (text.charAt(i) == '\\') {
                        i += 2;
                        continue;
                    }
                    if (text.charAt(i) == '"') {
                        i++;
                        break;
                    }
                    i++;
                }
                sb.append("\"\"");
                continue;
            }
            if (c == '\'') {
                i++;
                while (i < text.length()) {
                    if (text.charAt(i) == '\\') {
                        i += 2;
                        continue;
                    }
                    if (text.charAt(i) == '\'') {
                        i++;
                        break;
                    }
                    i++;
                }
                sb.append("''");
                continue;
            }
            sb.append(c);
            i++;
        }
        return sb.toString();
    }

    private static int findMatchingBrace(@NotNull String text, int openPos) {
        int depth = 0;
        for (int i = openPos; i < text.length(); i++) {
            if (text.charAt(i) == '{') depth++;
            else if (text.charAt(i) == '}') {
                depth--;
                if (depth == 0) return i;
            }
        }
        return -1;
    }
}
