/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.findusages;

import com.intellij.lang.HelpID;
import com.intellij.lang.cacheBuilder.DefaultWordsScanner;
import com.intellij.lang.cacheBuilder.WordsScanner;
import com.intellij.lang.findUsages.FindUsagesProvider;
import com.intellij.lexer.FlexAdapter;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiNamedElement;
import com.intellij.psi.tree.TokenSet;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;
import com.limemojito.oss.mql.MQL4Lexer;
import com.limemojito.oss.mql.parser.MQL4ParserDefinition;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

/**
 * Find-usages support (Phase 4, REVAMP_PLAN.md #3b) -- word-index scanning over the plugin's own
 * lexer, so {@code ReferencesSearch}/"Find Usages" can locate candidate identifier occurrences
 * across the project without a full parse of every file.
 */
public class MqlFindUsagesProvider implements FindUsagesProvider {

    @Nullable
    @Override
    public WordsScanner getWordsScanner() {
        return new DefaultWordsScanner(new FlexAdapter(new MQL4Lexer(null)),
                TokenSet.create(MQL4Elements.IDENTIFIER),
                MQL4ParserDefinition.COMMENTS,
                TokenSet.create(MQL4Elements.STRING_LITERAL, MQL4Elements.INTEGER_LITERAL, MQL4Elements.DOUBLE_LITERAL));
    }

    @Override
    public boolean canFindUsagesFor(@NotNull PsiElement psiElement) {
        return psiElement instanceof PsiNamedElement;
    }

    @Nullable
    @Override
    public String getHelpId(@NotNull PsiElement psiElement) {
        return HelpID.FIND_OTHER_USAGES;
    }

    @NotNull
    @Override
    public String getType(@NotNull PsiElement element) {
        if (element instanceof MQL4FunctionElement) {
            return "function";
        }
        if (element instanceof MQL4ClassElement) {
            return "class";
        }
        if (element instanceof MQL4EnumElement) {
            return "enum";
        }
        if (element instanceof MQL4EnumFieldElement) {
            return "enum constant";
        }
        if (element instanceof MQL4FunctionArgElement) {
            return "parameter";
        }
        if (element instanceof MQL4VarDefinitionElement) {
            return "variable";
        }
        return "";
    }

    @NotNull
    @Override
    public String getDescriptiveName(@NotNull PsiElement element) {
        if (element instanceof PsiNamedElement named) {
            String name = named.getName();
            return name == null ? "" : name;
        }
        return "";
    }

    @NotNull
    @Override
    public String getNodeText(@NotNull PsiElement element, boolean useFullName) {
        return getDescriptiveName(element);
    }
}
