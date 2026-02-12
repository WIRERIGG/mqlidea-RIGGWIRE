/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
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

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class VirtualCallInConstructorInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Virtual method called in constructor/destructor — virtual dispatch is not yet/no longer active, will call base version";

    private static final Pattern VIRTUAL_METHOD_DECL =
            Pattern.compile("\\bvirtual\\s+\\w+\\s+(\\w+)\\s*\\(");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            String className = cls.getTypeName();
            Set<String> virtualMethodNames = collectVirtualMethodNames(innerBlock);
            if (virtualMethodNames.isEmpty()) continue;

            checkConstructorsAndDestructors(innerBlock, className, virtualMethodNames, manager, cls, problems);
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    @NotNull
    private Set<String> collectVirtualMethodNames(@NotNull ASTNode innerBlock) {
        Set<String> virtualMethods = new HashSet<>();
        ASTNode child = innerBlock.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.FUNCTION
                    || child.getElementType() == MQL4Elements.FUNCTION_DECLARATION) {
                PsiElement psi = child.getPsi();
                if (psi instanceof MQL4FunctionElement funcElem) {
                    if (hasVirtualKeyword(child)) {
                        String name = funcElem.getFunctionName();
                        if (name != null && !name.startsWith("~")) {
                            virtualMethods.add(name);
                        }
                    }
                }
            }
            child = child.getTreeNext();
        }
        return virtualMethods;
    }

    private void checkConstructorsAndDestructors(@NotNull ASTNode innerBlock,
                                                  @NotNull String className,
                                                  @NotNull Set<String> virtualMethodNames,
                                                  @NotNull InspectionManager manager,
                                                  @NotNull MQL4ClassElement cls,
                                                  @NotNull List<ProblemDescriptor> problems) {
        ASTNode child = innerBlock.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.FUNCTION) {
                PsiElement psi = child.getPsi();
                if (psi instanceof MQL4FunctionElement funcElem) {
                    String name = funcElem.getFunctionName();
                    if (className.equals(name) || ("~" + className).equals(name)) {
                        ASTNode body = child.findChildByType(MQL4Elements.BRACKETS_BLOCK);
                        if (body != null && callsAnyVirtualMethod(body, virtualMethodNames)) {
                            problems.add(createWarning(manager, funcElem.getNavigationElement(), MESSAGE));
                        }
                    }
                }
            }
            child = child.getTreeNext();
        }
    }

    private boolean callsAnyVirtualMethod(@NotNull ASTNode body, @NotNull Set<String> virtualMethodNames) {
        for (String methodName : virtualMethodNames) {
            if (BracketBlockTokenWalker.containsFunctionCall(body, methodName)) {
                return true;
            }
        }
        return false;
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
