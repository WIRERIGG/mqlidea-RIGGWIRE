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
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class VirtualWithoutDestructorInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' has virtual methods but no virtual destructor";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            String className = cls.getTypeName();
            boolean hasVirtualMethod = false;
            boolean hasVirtualDestructor = false;

            ASTNode child = innerBlock.getFirstChildNode();
            while (child != null) {
                if (child.getElementType() == MQL4Elements.FUNCTION
                        || child.getElementType() == MQL4Elements.FUNCTION_DECLARATION) {
                    PsiElement psi = child.getPsi();
                    if (psi instanceof MQL4FunctionElement funcElem) {
                        String name = funcElem.getFunctionName();
                        boolean isVirtual = hasVirtualKeyword(child);
                        if (isVirtual && !name.startsWith("~")) {
                            hasVirtualMethod = true;
                        }
                        if (("~" + className).equals(name) && isVirtual) {
                            hasVirtualDestructor = true;
                        }
                    }
                }
                child = child.getTreeNext();
            }

            if (hasVirtualMethod && !hasVirtualDestructor) {
                problems.add(createWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, className)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private boolean hasVirtualKeyword(@NotNull ASTNode funcNode) {
        ASTNode child = funcNode.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.VIRTUAL_KEYWORD) return true;
            if (child.getElementType() == MQL4Elements.L_ROUND_BRACKET) break;
            child = child.getTreeNext();
        }
        return false;
    }
}
