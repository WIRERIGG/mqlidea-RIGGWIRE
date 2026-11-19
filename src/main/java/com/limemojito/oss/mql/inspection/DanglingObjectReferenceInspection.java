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
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * AST-based detection: a bare {@code delete <identifier>;} ({@link StatementAst#deletedIdentifier})
 * whose identifier is referenced again afterwards — unless that reference is (or comes at/after) a
 * reassignment {@code <identifier> = <anything>;} ({@link StatementAst#findAssignmentAfter}), which
 * ends the dangling window: the delete-then-recreate idiom {@code delete obj; obj = new CFoo();}
 * assigns a fresh value, so anything from that assignment onward refers to the new object, not the
 * deleted one. The reassignment's own left-hand identifier (the write, not a use) is never counted
 * as a dangling use either. {@code delete arr[i];} (array-element delete) is excluded by construction.
 */
public class DanglingObjectReferenceInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Object deleted then same identifier used afterwards — potential dangling reference";
    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                // Anchor at the dangling use site (the identifier used after delete), not the function header.
                ASTNode[] danglingUse = {null};
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    if (danglingUse[0] != null) return;
                    ASTNode idNode = StatementAst.bareDeletedIdentifier(stmt);
                    if (idNode == null) return;
                    String name = idNode.getText();
                    int deleteEnd = stmt.getTextRange().getEndOffset();
                    ASTNode reassignEq = StatementAst.findAssignmentAfter(body, name, deleteEnd);
                    ASTNode lhsToExclude = reassignEq != null ? StatementAst.prevNonTrivia(reassignEq) : null;
                    ASTNode use = findDanglingUse(body, name, deleteEnd, lhsToExclude, stmt);
                    if (use != null && use.getStartOffset() >= reachableEnd(stmt, body)) {
                        use = null; // past a return that follows the delete: not reached from it
                    }
                    if (use != null && reassignEq != null && use.getStartOffset() >= reassignEq.getStartOffset()) {
                        use = null; // at/after the reassignment — refers to the fresh value, not dangling
                    }
                    if (use != null) {
                        danglingUse[0] = use;
                    }
                });
                if (danglingUse[0] != null) {
                    problems.add(createWarning(manager, StatementAst.anchor(danglingUse[0], child.getNavigationElement()), MESSAGE, isOnTheFly));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** True when {@code use} is in another branch of an {@code if} that holds {@code delete}: {@code if (a) delete p; else p.Use();} */
    private static boolean inOtherBranch(@NotNull ASTNode delete, @NotNull ASTNode use) {
        for (ASTNode branch = delete; branch.getTreeParent() != null; branch = branch.getTreeParent()) {
            ASTNode parent = branch.getTreeParent();
            if (parent.getElementType() == MQL4Elements.IF_STATEMENT && parent.getTextRange().contains(use.getTextRange())
                    && !branch.getTextRange().contains(use.getTextRange())) {
                return true;
            }
        }
        return false;
    }

    /**
     * End of the code the delete can reach: the end of the first {@code return} that follows it in
     * an enclosing {@code {...}} block ({@code if (!ok) { delete p; return false; } p.Use();}), or
     * the end of the function.
     */
    private static int reachableEnd(@NotNull ASTNode delete, @NotNull ASTNode body) {
        for (ASTNode node = delete; node != null && node != body; node = node.getTreeParent()) {
            ASTNode parent = node.getTreeParent();
            if (parent == null || parent.getElementType() != MQL4Elements.BRACKETS_BLOCK
                    || parent.getFirstChildNode().getElementType() != MQL4Elements.L_CURLY_BRACKET) {
                continue;
            }
            for (ASTNode next = node.getTreeNext(); next != null; next = next.getTreeNext()) {
                if (next.getElementType() == MQL4Elements.RETURN_STATEMENT) {
                    return next.getTextRange().getEndOffset();
                }
            }
        }
        return Integer.MAX_VALUE;
    }

    /**
     * First {@code IDENTIFIER} token with text {@code name} at or after {@code fromOffset} in
     * {@code root}, skipping {@code excludeNode} (the reassignment's own left-hand identifier,
     * which is a write, not a use).
     */
    @Nullable
    private static ASTNode findDanglingUse(@NotNull ASTNode root, @NotNull String name, int fromOffset, @Nullable ASTNode excludeNode,
                                           @NotNull ASTNode delete) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == MQL4Elements.IDENTIFIER && name.equals(child.getText())
                    && child.getStartOffset() >= fromOffset && child != excludeNode && !inOtherBranch(delete, child)) {
                return child;
            }
            ASTNode found = findDanglingUse(child, name, fromOffset, excludeNode, delete);
            if (found != null) return found;
        }
        return null;
    }
}
