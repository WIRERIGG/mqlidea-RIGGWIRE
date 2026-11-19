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
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class UnusedParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Parameter '%s' is never used in function body";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                if (isEventHandler(func)) continue;
                ASTNode body = findBracketsBlock(func);
                if (body == null) continue;
                List<ASTNode> args = getFunctionArgs(func);
                if (args.isEmpty()) continue;
                // Collect the body's identifier set once, then test each parameter against it —
                // instead of walking the whole body once per parameter.
                java.util.Set<String> usedNames = new java.util.HashSet<>(StatementAst.collectIdentifiers(body));
                addInitializerListNames(func.getNode(), body, usedNames); // C(int a) : m(a) {}
                for (ASTNode arg : args) {
                    ASTNode idNode = arg.findChildByType(MQL4Elements.IDENTIFIER);
                    if (idNode == null) continue;
                    // The last IDENTIFIER in a FUNCTION_ARG is the parameter name;
                    // earlier IDENTIFIERs may be the type name. Walk to find the last one.
                    ASTNode lastId = idNode;
                    ASTNode sibling = idNode.getTreeNext();
                    while (sibling != null) {
                        if (sibling.getElementType() == MQL4Elements.IDENTIFIER) {
                            lastId = sibling;
                        }
                        sibling = sibling.getTreeNext();
                    }
                    String paramName = lastId.getText();
                    if (paramName == null || paramName.isEmpty()) continue;
                    if (!usedNames.contains(paramName)) {
                        problems.add(createWeakWarning(manager, arg.getPsi(),
                                String.format(MESSAGE, paramName)));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** Identifiers between the parameter list and the body: a constructor's initializer list. */
    private static void addInitializerListNames(@NotNull ASTNode function, @NotNull ASTNode body, @NotNull java.util.Set<String> names) {
        ASTNode args = function.findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        for (ASTNode n = args == null ? null : args.getTreeNext(); n != null && n != body; n = n.getTreeNext()) {
            if (n.getElementType() == MQL4Elements.IDENTIFIER) {
                names.add(n.getText());
            } else if (n.getFirstChildNode() != null) {
                names.addAll(StatementAst.collectIdentifiers(n));
            }
        }
    }
}
