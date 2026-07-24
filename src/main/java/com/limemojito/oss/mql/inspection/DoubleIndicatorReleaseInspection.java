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

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/**
 * AST-based detection: every {@code IndicatorRelease(...)} call's args-block text, scoped exactly
 * to that call (see {@link StatementAst#callArgsBlock}) rather than a whole-function regex — so
 * distinct array elements ({@code handles[0]} vs {@code handles[1]}) or distinct factory calls are
 * still correctly treated as different handles (Fable review, concern #3), and nested/adjacent
 * unrelated parens can no longer confuse which call an argument belongs to.
 * <p>
 * Branch-aware (Fable FP): two releases of the same handle are only a genuine double-free if they
 * can both execute on the same run. The partial-failure cleanup idiom
 * (RIGGWIRE_DataCapture.mq5:105-107) releases the SAME earlier handle from several mutually
 * exclusive {@code if(... == INVALID_HANDLE) { IndicatorRelease(h); ...; return INIT_FAILED; }}
 * guards — at most one of those branches ever runs. Two release calls are grouped by their
 * {@link StatementAst#nearestEnclosingIfStatement} within the function body; only calls that share
 * the same branch (including both being unconditional / top-level) are flagged as a duplicate.
 */
public class DoubleIndicatorReleaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Handle '%s' is released by IndicatorRelease() more than once — potential double-free";
    private static final Set<String> INDICATOR_RELEASE = Set.of("IndicatorRelease");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (isMql4Source(file)) return ProblemDescriptor.EMPTY_ARRAY;
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                // Releasing two DIFFERENT handles (the normal multi-indicator OnDeinit pattern) is
                // correct; only the SAME handle variable released more than once ON THE SAME
                // execution path is a real double-free.
                Map<String, List<ASTNode>> branchesSeen = new LinkedHashMap<>();
                // Anchor at the actual second (duplicate) call site, not the function header.
                Map<String, ASTNode> duplicated = new LinkedHashMap<>();
                StatementAst.forEachCall(body, INDICATOR_RELEASE, callId -> {
                    ASTNode args = StatementAst.callArgsBlock(callId);
                    if (args == null) return;
                    String text = args.getText();
                    String handle = text.length() >= 2 ? text.substring(1, text.length() - 1).trim() : text.trim();
                    ASTNode branch = StatementAst.nearestEnclosingIfStatement(callId, body);
                    List<ASTNode> branches = branchesSeen.computeIfAbsent(handle, k -> new ArrayList<>());
                    boolean sameBranchSeenBefore = branches.stream().anyMatch(seen -> Objects.equals(seen, branch));
                    if (sameBranchSeenBefore) {
                        duplicated.putIfAbsent(handle, callId);
                    }
                    branches.add(branch);
                });
                for (Map.Entry<String, ASTNode> entry : duplicated.entrySet()) {
                    problems.add(createProblem(manager,
                            StatementAst.anchor(entry.getValue(), child.getNavigationElement()),
                            String.format(MESSAGE, entry.getKey())));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }
}
