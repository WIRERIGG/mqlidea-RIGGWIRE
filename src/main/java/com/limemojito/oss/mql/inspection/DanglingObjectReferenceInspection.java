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
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class DanglingObjectReferenceInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Object deleted then same identifier used afterwards — potential dangling reference";
    private static final Pattern DELETE_PATTERN = Pattern.compile("\\bdelete\\s+(\\w+)");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                Matcher m = DELETE_PATTERN.matcher(text);
                while (m.find()) {
                    String deletedVar = m.group(1);
                    int afterDelete = m.end();
                    String remaining = text.substring(afterDelete);
                    if (Pattern.compile("\\b" + Pattern.quote(deletedVar) + "\\b").matcher(remaining).find()) {
                        String afterDeleteTrimmed = remaining.trim();
                        if (!afterDeleteTrimmed.startsWith(deletedVar + " = NULL")
                                && !afterDeleteTrimmed.startsWith(deletedVar + "=NULL")) {
                            problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE));
                            break;
                        }
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
