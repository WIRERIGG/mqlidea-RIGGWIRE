/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor.codecompletion;

import com.intellij.codeInsight.completion.CompletionParameters;
import com.intellij.codeInsight.completion.CompletionProvider;
import com.intellij.codeInsight.completion.CompletionResultSet;
import com.intellij.codeInsight.completion.util.ParenthesesInsertHandler;
import com.intellij.codeInsight.lookup.LookupElementBuilder;
import com.intellij.icons.AllIcons;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.ProcessingContext;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import com.limemojito.oss.mql.MqlBuiltinTypes;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.doc.StructCatalog;
import com.limemojito.oss.mql.doc.VectorMatrixCatalog;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.reference.MqlTypeResolver;

/**
 * Members of MQL5's {@code vector}/{@code matrix}/{@code complex} types (T-5): instance methods and
 * fields after {@code v.}, static constructors after {@code vector::}. The receiver's type comes
 * from the nearest preceding {@code Type name} text, like {@link MQL4StdLibMemberCompletionProvider},
 * which also covers the constructor form {@code matrix m(2,2);}. Also the fields and methods of
 * the built-in structures ({@code dt.} on an {@code MqlDateTime}), from {@link StructCatalog}.
 */
public class MQL4VectorMatrixCompletionProvider extends CompletionProvider<CompletionParameters> {

    @Override
    protected void addCompletions(@NotNull CompletionParameters parameters, @NotNull ProcessingContext context, @NotNull CompletionResultSet result) {
        PsiFile file = parameters.getOriginalFile();
        PsiElement separator = PsiTreeUtil.prevVisibleLeaf(parameters.getPosition());
        PsiElement qualifier = separator == null ? null : PsiTreeUtil.prevVisibleLeaf(separator);
        if (separator != null && separator.getNode().getElementType() == MQL4Elements.DOT && qualifier != null) {
            StructCatalog.Members struct = StructCatalog.of(MqlTypeResolver.resolveQualifierTypeName(qualifier));
            if (struct != null) {
                String type = MqlTypeResolver.resolveQualifierTypeName(qualifier);
                for (String name : struct.fields()) {
                    result.addElement(LookupElementBuilder.create(name).withIcon(AllIcons.Nodes.Field).withTypeText(type));
                }
                for (String name : struct.methods()) {
                    result.addElement(method(name));
                }
                return;
            }
        }
        if (!MqlDialect.isMql5(file)) {
            return;
        }
        if (qualifier == null || qualifier.getNode().getElementType() != MQL4Elements.IDENTIFIER) {
            return;
        }
        if (separator.getNode().getElementType() == MQL4Elements.COLON_COLON) {
            List<String> statics = VectorMatrixCatalog.of(qualifier.getText()).statics();
            if (!statics.isEmpty()) {
                for (String name : statics) {
                    result.addElement(method(name));
                }
                result.stopHere(); // after matrix:: only its static constructors are valid
            }
            return;
        }
        String type = MQL4StdLibMemberCompletionProvider.guessDeclaredType(file.getText(),
                qualifier.getTextRange().getStartOffset(), qualifier.getText());
        if (type == null || !MqlBuiltinTypes.MQL5_TYPES.contains(type)) {
            return;
        }
        VectorMatrixCatalog.Members members = VectorMatrixCatalog.of(type);
        for (String name : members.methods()) {
            result.addElement(method(name));
        }
        for (String name : members.fields()) {
            result.addElement(LookupElementBuilder.create(name).withIcon(AllIcons.Nodes.Field).withTypeText(type));
        }
    }

    @NotNull
    private static LookupElementBuilder method(@NotNull String name) {
        return LookupElementBuilder.create(name)
                .withIcon(AllIcons.Nodes.Method)
                .withInsertHandler(ParenthesesInsertHandler.WITH_PARAMETERS);
    }
}
