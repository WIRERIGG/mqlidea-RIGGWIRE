/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.MqlBuiltinFunctions;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import com.limemojito.oss.mql.reference.MqlVisibleNames;
import org.jetbrains.annotations.NotNull;

import java.util.List;

/**
 * A global call ({@code Foo(...)}) to a name that is no built-in and is declared nowhere the file
 * can see (see {@link MqlVisibleNames}). That is MetaEditor's error 256, "undeclared identifier".
 * In an MQL5 file a call to an MQL4-only function ({@code OrderLots()}, {@code TimeHour()}) is the
 * same error, since MQL5 doesn't have it.
 *
 * <p>Skipped: files with an {@code #include} that doesn't resolve, member and scoped calls,
 * {@code #define} and {@code #import} bodies (see {@link UndeclaredNames}).</p>
 */
public class UndefinedFunctionCallInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (UndeclaredNames.hasUnresolvedInclude(file)) {
            return ProblemDescriptor.EMPTY_ARRAY;
        }
        boolean mql5 = MqlDialect.isMql5(file);
        List<ProblemDescriptor> problems = new SmartList<>();
        UndeclaredNames.forEachIdentifier(file, identifier -> {
            String message = problem(identifier, mql5);
            if (message != null) {
                problems.add(createProblem(manager, identifier.getPsi(), message, isOnTheFly));
            }
        });
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static String problem(@NotNull ASTNode identifier, boolean mql5) {
        if (!StatementAst.isCallIdentifier(identifier) || UndeclaredNames.isDeclarationName(identifier)) {
            return null;
        }
        String name = identifier.getText();
        boolean mql4Only = mql5 && MqlBuiltinFunctions.isMql4Only(name);
        if (!mql4Only && UndeclaredNames.isBuiltin(name)) {
            return null;
        }
        PsiElement psi = identifier.getPsi();
        if (!MqlResolveUtil.resolve(psi, name).isEmpty() || MqlVisibleNames.isDeclared(name, psi.getContainingFile())) {
            return null;
        }
        return "'" + name + "' - undeclared identifier" + (mql4Only ? " (an MQL4 function, not in MQL5)" : "");
    }
}
