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
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class MissingDestructorInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' acquires a resource (new/FileOpen/indicator handle) but has no destructor to release it";
    // A resource is acquired if the class body allocates with `new`, opens a file, or creates an
    // indicator handle. A plain value class (only scalar/value members) needs no destructor in MQL5,
    // so requiring one for every constructor was a false positive. The handle-creator names come from
    // MQL5_HANDLE_CREATORS (iMA/iRSI/iCustom/IndicatorCreate/...) — NOT the broad `i[A-Z]...(` pattern,
    // which wrongly matched value functions like iClose/iTime/iBarShift (Fable review, concern #4).
    private static final TokenSet NEW_KEYWORD = TokenSet.create(MQL4Elements.NEW_KEYWORD);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            String className = cls.getTypeName();
            boolean hasDestructor = false;

            ASTNode child = innerBlock.getFirstChildNode();
            while (child != null) {
                if (child.getElementType() == MQL4Elements.FUNCTION
                        || child.getElementType() == MQL4Elements.FUNCTION_DECLARATION) {
                    PsiElement psi = child.getPsi();
                    if (psi instanceof MQL4FunctionElement funcElem
                            && ("~" + className).equals(funcElem.getFunctionName())) {
                        hasDestructor = true;
                    }
                }
                child = child.getTreeNext();
            }

            if (hasDestructor) continue;
            boolean acquiresResource = StatementAst.hasDescendant(innerBlock, NEW_KEYWORD)
                    || StatementAst.hasCall(innerBlock, "FileOpen")
                    || StatementAst.hasAnyCall(innerBlock, MQL5_HANDLE_CREATORS);
            if (acquiresResource) {
                problems.add(createWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, className)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
