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

import java.util.List;
import java.util.Set;

/**
 * AST-based detection of ignored return values: an {@code EXPRESSION_STATEMENT} that is a bare
 * call to an important function — the statement starts with the function's identifier followed
 * by its {@code (...)} args block and carries no top-level assignment operator. Calls whose
 * result is captured ({@code int h = FileOpen(...)}), returned, or used inside a condition are
 * different statement shapes and are never flagged, eliminating the old line-based false
 * positives.
 */
public class ReturnValueIgnoredInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Important function return value ignored — check return values of ArrayResize/FileOpen/ObjectCreate/etc. to detect failures";

    private static final Set<String> IMPORTANT_FUNCTIONS = Set.of(
            "ArrayResize", "ArrayCopy", "ArraySort",
            "StringFind", "StringReplace",
            "FileOpen", "FileCopy", "FileMove",
            "GlobalVariableSet",
            "ChartSetInteger", "ChartSetDouble", "ChartSetString",
            "ObjectCreate", "ObjectDelete",
            "EventSetTimer", "EventSetMillisecondTimer"
    );

    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, EXPRESSION_STATEMENTS, stmt -> {
                    String funcName = bareCallName(stmt);
                    if (funcName == null || !IMPORTANT_FUNCTIONS.contains(funcName)) return;
                    PsiElement psi = stmt.getPsi();
                    if (psi != null && psi.isValid()) {
                        problems.add(createWarning(manager, psi, MESSAGE));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * If the expression statement is a bare call — first meaningful child is an identifier
     * immediately followed by its {@code (...)} args block, with no top-level assignment
     * operator — returns the called function's name, otherwise null.
     */
    static String bareCallName(@NotNull ASTNode expressionStatement) {
        ASTNode identifier = null;
        boolean argsFollowIdentifier = false;
        for (ASTNode child = expressionStatement.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (StatementAst.isTrivia(child)) continue;
            if (StatementAst.ASSIGNMENT_OPERATORS.contains(child.getElementType())) {
                return null; // result is assigned somewhere at statement level
            }
            if (identifier == null) {
                if (child.getElementType() != MQL4Elements.IDENTIFIER) {
                    return null; // statement does not start with a plain identifier
                }
                identifier = child;
            } else if (!argsFollowIdentifier) {
                if (!StatementAst.isParenBlock(child)) {
                    return null; // identifier is not directly called (e.g. member access, array)
                }
                argsFollowIdentifier = true;
            }
        }
        return (identifier != null && argsFollowIdentifier) ? identifier.getText() : null;
    }
}
