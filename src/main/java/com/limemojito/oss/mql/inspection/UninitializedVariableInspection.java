/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import org.jetbrains.annotations.NotNull;

import java.util.List;
import java.util.Set;

public class UninitializedVariableInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Variable '%s' is not initialized — may contain undefined value";
    private static final Set<String> NUMERIC_TYPES = Set.of(
            "INT_KEYWORD", "LONG_KEYWORD", "SHORT_KEYWORD", "CHAR_KEYWORD",
            "UINT_KEYWORD", "ULONG_KEYWORD", "USHORT_KEYWORD", "UCHAR_KEYWORD",
            "DOUBLE_KEYWORD", "FLOAT_KEYWORD", "BOOL_KEYWORD",
            "COLOR_KEYWORD", "DATETIME_KEYWORD"
    );
    private static final Set<String> STRING_TYPES = Set.of("STRING_KEYWORD");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : findTopLevelVarDeclarations(file)) {
            ProgressManager.checkCanceled();
            if (isInputVariable(child) || isExternVariable(child)) continue;

            ASTNode node = child.getNode();
            boolean isNumericType = false;
            boolean isStringType = false;
            ASTNode typeNode = node.getFirstChildNode();
            while (typeNode != null) {
                String typeName = typeNode.getElementType().toString();
                if (NUMERIC_TYPES.contains(typeName)) {
                    isNumericType = true;
                    break;
                }
                if (STRING_TYPES.contains(typeName)) {
                    isStringType = true;
                    break;
                }
                if (typeNode.getElementType() == MQL4Elements.VAR_DEFINITION_LIST) break;
                typeNode = typeNode.getTreeNext();
            }
            if (!isNumericType && !isStringType) continue;

            ASTNode defList = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
            if (defList == null) continue;
            ASTNode def = defList.findChildByType(MQL4Elements.VAR_DEFINITION);
            if (def == null) continue;

            boolean hasInitializer = def.findChildByType(MQL4Elements.EQ) != null;
            if (!hasInitializer) {
                String name = getVariableName(child);
                if (name != null) {
                    String initValue = isStringType ? " = \"\"" : " = 0";
                    problems.add(manager.createProblemDescriptor(child, child,
                            String.format(MESSAGE, name),
                            ProblemHighlightType.WARNING, true,
                            new AddInitializerFix(initValue)));
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private record AddInitializerFix(@NotNull String initValue) implements LocalQuickFix {

        @NotNull
        @Override
        public String getName() {
            return "Add initializer '" + initValue.trim() + "'";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return "Add variable initializer";
        }

        @Override
        public void applyFix(@NotNull Project project, @NotNull ProblemDescriptor descriptor) {
            PsiElement element = descriptor.getPsiElement();
            Document doc = PsiDocumentManager.getInstance(project).getDocument(element.getContainingFile());
            if (doc == null) return;
            ASTNode node = element.getNode();
            ASTNode defList = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
            if (defList == null) return;
            ASTNode def = defList.findChildByType(MQL4Elements.VAR_DEFINITION);
            if (def == null) return;
            ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
            if (id == null) return;
            int offset = id.getTextRange().getEndOffset();
            doc.insertString(offset, initValue);
        }
    }
}
