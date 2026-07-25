/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.refactoring;

import com.intellij.openapi.actionSystem.DataContext;
import com.intellij.openapi.command.WriteCommandAction;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.editor.SelectionModel;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

/**
 * Phase 6b (REVAMP_PLAN.md): a conservative "Extract Variable" ({@code Ctrl+Alt+V}). Given a
 * selected expression inside a statement, it introduces a {@code <type> name = <expr>;} declaration
 * on the line above and replaces the selected occurrence with {@code name}. Complements the
 * MagicNumber inspection (pull a literal like {@code 20*Point} into a named constant).
 *
 * <p>Deliberately minimal: it operates on the exact selected text only (no occurrence search), and
 * infers a plausible type token (string / int / double) that the user can adjust -- MQL has no
 * {@code auto}. If nothing is selected it does nothing (real MQL introduce-variable would prompt).</p>
 */
public class MqlIntroduceVariableHandler implements com.intellij.refactoring.RefactoringActionHandler {

    /** Default name for the introduced variable (kept fixed so the action is testable head-less). */
    public static final String DEFAULT_NAME = "extracted";

    @Override
    public void invoke(@NotNull Project project, @NotNull Editor editor, @NotNull PsiFile file, DataContext dataContext) {
        SelectionModel selection = editor.getSelectionModel();
        if (!selection.hasSelection()) {
            return;
        }
        int start = selection.getSelectionStart();
        int end = selection.getSelectionEnd();
        if (end <= start) {
            return;
        }
        Document document = editor.getDocument();
        String exprText = document.getText().substring(start, end).trim();
        if (exprText.isEmpty()) {
            return;
        }
        String name = DEFAULT_NAME;
        String declaration = inferTypeToken(exprText) + " " + name + " = " + exprText + ";";

        int line = document.getLineNumber(start);
        int lineStart = document.getLineStartOffset(line);
        String indent = leadingWhitespace(document.getText().substring(lineStart, start));

        WriteCommandAction.writeCommandAction(project, file)
                .withName("Extract Variable")
                .run(() -> {
                    // Replace the (higher-offset) selection first so the (lower-offset) insertion
                    // below does not shift the range we are replacing.
                    document.replaceString(start, end, name);
                    document.insertString(lineStart, indent + declaration + "\n");
                    PsiDocumentManager.getInstance(project).commitDocument(document);
                });
    }

    @Override
    public void invoke(@NotNull Project project, PsiElement @NotNull [] elements, DataContext dataContext) {
        // Not invoked from the element list -- introduce-variable is an editor/selection refactoring.
    }

    /** The whitespace prefix of {@code text} (indentation of the statement's line). */
    @NotNull
    private static String leadingWhitespace(@NotNull String text) {
        int i = 0;
        while (i < text.length() && (text.charAt(i) == ' ' || text.charAt(i) == '\t')) {
            i++;
        }
        return text.substring(0, i);
    }

    /**
     * A plausible declared type for {@code expr}: {@code string} if it contains a string literal,
     * {@code int} for a bare integer literal, otherwise {@code double} (the safe default for
     * arithmetic / point maths like {@code 20*Point}). The user can adjust it afterwards.
     */
    @NotNull
    public static String inferTypeToken(@Nullable String expr) {
        if (expr == null || expr.isEmpty()) {
            return "double";
        }
        if (expr.indexOf('"') >= 0 || expr.indexOf('\'') >= 0) {
            return "string";
        }
        if (expr.matches("[+-]?\\d+")) {
            return "int";
        }
        return "double";
    }
}
