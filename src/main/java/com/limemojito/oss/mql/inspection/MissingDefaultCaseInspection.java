/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * AST-based detection of {@code switch} statements without a {@code default} case. Each
 * {@code SWITCH_STATEMENT}'s own {@code {...}} body block is inspected for a direct
 * {@code default} label token, so a {@code default} belonging to another switch (or appearing
 * anywhere else in the function) no longer masks the problem.
 * <p>
 * Not reported: a switch whose cases cover every value of one enum, and a switch followed directly
 * by a {@code return}, which acts as the default.
 */
public class MissingDefaultCaseInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE =
            "Switch statement without 'default' case — unhandled values may cause unexpected behavior";

    private static final TokenSet SWITCH_STATEMENTS = TokenSet.create(MQL4Elements.SWITCH_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : childrenAndClassMethods(file)) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body == null) continue;
                StatementAst.forEachDescendant(body, SWITCH_STATEMENTS, switchStmt -> {
                    ASTNode switchBody = StatementAst.findCodeBlockChild(switchStmt);
                    // No body block (tolerant parse of malformed switch): nothing to judge.
                    if (switchBody == null) return;
                    if (switchBody.findChildByType(MQL4Elements.DEFAULT_KEYWORD) != null) return;
                    if (isFollowedByReturn(switchStmt) || coversWholeEnum(switchBody)) return;
                    PsiElement psi = switchStmt.getPsi();
                    if (psi != null && psi.isValid()) {
                        // WEAK_WARNING: the case labels may be plain integers or values this can't
                        // resolve, where a missing case can't be told apart from a deliberate one.
                        problems.add(createWeakWarning(manager, psi, MESSAGE, new AddDefaultCaseFix()));
                    }
                });
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** A {@code return} right after the switch already handles every value no case matched. */
    private static boolean isFollowedByReturn(@NotNull ASTNode switchStmt) {
        ASTNode next = StatementAst.nextNonTrivia(switchStmt);
        return next != null && next.getElementType() == MQL4Elements.RETURN_STATEMENT;
    }

    /**
     * True when every case label names a value of one enum and every value of that enum has a case,
     * so there is no value left for a {@code default} to handle.
     */
    private static boolean coversWholeEnum(@NotNull ASTNode switchBody) {
        MQL4EnumElement enumType = null;
        Set<PsiElement> covered = new HashSet<>();
        for (ASTNode child = switchBody.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() != MQL4Elements.CASE_KEYWORD) continue;
            ASTNode label = lastIdentifierOfLabel(child);
            if (label == null) return false;
            MQL4EnumFieldElement field = null;
            for (PsiElement target : MqlResolveUtil.resolve(label.getPsi(), label.getText())) {
                if (target instanceof MQL4EnumFieldElement f) field = f;
            }
            MQL4EnumElement owner = field == null ? null : PsiTreeUtil.getParentOfType(field, MQL4EnumElement.class);
            if (owner == null || (enumType != null && owner != enumType)) return false;
            enumType = owner;
            covered.add(field);
        }
        if (enumType == null) return false;
        Collection<MQL4EnumFieldElement> all = PsiTreeUtil.findChildrenOfType(enumType, MQL4EnumFieldElement.class);
        return !all.isEmpty() && covered.containsAll(all);
    }

    /** The value a {@code case} names: the last identifier before its {@code :} ({@code P_C} in {@code EP::P_C}). */
    @Nullable
    private static ASTNode lastIdentifierOfLabel(@NotNull ASTNode caseKeyword) {
        ASTNode label = StatementAst.nextNonTrivia(caseKeyword);
        if (label == null) return null;
        if (label.getElementType() == MQL4Elements.IDENTIFIER) return label;
        ASTNode last = null;
        for (ASTNode child = label.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            IElementType t = child.getElementType();
            if (t == MQL4Elements.IDENTIFIER) last = child;
            else if (t != MQL4Elements.COLON_COLON && !StatementAst.isTrivia(child)) return null;
        }
        return last;
    }

    private static class AddDefaultCaseFix implements LocalQuickFix {
        @NotNull
        @Override
        public String getName() {
            return "Add 'default: break;' case";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return getName();
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiElement element = descriptor.getPsiElement();
            if (element == null || !element.isValid()) return;
            PsiFile file = element.getContainingFile();
            if (file == null) return;
            Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
            if (doc == null) return;

            ASTNode switchStmt = element.getNode();
            if (switchStmt == null) return;
            ASTNode switchBody = StatementAst.findCodeBlockChild(switchStmt);
            if (switchBody == null) return;
            ASTNode closingBrace = findClosingBrace(switchBody);
            if (closingBrace == null) return;

            doc.insertString(closingBrace.getStartOffset(), "      default:\n         break;\n   ");
        }

        @Nullable
        private static ASTNode findClosingBrace(@NotNull ASTNode codeBlock) {
            // Direct child search: nested braces live inside nested statement nodes.
            for (ASTNode child = codeBlock.getLastChildNode(); child != null; child = child.getTreePrev()) {
                if (child.getElementType() == MQL4Elements.R_CURLY_BRACKET) {
                    return child;
                }
            }
            return null;
        }
    }
}
