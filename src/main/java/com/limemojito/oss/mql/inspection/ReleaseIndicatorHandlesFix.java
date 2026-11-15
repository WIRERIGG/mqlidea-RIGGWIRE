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
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;

/**
 * Releases the given global indicator handles in {@code OnDeinit}: appended to its body, or in a
 * new {@code OnDeinit} at the end of the file when there is none. Each release is guarded by
 * {@code INVALID_HANDLE}, since a creation can fail.
 */
final class ReleaseIndicatorHandlesFix implements LocalQuickFix {

    private final List<String> handles;

    ReleaseIndicatorHandlesFix(@NotNull List<String> handles) {
        this.handles = List.copyOf(handles);
    }

    @NotNull
    @Override
    public String getName() {
        return handles.size() == 1 ? "Release '" + handles.get(0) + "' in OnDeinit" : "Release " + handles.size() + " indicator handles in OnDeinit";
    }

    @NotNull
    @Override
    public String getFamilyName() {
        return "Release indicator handles in OnDeinit";
    }

    @NotNull
    String releases(@NotNull String indent) {
        StringBuilder out = new StringBuilder();
        for (String h : handles) {
            out.append(indent).append("if(").append(h).append(" != INVALID_HANDLE)\n")
                    .append(indent).append("   IndicatorRelease(").append(h).append(");\n");
        }
        return out.toString();
    }

    @NotNull
    String newOnDeinit() {
        return "\nvoid OnDeinit(const int reason)\n  {\n" + releases("   ") + "  }\n";
    }

    @Override
    public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        PsiFile file = element == null ? null : element.getContainingFile();
        if (file == null) return;
        Document doc = PsiDocumentManager.getInstance(project).getDocument(file);
        if (doc == null) return;
        ASTNode close = closingBrace(element);
        if (close != null) {
            int at = close.getStartOffset();
            int lineStart = doc.getLineStartOffset(doc.getLineNumber(at));
            boolean ownLine = doc.getText(new com.intellij.openapi.util.TextRange(lineStart, at)).isBlank();
            doc.insertString(ownLine ? lineStart : at, (ownLine ? "" : "\n") + releases("   "));
        } else {
            doc.insertString(doc.getTextLength(), newOnDeinit());
        }
        PsiDocumentManager.getInstance(project).commitDocument(doc);
    }

    /** The {@code }} of the OnDeinit body when {@code element} is (inside) OnDeinit, else null. */
    @Nullable
    private static ASTNode closingBrace(@NotNull PsiElement element) {
        MQL4FunctionElement function = com.intellij.psi.util.PsiTreeUtil.getParentOfType(element, MQL4FunctionElement.class, false);
        if (function == null || !"OnDeinit".equals(function.getName())) return null;
        ASTNode body = function.getNode().findChildByType(com.limemojito.oss.mql.psi.MQL4Elements.BRACKETS_BLOCK);
        ASTNode last = body == null ? null : body.getLastChildNode();
        return last != null && "}".equals(last.getText()) ? last : null;
    }

    @NotNull
    @Override
    public IntentionPreviewInfo generatePreview(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
        PsiElement element = descriptor.getPsiElement();
        if (element == null) return IntentionPreviewInfo.EMPTY;
        return closingBrace(element) != null
                ? new IntentionPreviewInfo.CustomDiff(MQL4FileType.INSTANCE, "  }", releases("   ") + "  }")
                : new IntentionPreviewInfo.CustomDiff(MQL4FileType.INSTANCE, "", newOnDeinit());
    }
}
