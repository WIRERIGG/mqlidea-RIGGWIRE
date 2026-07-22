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

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import java.util.regex.Pattern;

public class ImmutableInputParameterInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Input parameter '%s' appears to be reassigned — input variables should be treated as immutable";
    private static final ConcurrentHashMap<String, Pattern> REASSIGN_CACHE = new ConcurrentHashMap<>();

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        List<String> inputNames = new ArrayList<>();

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == com.limemojito.oss.mql.psi.MQL4Elements.VAR_DECLARATION_STATEMENT
                    && isInputVariable(child)) {
                String name = getVariableName(child);
                if (name != null) inputNames.add(name);
            }
        }
        if (inputNames.isEmpty()) return ProblemDescriptor.EMPTY_ARRAY;

        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                String text = BracketBlockTokenWalker.stripCommentsAndStrings(body.getText());
                for (String inputName : inputNames) {
                    if (buildReassignmentPattern(inputName).matcher(text).find()) {
                        problems.add(createWarning(manager, child.getNavigationElement(),
                                String.format(MESSAGE, inputName), isOnTheFly));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * Matches a genuine reassignment of the input variable (assignment, compound assignment
     * or increment/decrement) as a whole word, without matching comparisons such as
     * {@code ==}, {@code <=}, {@code >=} or {@code !=}, and without matching the name
     * inside a longer identifier (e.g. {@code Period} inside {@code myPeriod}).
     */
    private static Pattern buildReassignmentPattern(@NotNull String inputName) {
        String name = Pattern.quote(inputName);
        return REASSIGN_CACHE.computeIfAbsent(inputName, key -> Pattern.compile(
                "\\b" + name + "\\s*(?:(?<![!<>+\\-*/%&|^=])=(?!=)|\\+=|-=|\\*=|/=|%=|&=|\\|=|\\^=|>>=|<<=|\\+\\+|--)"
                        + "|(?:\\+\\+|--)\\s*\\b" + name + "\\b"));
    }
}
