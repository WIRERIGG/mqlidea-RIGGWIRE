/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInsight.intention.preview.IntentionPreviewInfo;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.limemojito.oss.mql.MQL4FileType;
import org.jetbrains.annotations.NotNull;

/**
 * Quick fix for the return-value checks ({@link UncheckedCopyRatesInspection},
 * {@link ArrayResizeReturnCheckInspection}) whose flagged call is a bare expression statement
 * {@code Foo(...);} — wraps it as
 * <pre>{@code if(Foo(...) < 0)
 *    Print(__FUNCTION__, ": Foo failed");}</pre>
 * The MQL5 functions this targets all return {@code -1} on failure, so {@code < 0} is the correct
 * failure test. The inserted {@code Print} is always compilable (void, no {@code return} needed),
 * so the fix can never produce non-compiling code regardless of the enclosing function's return
 * type — it turns an ignored failure into a logged, checked one that the developer can then harden.
 * Purely mechanical document-text rewrite of the single statement, mirroring
 * {@link NullifyAfterDeleteFix}; only offered when the call is a bare statement (never for an
 * assigned/declared call, which this wrap would corrupt).
 */
final class WrapCallInFailureCheckFix implements LocalQuickFix {

    private final String callName;

    WrapCallInFailureCheckFix(@NotNull String callName) {
        this.callName = callName;
    }

    @NotNull
    @Override
    public String getName() {
        return "Wrap in 'if(" + callName + "(...) < 0)' failure check";
    }

    @NotNull
    @Override
    public String getFamilyName() {
        return "Check return value for failure";
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        if (element == null || !element.isValid()) return;
        ASTNode callId = element.getNode();
        if (callId == null || !StatementAst.isBareCallStatement(callId)) return;
        ASTNode statement = StatementAst.enclosingStatement(callId);
        if (statement == null) return;
        PsiFile file = element.getContainingFile();
        if (file == null) return;
        Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
        if (doc == null) return;

        int start = statement.getTextRange().getStartOffset();
        int end = statement.getTextRange().getEndOffset();
        if (start < 0 || end > doc.getTextLength() || start >= end) return;

        String stmtText = statement.getText();
        // Strip the trailing ';' to recover the call expression.
        String expr = stmtText.endsWith(";") ? stmtText.substring(0, stmtText.length() - 1).trim() : stmtText.trim();
        String indent = lineIndent(doc, start);
        String replacement = "if(" + expr + " < 0)\n"
                + indent + "   Print(__FUNCTION__, \": " + callName + " failed\");";
        doc.replaceString(start, end, replacement);
        PsiDocumentManager.getInstance(project).commitDocument(doc);
    }

    /**
     * Alt-Enter preview. This fix edits the document via {@link Document#replaceString} rather than
     * a pure PSI mutation in the highlighted range, so the platform's default preview cannot render
     * the change. We build the before/after of the single rewritten statement explicitly as a
     * {@link IntentionPreviewInfo.CustomDiff}, which does not depend on the preview copy having a
     * committable document.
     */
    @NotNull
    @Override
    public IntentionPreviewInfo generatePreview(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        if (element == null || !element.isValid()) return IntentionPreviewInfo.EMPTY;
        ASTNode callId = element.getNode();
        if (callId == null || !StatementAst.isBareCallStatement(callId)) return IntentionPreviewInfo.EMPTY;
        ASTNode statement = StatementAst.enclosingStatement(callId);
        if (statement == null) return IntentionPreviewInfo.EMPTY;
        String original = statement.getText();
        String expr = original.endsWith(";") ? original.substring(0, original.length() - 1).trim() : original.trim();
        String modified = "if(" + expr + " < 0)\n   Print(__FUNCTION__, \": " + callName + " failed\");";
        return new IntentionPreviewInfo.CustomDiff(MQL4FileType.INSTANCE, original, modified);
    }

    @NotNull
    private static String lineIndent(@NotNull Document doc, int offset) {
        int lineStart = doc.getLineStartOffset(doc.getLineNumber(offset));
        CharSequence text = doc.getCharsSequence();
        int i = lineStart;
        while (i < text.length() && (text.charAt(i) == ' ' || text.charAt(i) == '\t')) i++;
        return text.subSequence(lineStart, i).toString();
    }
}
