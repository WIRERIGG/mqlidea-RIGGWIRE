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
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import com.intellij.psi.tree.TokenSet;
import com.limemojito.oss.mql.psi.MQL4Elements;
import java.util.List;

public class StackOverflowRiskInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Function '%s()' appears to call itself recursively without depth limit";

    private static final TokenSet RETURNS = TokenSet.create(MQL4Elements.RETURN_STATEMENT);

    /**
     * True when a {@code return} ends the recursion before {@code call} runs: a {@code return} under
     * an {@code if} that ends before the call ({@code if(n<=1) return 1; return n*Fact(n-1);}), or a
     * conditional {@code ?:} ahead of the call in its own {@code return}.
     */
    private static boolean hasBaseCase(@NotNull ASTNode body, @NotNull ASTNode call) {
        int callStart = call.getStartOffset();
        boolean[] found = {false};
        StatementAst.forEachDescendant(body, RETURNS, ret -> {
            if (found[0]) {
                return;
            }
            if (ret.getTextRange().getEndOffset() <= callStart && StatementAst.isNestedInIfStatement(ret, body)) {
                found[0] = true;
            } else if (ret.getTextRange().contains(callStart)) {
                found[0] = hasQuestionBefore(ret, callStart);
            }
        });
        return found[0];
    }

    private static boolean hasQuestionBefore(@NotNull ASTNode node, int offset) {
        for (ASTNode child = node.getFirstChildNode(); child != null && child.getStartOffset() < offset; child = child.getTreeNext()) {
            if (child.getElementType() == MQL4Elements.QUESTION || hasQuestionBefore(child, offset)) {
                return true;
            }
        }
        return false;
    }

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                String name = func.getFunctionName();
                if (name.equals(MQL4FunctionElement.UNKNOWN_NAME) || name.startsWith("~")) continue;
                ASTNode body = findBracketsBlock(child);
                ASTNode recursiveCall = StatementAst.findCall(body, name);
                if (recursiveCall != null) {
                    String text = StatementAst.heuristicText(body);
                    boolean hasDepthCheck = text.contains("depth") || text.contains("level")
                            || text.contains("maxRecurs") || text.contains("MAX_DEPTH");
                    if (!hasDepthCheck && !hasBaseCase(body, recursiveCall)) {
                        problems.add(createWarning(manager, StatementAst.anchor(recursiveCall, child.getNavigationElement()),
                                String.format(MESSAGE, name)));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
