/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiComment;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiWhiteSpace;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * AST-based detection of heap allocation inside a loop: a {@code NEW_KEYWORD} token anywhere in
 * the body subtree of a {@code FOR/WHILE/DO_STATEMENT}. The old text heuristic matched
 * {@code new} against the next {@code {...}} region after any loop keyword, so a brace-less loop
 * followed by an unrelated block containing {@code new} was a false positive; an allocation
 * outside every loop body is no longer flagged.
 * <p>
 * A {@code new} whose object is handed to something that keeps it is how MQL5 builds collections,
 * so it is not reported: an indexed slot ({@code items[i] = new CItem(i)}), a member
 * ({@code obj.m_child = new CItem()}), a call argument ({@code list.Add(new CItem(i))}) or a
 * {@code return}. A {@code new} stored in a plain variable still is.
 */
public class NewKeywordInLoopInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Heap allocation ('new') inside loop — causes repeated allocation overhead and potential memory leaks";

    private static final TokenSet NEW_KEYWORD = TokenSet.create(MQL4Elements.NEW_KEYWORD);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, StatementAst.LOOP_STATEMENTS, loop -> {
                    ASTNode loopBody = StatementAst.findLoopBody(loop);
                    if (loopBody == null || !hasUnownedNew(loopBody)) return;
                    PsiElement psi = loop.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean hasUnownedNew(@NotNull ASTNode loopBody) {
        boolean[] found = {false};
        StatementAst.forEachDescendant(loopBody, NEW_KEYWORD, newKeyword -> {
            if (!found[0] && !isOwnedAllocation(newKeyword)) found[0] = true;
        });
        return found[0];
    }

    /** True when the object created by {@code newKeyword} is stored somewhere that keeps it. */
    private static boolean isOwnedAllocation(@NotNull ASTNode newKeyword) {
        PsiElement prev = prevCodeLeaf(newKeyword.getPsi());
        if (prev == null) return false;
        IElementType t = prev.getNode().getElementType();
        if (t == MQL4Elements.L_ROUND_BRACKET || t == MQL4Elements.COMMA || t == MQL4Elements.RETURN_KEYWORD) {
            return true; // Add(new CItem(i)), f(a, new B), return new CItem()
        }
        if (t != MQL4Elements.EQ) return false;
        // walk back over the assignment target: x  |  a.b.c  |  arr[i]
        PsiElement target = prevCodeLeaf(prev);
        if (target != null && target.getNode().getElementType() == MQL4Elements.R_SQUARE_BRACKET) {
            return true; // items[i] = new CItem(i)
        }
        if (target == null || target.getNode().getElementType() != MQL4Elements.IDENTIFIER) return false;
        PsiElement before = prevCodeLeaf(target);
        return before != null && before.getNode().getElementType() == MQL4Elements.DOT; // obj.m_child = new CItem()
    }

    @Nullable
    private static PsiElement prevCodeLeaf(@NotNull PsiElement element) {
        PsiElement leaf = PsiTreeUtil.prevLeaf(element);
        while (leaf instanceof PsiWhiteSpace || leaf instanceof PsiComment) {
            leaf = PsiTreeUtil.prevLeaf(leaf);
        }
        return leaf;
    }
}
