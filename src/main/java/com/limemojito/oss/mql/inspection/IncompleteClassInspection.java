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

public class IncompleteClassInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' uses new/delete but lacks copy constructor or assignment operator (Rule of Three)";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            String className = cls.getTypeName();
            boolean hasConstructor = false;
            boolean hasDestructor = false;
            boolean hasCopyConstructor = false;
            boolean hasAssignmentOp = false;
            boolean usesNew = false;

            ASTNode child = innerBlock.getFirstChildNode();
            while (child != null) {
                if (child.getElementType() == MQL4Elements.FUNCTION
                        || child.getElementType() == MQL4Elements.FUNCTION_DECLARATION) {
                    PsiElement psi = child.getPsi();
                    if (psi instanceof MQL4FunctionElement funcElem) {
                        String name = funcElem.getFunctionName();
                        String sig = funcElem.getSignature();
                        if (className.equals(name)) {
                            if (sig.contains(className)) {
                                hasCopyConstructor = true;
                            } else {
                                hasConstructor = true;
                            }
                        }
                        if (("~" + className).equals(name)) hasDestructor = true;
                        if ("operator=".equals(name)) hasAssignmentOp = true;
                    }
                    ASTNode bodyBlock = child.findChildByType(MQL4Elements.BRACKETS_BLOCK);
                    if (bodyBlock != null && BracketBlockTokenWalker.containsPattern(bodyBlock, "\\bnew\\b")) {
                        usesNew = true;
                    }
                }
                child = child.getTreeNext();
            }

            if (usesNew && hasConstructor && hasDestructor && (!hasCopyConstructor || !hasAssignmentOp)) {
                problems.add(createWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, className)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
