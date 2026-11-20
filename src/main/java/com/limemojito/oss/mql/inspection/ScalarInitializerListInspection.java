/*
 * Copyright (c) 2026.  RIGGWIRE Trading Systems.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * A single number, string or other scalar declared with a {@code {...}} list of several values:
 * {@code int x = {1, 2};}. MetaEditor rejects it with error 186 "too many initializers" (or 187
 * "'{' - constant expected" at global scope). Arrays, structs, {@code vector}, {@code matrix} and
 * {@code complex} take such lists and aren't checked, nor are pointers and references.
 */
public class ScalarInitializerListInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "too many initializers: a single value can't take a list";
    private static final TokenSet SCALARS = TokenSet.create(MQL4Elements.INT_KEYWORD, MQL4Elements.UINT_KEYWORD,
            MQL4Elements.LONG_KEYWORD, MQL4Elements.ULONG_KEYWORD, MQL4Elements.DOUBLE_KEYWORD, MQL4Elements.FLOAT_KEYWORD,
            MQL4Elements.SHORT_KEYWORD, MQL4Elements.USHORT_KEYWORD, MQL4Elements.CHAR_KEYWORD, MQL4Elements.UCHAR_KEYWORD,
            MQL4Elements.BOOL_KEYWORD, MQL4Elements.DATETIME_KEYWORD, MQL4Elements.COLOR_KEYWORD, MQL4Elements.STRING_KEYWORD);
    /** What may come before the type: {@code input}, {@code static}, {@code const} ... */
    private static final TokenSet MODIFIERS = TokenSet.orSet(MQL4TokenSets.MEMORY_CLASSES, TokenSet.create(MQL4Elements.CONST_KEYWORD));

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        StatementAst.forEachDescendant(file.getNode(), TokenSet.create(MQL4Elements.VAR_DECLARATION_STATEMENT), stmt -> {
            if (!isScalarDeclaration(stmt)) return;
            StatementAst.forEachDescendant(stmt, TokenSet.create(MQL4Elements.VAR_DEFINITION), def -> {
                ASTNode brace = listInitializer(def);
                if (brace != null && brace.getPsi() != null) {
                    problems.add(createProblem(manager, brace.getPsi(), MESSAGE, isOnTheFly));
                }
            });
        });
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** {@code [input|static|const ...] <scalar keyword> <names>}: no pointer, reference or class type. */
    private static boolean isScalarDeclaration(@NotNull ASTNode stmt) {
        boolean type = false;
        for (ASTNode n = stmt.getFirstChildNode(); n != null; n = n.getTreeNext()) {
            IElementType t = n.getElementType();
            if (StatementAst.isTrivia(n) || (!type && MODIFIERS.contains(t))) continue;
            if (!type) {
                if (!SCALARS.contains(t)) return false;
                type = true;
                continue;
            }
            return t == MQL4Elements.VAR_DEFINITION_LIST; // '*' or '&' here would be a pointer or reference
        }
        return false;
    }

    /** The {@code {} of a {@code name = {a, b, ...}} initializer with two or more values, for a name that isn't an array. */
    @Nullable
    private static ASTNode listInitializer(@NotNull ASTNode def) {
        ASTNode last = def.getLastChildNode();
        while (last != null && StatementAst.isTrivia(last)) last = last.getTreePrev();
        if (last == null || last.getElementType() != MQL4Elements.EQ || def.findChildByType(MQL4Elements.BRACKETS_BLOCK) != null
                || def.findChildByType(MQL4Elements.L_SQUARE_BRACKET) != null) {
            return null;
        }
        ASTNode brace = def.getTreeNext();
        while (brace != null && StatementAst.isTrivia(brace)) brace = brace.getTreeNext();
        if (brace == null && def.getTreeParent() != null && def.getTreeParent().getElementType() == MQL4Elements.VAR_DEFINITION_LIST) {
            brace = def.getTreeParent().getTreeNext(); // the last name's initializer follows the list
            while (brace != null && StatementAst.isTrivia(brace)) brace = brace.getTreeNext();
        }
        if (brace == null || brace.getElementType() != MQL4Elements.L_CURLY_BRACKET) return null;
        int depth = 0;
        for (ASTNode n = brace; n != null; n = n.getTreeNext()) {
            IElementType t = n.getElementType();
            if (t == MQL4Elements.L_CURLY_BRACKET) depth++;
            else if (t == MQL4Elements.R_CURLY_BRACKET && --depth == 0) return null;
            else if (t == MQL4Elements.COMMA && depth == 1) return brace;
            else if (t == MQL4Elements.SEMICOLON) return null;
        }
        return null;
    }
}
