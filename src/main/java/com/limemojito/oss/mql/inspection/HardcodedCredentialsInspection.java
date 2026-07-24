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
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.List;
import java.util.regex.Pattern;

/**
 * Flags a credential-ASSIGNMENT shape — {@code password = <value>}, {@code apikey: <value>} —
 * rather than any string literal that merely mentions a credential-sounding word. The previous
 * version regexed literal content for password/token/auth/secret/key/api substrings, which flagged
 * ordinary prose like {@code Print("Authorization failed")}. The new pattern requires the keyword
 * to be immediately followed by an assignment/colon and a value, checked against both the literal's
 * own (unquoted) text — covering a single literal embedding {@code "password=abc123"}, e.g. inside a
 * URL/query string — and the literal's containing statement's full text, which covers the idiomatic
 * {@code string password = "secret123";} (the assignment lives in real code around the literal, not
 * inside the literal itself).
 */
public class HardcodedCredentialsInspection extends MQL5SafetyInspectionBase {

    private static final String MESSAGE = "Potential hardcoded credentials detected — use input parameters instead";
    // Requires an actual secret value after the keyword's = / : — an optional opening quote then a
    // real value character (not whitespace, another quote, '+', ';' or ')'). This flags both the
    // inline form "password=hunter2" and the variable form  password = "hunter2"  (opening quote
    // then value), while EXCLUDING the safe URL/query idiom  "&token=" + m_key  where the char
    // after the keyword's '=' is the string's own CLOSING quote followed by whitespace/'+': there
    // the secret lives in a variable, not the literal.
    private static final Pattern CREDENTIAL_PATTERN =
            Pattern.compile("(?i)\\b(password|api_?key|secret|token|passwd)\\b\\s*[=:]\\s*\"?\\s*[^\\s\"'+;)]");

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        List<ProblemDescriptor> problems = new SmartList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child instanceof MQL4FunctionElement func && !func.isDeclaration()) {
                ASTNode body = findBracketsBlock(child);
                if (body != null) {
                    ASTNode literal = findCredentialLiteral(body);
                    if (literal != null) {
                        problems.add(createProblem(manager, StatementAst.anchor(literal, child.getNavigationElement()), MESSAGE, isOnTheFly));
                    }
                }
            }
        }
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    @Nullable
    private static ASTNode findCredentialLiteral(@NotNull ASTNode root) {
        for (ASTNode child = root.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == MQL4Elements.STRING_LITERAL && matchesCredentialShape(child)) {
                return child;
            }
            ASTNode found = findCredentialLiteral(child);
            if (found != null) return found;
        }
        return null;
    }

    /**
     * True when the literal's own text, or the full text of its containing
     * {@code VAR_DECLARATION_STATEMENT}/{@code EXPRESSION_STATEMENT}, matches the
     * credential-assignment shape.
     */
    private static boolean matchesCredentialShape(@NotNull ASTNode literal) {
        if (CREDENTIAL_PATTERN.matcher(literal.getText()).find()) {
            return true;
        }
        ASTNode statement = enclosingStatement(literal);
        return statement != null && CREDENTIAL_PATTERN.matcher(statement.getText()).find();
    }

    @Nullable
    private static ASTNode enclosingStatement(@NotNull ASTNode node) {
        for (ASTNode current = node.getTreeParent(); current != null; current = current.getTreeParent()) {
            IElementType t = current.getElementType();
            if (t == MQL4Elements.VAR_DECLARATION_STATEMENT || t == MQL4Elements.EXPRESSION_STATEMENT) {
                return current;
            }
        }
        return null;
    }
}
