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
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;

public class PublicDataMemberInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' has public data members — consider using getter/setter methods for encapsulation";

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            boolean inPublicSection = false;
            boolean hasPublicData = false;
            ASTNode child = innerBlock.getFirstChildNode();
            while (child != null) {
                if (child.getElementType() == MQL4Elements.PUBLIC_KEYWORD) {
                    inPublicSection = true;
                } else if (child.getElementType() == MQL4Elements.PRIVATE_KEYWORD
                        || child.getElementType() == MQL4Elements.PROTECTED_KEYWORD) {
                    inPublicSection = false;
                } else if (inPublicSection
                        && child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                    hasPublicData = true;
                    break;
                }
                child = child.getTreeNext();
            }

            if (hasPublicData) {
                problems.add(createWeakWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, cls.getTypeName())));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
