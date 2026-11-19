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
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

public class UnusedParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Parameter '%s' is never used in function body";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        List<PsiElement> declarations = childrenAndClassMethods(file);
        java.util.Set<String> virtualMethods = new java.util.HashSet<>(); // "Class::Method"
        for (PsiElement child : declarations) {
            if (child instanceof MQL4FunctionElement func && isVirtual(func)) {
                MQL4ClassElement owner = PsiTreeUtil.getParentOfType(func, MQL4ClassElement.class);
                if (owner != null) {
                    virtualMethods.add(owner.getName() + "::" + func.getFunctionName());
                }
            }
        }
        for (PsiElement child : declarations) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                if (isEventHandler(func)) continue;
                // a virtual method's parameters are fixed by the class hierarchy, used or not
                if (isVirtual(func) || virtualMethods.contains(qualifier(func) + "::" + func.getFunctionName())) continue;
                ASTNode body = findBracketsBlock(func);
                if (body == null) continue;
                List<ASTNode> args = getFunctionArgs(func);
                if (args.isEmpty()) continue;
                // Collect the body's identifier set once, then test each parameter against it —
                // instead of walking the whole body once per parameter.
                java.util.Set<String> usedNames = new java.util.HashSet<>(StatementAst.collectIdentifiers(body));
                addInitializerListNames(func.getNode(), body, usedNames); // C(int a) : m(a) {}
                for (ASTNode arg : args) {
                    // the argument element knows its name: not a type before it, nor a default value after it (= UINT_MAX)
                    String paramName = arg.getPsi() instanceof MQL4FunctionArgElement param ? param.getName() : null;
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

    private static boolean isVirtual(@NotNull MQL4FunctionElement func) {
        // in a class body the modifiers are the function's preceding siblings: `virtual void M(...)`
        for (ASTNode n = StatementAst.prevNonTrivia(func.getNode()); n != null
                && (n.getElementType() == MQL4Elements.VIRTUAL_KEYWORD || n.getElementType() == MQL4Elements.STATIC_KEYWORD);
             n = StatementAst.prevNonTrivia(n)) {
            if (n.getElementType() == MQL4Elements.VIRTUAL_KEYWORD) return true;
        }
        for (ASTNode n = func.getNode().getFirstChildNode(); n != null && n.getElementType() != MQL4Elements.FUNCTION_ARGS_LIST; n = n.getTreeNext()) {
            if (n.getElementType() == MQL4Elements.VIRTUAL_KEYWORD) return true;
        }
        ASTNode args = func.getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        for (ASTNode n = args == null ? null : args.getTreeNext(); n != null && n.getElementType() != MQL4Elements.BRACKETS_BLOCK; n = n.getTreeNext()) {
            if (n.getElementType() == MQL4Elements.OVERRIDE_KEYWORD) return true;
        }
        return false;
    }

    /** {@code C} for an out-of-class definition {@code void C::M(...)}, else null. */
    @Nullable
    private static String qualifier(@NotNull MQL4FunctionElement func) {
        ASTNode name = func.getNameIdentifier() == null ? null : func.getNameIdentifier().getNode();
        ASTNode colons = name == null ? null : StatementAst.prevNonTrivia(name);
        if (colons == null || colons.getElementType() != MQL4Elements.COLON_COLON) return null;
        ASTNode owner = StatementAst.prevNonTrivia(colons);
        return owner != null && owner.getElementType() == MQL4Elements.IDENTIFIER ? owner.getText() : null;
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
