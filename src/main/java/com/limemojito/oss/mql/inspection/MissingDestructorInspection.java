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
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * Flags a class that acquires a resource ({@code new}/{@code FileOpen}/an indicator handle) into a
 * MEMBER FIELD but has no destructor to release it. Only a member-field acquisition is flagged: a
 * class whose method acquires and releases a resource entirely through a local variable
 * ({@code void Foo() { int h = FileOpen(...); FileClose(h); }}) owns nothing at the class level and
 * needs no destructor — the previous version flagged any {@code new}/{@code FileOpen}/handle-creator
 * call ANYWHERE in the class body, including ones fully scoped to (and released within) a single
 * method.
 * <p>
 * Field names are collected two ways. {@code parseLocalVarDeclaration}'s narrow gate (reused for
 * class members) only produces a named {@code VAR_DECLARATION_STATEMENT} for a <em>primitive</em>
 * keyword type ({@code int}/{@code double}/...); a custom class/pointer-typed field —
 * {@code CObj *m_obj;}, the overwhelmingly common shape for a resource-owning member — is not a
 * {@code DATA_TYPES} token, so it falls through the parser's tolerant per-token fallback as raw,
 * unwrapped sibling tokens directly inside the class's inner block. Those are recognised here by a
 * small raw-token scan: {@code IDENTIFIER} [{@code *}|{@code &}] {@code IDENTIFIER} ({@code ;}|{@code =}|{@code ,}).
 */
public class MissingDestructorInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Class '%s' acquires a resource (new/FileOpen/indicator handle) but has no destructor to release it";
    private static final TokenSet NEW_KEYWORD = TokenSet.create(MQL4Elements.NEW_KEYWORD);
    private static final TokenSet EXPRESSION_STATEMENTS = TokenSet.create(MQL4Elements.EXPRESSION_STATEMENT);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (MQL4ClassElement cls : findClassElements(file)) {
            ProgressManager.checkCanceled();
            if (cls.getClassType() != MQL4ClassElement.ClassType.Class) continue;
            ASTNode innerBlock = cls.getInnerBlockNode();
            if (innerBlock == null) continue;

            String className = cls.getTypeName();
            boolean hasDestructor = false;
            List<String> fieldNames = new ArrayList<>();

            ASTNode child = innerBlock.getFirstChildNode();
            while (child != null) {
                if (child.getElementType() == MQL4Elements.FUNCTION
                        || child.getElementType() == MQL4Elements.FUNCTION_DECLARATION) {
                    PsiElement psi = child.getPsi();
                    if (psi instanceof MQL4FunctionElement funcElem
                            && ("~" + className).equals(funcElem.getFunctionName())) {
                        hasDestructor = true;
                    }
                } else if (child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                    PsiElement psi = child.getPsi();
                    if (psi != null) {
                        String name = getVariableName(psi);
                        if (name != null) fieldNames.add(name);
                    }
                } else if (child.getElementType() == MQL4Elements.IDENTIFIER) {
                    String name = rawFieldNameStartingAt(child);
                    if (name != null) fieldNames.add(name);
                }
                child = child.getTreeNext();
            }

            if (hasDestructor) continue;
            boolean acquiresResource = fieldNames.stream().anyMatch(name -> isFieldAssignedResource(innerBlock, name));
            if (acquiresResource) {
                problems.add(createWarning(manager, cls.getNavigationElement(),
                        String.format(MESSAGE, className)));
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /**
     * If {@code typeIdentifier} starts a raw (parser-fallback, un-wrapped) member field
     * declaration — {@code <TypeIdentifier> [*|&] <fieldName> (;|=|,)} — directly inside the class
     * inner block, returns {@code fieldName}; otherwise null. Only direct top-level siblings are
     * ever passed in here (methods are a single {@code FUNCTION} node the caller does not descend
     * into), so this cannot mistake something inside a method body for a field declaration.
     */
    @Nullable
    private static String rawFieldNameStartingAt(@NotNull ASTNode typeIdentifier) {
        ASTNode next = StatementAst.nextNonTrivia(typeIdentifier);
        if (next == null) return null;
        if (next.getElementType() == MQL4Elements.MUL || next.getElementType() == MQL4Elements.AND) {
            next = StatementAst.nextNonTrivia(next);
        }
        if (next == null || next.getElementType() != MQL4Elements.IDENTIFIER) return null;
        ASTNode after = StatementAst.nextNonTrivia(next);
        if (after == null) return null;
        IElementType at = after.getElementType();
        // A bare ';' terminating a raw field decl is wrapped by the parser as an EMPTY_STATEMENT
        // node, not a SEMICOLON token — accept both so `CObj *m_obj;` is recognised as a field.
        if (at == MQL4Elements.SEMICOLON || at == MQL4Elements.EMPTY_STATEMENT
                || at == MQL4Elements.EQ || at == MQL4Elements.COMMA) {
            return next.getText();
        }
        return null;
    }

    /**
     * True when a statement shaped {@code <fieldName> = <expr>;} occurs anywhere in
     * {@code innerBlock} (including nested inside a method body) whose right-hand side acquires a
     * resource ({@code new}, {@code FileOpen}, or an indicator-handle-creating call).
     */
    private static boolean isFieldAssignedResource(@NotNull ASTNode innerBlock, @NotNull String fieldName) {
        boolean[] found = {false};
        StatementAst.forEachDescendant(innerBlock, EXPRESSION_STATEMENTS, stmt -> {
            if (found[0]) return;
            ASTNode first = stmt.getFirstChildNode();
            while (first != null && StatementAst.isTrivia(first)) first = first.getTreeNext();
            if (first == null || first.getElementType() != MQL4Elements.IDENTIFIER || !fieldName.equals(first.getText())) {
                return;
            }
            ASTNode eq = StatementAst.nextNonTrivia(first);
            if (eq == null || eq.getElementType() != MQL4Elements.EQ) return;
            if (StatementAst.hasDescendant(stmt, NEW_KEYWORD)
                    || StatementAst.hasCall(stmt, "FileOpen")
                    || StatementAst.hasAnyCall(stmt, MQL5_HANDLE_CREATORS)) {
                found[0] = true;
            }
        });
        return found[0];
    }
}
