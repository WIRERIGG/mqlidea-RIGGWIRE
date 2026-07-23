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
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * AST-based detection of switch case fall-through, scoped strictly to each
 * {@code SWITCH_STATEMENT}'s own {@code {...}} body block. {@code case}/{@code default} labels
 * are raw tokens directly inside the body; a label segment with real statements but no
 * {@code break}/{@code continue} ({@code SINGLE_WORD_STATEMENT}) or {@code RETURN_STATEMENT}
 * before the next label is flagged. Intentional empty fall-through ({@code case X: case Y:}) and
 * the final segment before the closing brace are never flagged, and — unlike the old text scan
 * over the whole function — labels of two different switches are no longer treated as one
 * sequence, nor can {@code case}/{@code break} in comments or strings misfire.
 */
public class MissingBreakInSwitchInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Possible unintended switch case fall-through — missing 'break' or 'return' statement";

    private static final TokenSet SWITCH_STATEMENTS = TokenSet.create(MQL4Elements.SWITCH_STATEMENT);

    /** Statements that end a case segment: break/continue ({@code SINGLE_WORD_STATEMENT}) or return. */
    private static final TokenSet EXIT_STATEMENTS = TokenSet.create(
            MQL4Elements.SINGLE_WORD_STATEMENT, MQL4Elements.RETURN_STATEMENT
    );

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, SWITCH_STATEMENTS, switchStmt -> {
                    ASTNode switchBody = StatementAst.findCodeBlockChild(switchStmt);
                    if (switchBody == null || !hasFallThrough(switchBody)) return;
                    PsiElement psi = switchStmt.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWeakWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * Walks the direct children of the switch body block. Label values between a
     * {@code case} keyword and its {@code ':'} are skipped, so only real statements count as
     * segment content. The last segment (before the closing brace) can fall out of the switch
     * legitimately and is never reported.
     */
    private static boolean hasFallThrough(@NotNull ASTNode switchBody) {
        boolean inSegment = false;       // a case/default label has been seen
        boolean inLabelHeader = false;   // between the label keyword and its ':'
        boolean segmentHasStatements = false;
        boolean segmentHasExit = false;
        for (ASTNode child = switchBody.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType t = child.getElementType();
            if (StatementAst.isTrivia(child)
                    || t == MQL4Elements.L_CURLY_BRACKET
                    || t == MQL4Elements.R_CURLY_BRACKET) {
                continue;
            }
            if (t == MQL4Elements.CASE_KEYWORD || t == MQL4Elements.DEFAULT_KEYWORD) {
                if (inSegment && segmentHasStatements && !segmentHasExit) {
                    return true; // previous label's statements fall into this label
                }
                inSegment = true;
                inLabelHeader = true;
                segmentHasStatements = false;
                segmentHasExit = false;
                continue;
            }
            if (inLabelHeader) {
                if (t == MQL4Elements.COLON) {
                    inLabelHeader = false;
                }
                continue; // label value tokens/expression are not segment statements
            }
            if (!inSegment) {
                continue; // stray content before the first label
            }
            segmentHasStatements = true;
            if (EXIT_STATEMENTS.contains(t) || StatementAst.hasDescendant(child, EXIT_STATEMENTS)) {
                segmentHasExit = true;
            }
        }
        return false;
    }
}
