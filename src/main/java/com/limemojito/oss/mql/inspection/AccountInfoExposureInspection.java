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
 * <p>
 * {@code OUTPUT_FUNCS} is restricted to functions that actually leave the machine. {@code Print}/
 * {@code PrintFormat}/{@code Comment}/{@code Alert} only write to the local terminal log/UI — never
 * a privacy risk — so including them flagged the ordinary, safe idiom
 * {@code double bal = AccountBalance(); Print(bal);} on every EA that logs its own balance.
 * {@code SendMail}/{@code SendNotification} go to the owner's own configured mailbox and device, so
 * they get a weak warning; {@code WebRequest}/{@code SendFTP} keep the warning.
 */
public class AccountInfoExposureInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Account information sent to external output — potential data privacy risk";
    private static final Set<String> ACCOUNT_FUNCS = Set.of(
            "AccountInfoDouble", "AccountInfoInteger", "AccountInfoString",
            "AccountBalance", "AccountEquity", "AccountNumber", "AccountName"
    );
    private static final String OWNER_MESSAGE = "Account information sent by mail or push notification — check it is meant to leave the terminal";
    /** Destinations someone else runs: a web server or an FTP server. */
    private static final Set<String> THIRD_PARTY_OUTPUT_FUNCS = Set.of("WebRequest", "SendFTP");
    /** The terminal owner's own mailbox and phone, set up in the terminal options: lower risk, so a weak warning. */
    private static final Set<String> OWNER_OUTPUT_FUNCS = Set.of("SendMail", "SendNotification");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (StatementAst.hasAnyCall(body, ACCOUNT_FUNCS)) {
                    // Anchor at the output call — that is where the account data actually leaves the EA.
                    ASTNode thirdParty = StatementAst.findAnyCall(body, THIRD_PARTY_OUTPUT_FUNCS);
                    if (thirdParty != null) {
                        problems.add(createWarning(manager, StatementAst.anchor(thirdParty, child.getNavigationElement()), MESSAGE));
                    } else {
                        ASTNode ownerOutput = StatementAst.findAnyCall(body, OWNER_OUTPUT_FUNCS);
                        if (ownerOutput != null) {
                            problems.add(createWeakWarning(manager, StatementAst.anchor(ownerOutput, child.getNavigationElement()), OWNER_MESSAGE));
                        }
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
