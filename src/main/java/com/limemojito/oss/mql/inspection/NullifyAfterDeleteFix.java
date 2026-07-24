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
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Shared quick fix for {@link NullAfterDeleteInspection} and {@link DeleteWithoutNullCheckInspection}:
 * inserts {@code "<pointer> = NULL;"} on the line following a bare {@code delete <pointer>;}
 * statement. Purely mechanical — a plain text insertion right after the delete statement's
 * closing {@code ';'}, matching that statement's own line indentation. Does not touch, reparse or
 * restructure any other part of the file, so it is safe regardless of surrounding code shape.
 */
final class NullifyAfterDeleteFix implements LocalQuickFix {

    private final String pointerName;

    NullifyAfterDeleteFix(@NotNull String pointerName) {
        this.pointerName = pointerName;
    }

    @NotNull
    @Override
    public String getName() {
        return "Set '" + pointerName + " = NULL' after delete";
    }

    @NotNull
    @Override
    public String getFamilyName() {
        return "Set pointer to NULL after delete";
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        if (element == null || !element.isValid()) {
            return;
        }
        ASTNode anchorNode = element.getNode();
        if (anchorNode == null) {
            return;
        }
        ASTNode statement = enclosingExpressionStatement(anchorNode);
        if (statement == null) {
            return;
        }
        PsiFile file = element.getContainingFile();
        if (file == null) {
            return;
        }
        Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
        if (doc == null) {
            return;
        }

        int insertOffset = statement.getTextRange().getEndOffset();
        if (insertOffset < 0 || insertOffset > doc.getTextLength()) {
            return;
        }
        String indent = lineIndent(doc, statement.getStartOffset());
        doc.insertString(insertOffset, "\n" + indent + pointerName + " = NULL;");
        PsiDocumentManager.getInstance(project).commitDocument(doc);
    }

    /** Walks up from {@code node} to the enclosing {@code EXPRESSION_STATEMENT} (the {@code delete ...;} statement), or null. */
    @Nullable
    private static ASTNode enclosingExpressionStatement(@NotNull ASTNode node) {
        for (ASTNode current = node; current != null; current = current.getTreeParent()) {
            if (current.getElementType() == MQL4Elements.EXPRESSION_STATEMENT) {
                return current;
            }
        }
        return null;
    }

    /** Leading whitespace (spaces/tabs) of the source line containing {@code offset}. */
    @NotNull
    private static String lineIndent(@NotNull Document doc, int offset) {
        int line = doc.getLineNumber(offset);
        int lineStart = doc.getLineStartOffset(line);
        CharSequence text = doc.getCharsSequence();
        int i = lineStart;
        while (i < text.length() && (text.charAt(i) == ' ' || text.charAt(i) == '\t')) {
            i++;
        }
        return text.subSequence(lineStart, i).toString();
    }
}
