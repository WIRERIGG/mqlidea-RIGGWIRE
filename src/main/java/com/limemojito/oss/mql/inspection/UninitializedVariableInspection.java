/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
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
import com.intellij.psi.tree.IElementType;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
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

            for (ASTNode def = defList.getFirstChildNode(); def != null; def = def.getTreeNext()) {
                if (def.getElementType() != MQL4Elements.VAR_DEFINITION) continue;
                if (isArrayDeclarator(def)) continue;

                boolean hasInitializer = def.findChildByType(MQL4Elements.EQ) != null;
                if (!hasInitializer) {
                    ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
                    if (id != null) {
                        String initValue = isStringType ? " = \"\"" : " = 0";
                        problems.add(manager.createProblemDescriptor(child, child,
                                String.format(MESSAGE, id.getText()),
                                ProblemHighlightType.WARNING, true,
                                new AddInitializerFix(initValue, id.getText())));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * True if the var definition declares an array (e.g. {@code double buffer[];}) — such declarators
     * cannot take a scalar initializer. The parser may keep the bracket tokens inside the
     * VAR_DEFINITION, or (via error recovery) as following siblings of the VAR_DEFINITION_LIST,
     * so both locations are checked.
     */
    private static boolean isArrayDeclarator(@NotNull ASTNode def) {
        if (def.findChildByType(MQL4Elements.L_SQUARE_BRACKET) != null) return true;
        ASTNode next = def.getTreeNext();
        ASTNode scope = def.getTreeParent();
        while (next == null && scope != null
                && scope.getElementType() != MQL4Elements.VAR_DECLARATION_STATEMENT) {
            next = scope.getTreeNext();
            scope = scope.getTreeParent();
        }
        while (next != null) {
            IElementType type = next.getElementType();
            if (type == MQL4Elements.L_SQUARE_BRACKET) return true;
            if (!MQL4TokenSets.COMMENTS_OR_WS.contains(type)) return false;
            next = next.getTreeNext();
        }
        return false;
    }

    private record AddInitializerFix(@NotNull String initValue,
                                     @NotNull String variableName) implements LocalQuickFix {

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
            if (element == null) return;
            Document doc = PsiDocumentManager.getInstance(project).getDocument(element.getContainingFile());
            if (doc == null) return;
            ASTNode node = element.getNode();
            ASTNode defList = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
            if (defList == null) return;
            for (ASTNode def = defList.getFirstChildNode(); def != null; def = def.getTreeNext()) {
                if (def.getElementType() != MQL4Elements.VAR_DEFINITION) continue;
                ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
                if (id == null || !variableName.equals(id.getText())) continue;
                if (isArrayDeclarator(def)) return; // arrays cannot take a scalar initializer
                doc.insertString(id.getTextRange().getEndOffset(), initValue);
                return;
            }
        }
    }
}
