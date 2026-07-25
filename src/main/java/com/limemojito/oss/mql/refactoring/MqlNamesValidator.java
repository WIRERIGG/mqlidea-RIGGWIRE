/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.refactoring;

import com.intellij.lang.refactoring.NamesValidator;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.doc.DocEntry;
import com.limemojito.oss.mql.doc.DocEntryType;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.Set;
import java.util.regex.Pattern;

/**
 * Backs rename/introduce-variable validation: is a proposed name a reserved MQL keyword, and does
 * it look like a legal identifier. Reuses the bundled {@code mql4-keywords.json} catalog (already
 * loaded by {@link MQL4DocumentationProvider} for completion/quick-doc) as the canonical keyword
 * list rather than hand-duplicating the lexer's keyword tokens -- that catalog already carries the
 * lexed *text* of every reserved word ("if", "for", "class", "int", ...), which is what this class
 * needs to compare a candidate name against (the lexer's {@code IElementType} constants only carry
 * token identity, not text).
 */
public class MqlNamesValidator implements NamesValidator {

    private static final Pattern IDENTIFIER_PATTERN = Pattern.compile("^[A-Za-z_][A-Za-z0-9_]*$");

    private static volatile Set<String> keywordTexts;

    @Override
    public boolean isKeyword(@NotNull String name, @Nullable Project project) {
        return keywords().contains(name);
    }

    @Override
    public boolean isIdentifier(@NotNull String name, @Nullable Project project) {
        return IDENTIFIER_PATTERN.matcher(name).matches() && !isKeyword(name, project);
    }

    @NotNull
    private static Set<String> keywords() {
        Set<String> cached = keywordTexts;
        if (cached != null) {
            return cached;
        }
        Set<String> built = new HashSet<>();
        for (DocEntry entry : MQL4DocumentationProvider.getEntries()) {
            if (entry.type == DocEntryType.Keyword) {
                built.add(entry.text);
            }
        }
        keywordTexts = built;
        return built;
    }
}
