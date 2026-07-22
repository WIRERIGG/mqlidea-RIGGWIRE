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
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class LazyEvaluationMissInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Indicator value computed before conditional check — consider lazy evaluation";
    private static final Set<String> INDICATOR_FUNCS = Set.of("CopyBuffer", "CopyRates", "iCustom");
    private static final Pattern IF_KEYWORD_PATTERN = Pattern.compile("\\bif\\b");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func
                    && !func.isDeclaration()
                    && "OnTick".equals(func.getFunctionName())) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                for (String funcName : INDICATOR_FUNCS) {
                    int callPos = text.indexOf(funcName + "(");
                    if (callPos < 0) continue;
                    Matcher ifMatcher = IF_KEYWORD_PATTERN.matcher(text);
                    if (ifMatcher.find(callPos)) {
                        problems.add(createWeakWarning(manager, child.getNavigationElement(), MESSAGE, isOnTheFly));
                        break;
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
