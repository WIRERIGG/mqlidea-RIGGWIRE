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
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.Set;

/**
 * AST-based detection: an account-info call and an output call both present in the same function
 * body (structural call recognition — an {@code IDENTIFIER} directly followed by a {@code (...)}
 * args block — instead of a regex over comment/string-stripped text). Kept function-scoped
 * (matching the original intent: the account value may flow through a local variable into the
 * output call, e.g. {@code double bal = AccountBalance(); Print(bal);}), so this remains a nudge
 * rather than a precise taint check.
 */
public class AccountInfoExposureInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Account information sent to external output — potential data privacy risk";
    private static final Set<String> ACCOUNT_FUNCS = Set.of(
            "AccountInfoDouble", "AccountInfoInteger", "AccountInfoString",
            "AccountBalance", "AccountEquity", "AccountNumber", "AccountName"
    );
    private static final Set<String> OUTPUT_FUNCS = Set.of("Print", "PrintFormat", "WebRequest", "SendFTP", "SendMail", "SendNotification");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasAnyCall(body, ACCOUNT_FUNCS) && StatementAst.hasAnyCall(body, OUTPUT_FUNCS)) {
                    problems.add(createWarning(manager, child.getNavigationElement(), MESSAGE));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
