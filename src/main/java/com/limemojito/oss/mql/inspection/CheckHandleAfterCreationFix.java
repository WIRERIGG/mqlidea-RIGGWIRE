/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;

/**
 * Quick fix for {@link UncheckedHandleInspection}: after an indicator-handle creation
 * {@code handle = iMA(...);} (or {@code int handle = iMA(...);}) inserts
 * <pre>{@code if(handle == INVALID_HANDLE)
 *    Print(__FUNCTION__, ": invalid indicator handle 'handle'");}</pre>
 * {@code INVALID_HANDLE} is {@code -1}, so this is the canonical post-creation validity check. The
 * inserted body is a {@code Print} (void, always compilable), so the fix never breaks the build
 * regardless of the enclosing function's return type; the developer can replace the log with a
 * {@code return INIT_FAILED;} where appropriate. Purely mechanical text insertion after the
 * creation statement, mirroring {@link NullifyAfterDeleteFix}; only offered when the handle was
 * assigned to a named variable.
 */
final class CheckHandleAfterCreationFix implements LocalQuickFix {

    private final String handleName;

    CheckHandleAfterCreationFix(@NotNull String handleName) {
        this.handleName = handleName;
    }

    @NotNull
    @Override
    public String getName() {
        return "Add 'if(" + handleName + " == INVALID_HANDLE)' check";
    }

    @NotNull
    @Override
    public String getFamilyName() {
        return "Check indicator handle after creation";
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        if (element == null || !element.isValid()) return;
        ASTNode callId = element.getNode();
        if (callId == null) return;
        ASTNode statement = StatementAst.enclosingStatement(callId);
        if (statement == null) return;
        PsiFile file = element.getContainingFile();
        if (file == null) return;
        Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
        if (doc == null) return;

        int insertOffset = statement.getTextRange().getEndOffset();
        if (insertOffset < 0 || insertOffset > doc.getTextLength()) return;
        String indent = lineIndent(doc, statement.getTextRange().getStartOffset());
        String inserted = "\n" + indent + "if(" + handleName + " == INVALID_HANDLE)\n"
                + indent + "   Print(__FUNCTION__, \": invalid indicator handle '" + handleName + "'\");";
        doc.insertString(insertOffset, inserted);
        PsiDocumentManager.getInstance(project).commitDocument(doc);
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
