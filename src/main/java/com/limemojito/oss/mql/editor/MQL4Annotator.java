/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.editor;

import com.intellij.lang.ASTNode;
import com.intellij.lang.annotation.AnnotationHolder;
import com.intellij.lang.annotation.Annotator;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.editor.DefaultLanguageHighlighterColors;
import com.intellij.openapi.editor.colors.TextAttributesKey;
import com.intellij.openapi.util.TextRange;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiWhiteSpace;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.PsiTreeUtil;
import com.limemojito.oss.mql.MqlBuiltinTypes;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.MqlEventHandlers;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

public class MQL4Annotator implements Annotator {

    public static final TextAttributesKey EVENT_HANDLER_NAME = TextAttributesKey.createTextAttributesKey(
            "MQL5_EVENT_HANDLER", DefaultLanguageHighlighterColors.FUNCTION_DECLARATION);

    public static final TextAttributesKey INPUT_PARAMETER = TextAttributesKey.createTextAttributesKey(
            "MQL5_INPUT_PARAMETER", DefaultLanguageHighlighterColors.INSTANCE_FIELD);

    @Override
    public void annotate(@NotNull PsiElement element, @NotNull AnnotationHolder holder) {
        IElementType type = element.getNode().getElementType();
        if (element instanceof MQL4FunctionElement func) {
            annotateEventHandler(func, holder);
        } else if (type == MQL4Elements.VAR_DECLARATION_STATEMENT) {
            annotateInputParameter(element, holder);
            annotateExternInitializer(element, holder);
        } else if (MACRO_OPERATORS.contains(type)) {
            annotateMacroOperator(element, holder);
        } else if (MQL4TokenSets.CONTEXTUAL_KEYWORDS.contains(type)) {
            keyword(element, holder);
        } else if (type == MQL4Elements.IDENTIFIER) {
            annotateReservedIdentifier(element, holder);
        } else if (type == MQL4Elements.CHAR_LITERAL) {
            annotateCharCode(element, holder);
        } else if (type == MQL4Elements.STRING_LITERAL) {
            annotateStringCharCodes(element, holder);
        } else if (NEEDS_RIGHT_OPERAND.contains(type)) {
            annotateMissingOperand(element, type, holder);
        }
    }

    /** Operators that can't end an expression: postfix {@code ++}/{@code --} and the macro operators can. */
    private static final TokenSet NEEDS_RIGHT_OPERAND = TokenSet.andNot(MQL4TokenSets.OPERATORS,
            TokenSet.create(MQL4Elements.PLUS_PLUS, MQL4Elements.MINUS_MINUS, MQL4Elements.PP_STRINGIZE, MQL4Elements.PP_CONCAT));

    private static final TokenSet EXPRESSION_END = TokenSet.create(MQL4Elements.SEMICOLON, MQL4Elements.R_ROUND_BRACKET,
            MQL4Elements.R_SQUARE_BRACKET, MQL4Elements.COMMA);

    /** Before {@code )} or {@code ,} these are a pointer or reference type: {@code (CFoo*)p}, {@code f(int &, T *)}. */
    private static final TokenSet DECLARATOR_OPERATORS = TokenSet.create(MQL4Elements.MUL, MQL4Elements.AND);

    /**
     * {@code int x = ;} and {@code y = 1 + ;}: an operator directly followed by the end of the
     * expression. The parser keeps statements as flat tokens, so the check is on the token pair. A
     * {@code #define} body may hold any fragment ({@code #define PLUS +}), so it is skipped.
     */
    private static void annotateMissingOperand(@NotNull PsiElement op, @NotNull IElementType type, @NotNull AnnotationHolder holder) {
        PsiElement next = PsiTreeUtil.nextLeaf(op);
        while (next != null && (next instanceof PsiWhiteSpace || MQL4TokenSets.COMMENTS_OR_WS.contains(next.getNode().getElementType()))) {
            next = PsiTreeUtil.nextLeaf(next);
        }
        if (next == null) {
            return;
        }
        IElementType nextType = next.getNode().getElementType();
        if (!EXPRESSION_END.contains(nextType)
                || (DECLARATOR_OPERATORS.contains(type) && nextType != MQL4Elements.SEMICOLON)
                || PsiTreeUtil.findFirstParent(op, e -> e.getNode() != null
                        && (e.getNode().getElementType() == MQL4Elements.PREPROCESSOR_DEFINE_BLOCK
                        || e.getNode().getElementType() == MQL4Elements.OPERATOR_NAME)) != null) {
            return;
        }
        holder.newAnnotation(HighlightSeverity.ERROR, "Expression expected after '" + op.getText() + "'")
                .range(op)
                .create();
    }

    /**
     * Keyword color for a word the lexer leaves an IDENTIFIER: the parser remaps {@code union},
     * {@code typedef}, {@code pack} and {@code group} where they are syntax, but the highlighter
     * re-lexes and never sees that.
     */
    private static void keyword(@NotNull PsiElement element, @NotNull AnnotationHolder holder) {
        holder.newSilentAnnotation(HighlightSeverity.INFORMATION)
                .range(element)
                .textAttributes(DefaultLanguageHighlighterColors.KEYWORD)
                .create();
    }

    /**
     * MQL5's matrix and vector types (reserved in MQL5, ordinary names in MQL4) and {@code offsetof}
     * before its argument list.
     */
    private static void annotateReservedIdentifier(@NotNull PsiElement id, @NotNull AnnotationHolder holder) {
        String text = id.getText();
        if (MqlBuiltinTypes.MQL5_TYPES.contains(text)) {
            PsiFile file = id.getContainingFile();
            if (file != null && MqlDialect.isMql5(file)) {
                keyword(id, holder);
            }
        } else if ("offsetof".equals(text)) {
            PsiElement next = PsiTreeUtil.nextVisibleLeaf(id);
            if (next != null && next.getNode().getElementType() == MQL4Elements.L_ROUND_BRACKET) {
                keyword(id, holder);
            }
        }
    }

    /**
     * {@code '\99999'} and {@code '\x10000'}: MetaEditor's error 239. The lexer keeps the literal one
     * token whatever the code, so the range check lives here.
     */
    private static void annotateCharCode(@NotNull PsiElement literal, @NotNull AnnotationHolder holder) {
        String text = literal.getText();
        if (text.length() < 4 || text.charAt(1) != '\\') {
            return;
        }
        String body = text.substring(2, text.length() - 1);
        String message = null;
        if (body.length() > 1 && (body.charAt(0) == 'x' || body.charAt(0) == 'X')) {
            if (body.length() > 5) {
                message = "only 4 hex digits expected";
            }
        } else if (!body.isEmpty() && body.chars().allMatch(Character::isDigit)) {
            long code = body.length() > 10 ? Long.MAX_VALUE : Long.parseLong(body);
            if (code > MAX_CHAR_CODE) {
                message = "too big for character code (" + body + "), must be in range [0," + MAX_CHAR_CODE + "]";
            }
        }
        if (message != null) {
            holder.newAnnotation(HighlightSeverity.ERROR, message).range(literal).create();
        }
    }

    private static final int MAX_CHAR_CODE = 65535;

    /** {@code "\99999"} inside a string: MetaEditor's warning 85 (the code is truncated, not rejected). */
    private static void annotateStringCharCodes(@NotNull PsiElement literal, @NotNull AnnotationHolder holder) {
        String text = literal.getText();
        int start = literal.getTextRange().getStartOffset();
        for (int i = 0; i < text.length() - 1; i++) {
            if (text.charAt(i) != '\\') {
                continue;
            }
            int j = i + 1;
            while (j < text.length() && j - i <= 5 && Character.isDigit(text.charAt(j))) {
                j++;
            }
            if (j > i + 1) {
                int code = Integer.parseInt(text.substring(i + 1, j));
                if (code > MAX_CHAR_CODE) {
                    holder.newAnnotation(HighlightSeverity.WARNING,
                                    code + " is too big for character code, must be in range [0," + MAX_CHAR_CODE + "]")
                            .range(new TextRange(start + i, start + j))
                            .create();
                }
                i = j - 1;
            } else {
                i++; // skip the escaped character, so "\\9" is not read as an escape
            }
        }
    }

    /** {@code extern int x = 3;}: MQL5's error 303 (MQL4 allows the initializer). */
    private static void annotateExternInitializer(@NotNull PsiElement varDecl, @NotNull AnnotationHolder holder) {
        ASTNode node = varDecl.getNode();
        if (node.findChildByType(MQL4Elements.EXTERN_KEYWORD) == null) {
            return;
        }
        PsiFile file = varDecl.getContainingFile();
        if (file == null || !MqlDialect.isMql5(file)) {
            return;
        }
        ASTNode list = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (list == null) {
            return;
        }
        for (ASTNode def = list.getFirstChildNode(); def != null; def = def.getTreeNext()) {
            if (def.getElementType() != MQL4Elements.VAR_DEFINITION) {
                continue;
            }
            ASTNode eq = def.findChildByType(MQL4Elements.EQ);
            if (eq != null) {
                holder.newAnnotation(HighlightSeverity.ERROR, "extern variable initialization is not allowed")
                        .range(eq)
                        .create();
            }
        }
    }

    private static final TokenSet MACRO_OPERATORS = TokenSet.create(MQL4Elements.PP_STRINGIZE, MQL4Elements.PP_CONCAT);

    /**
     * {@code #} and {@code ##} lex as tokens so macro bodies ({@code #define STR(x) #x}) are clean, but
     * outside a {@code #define} they are stray characters, which MetaEditor rejects.
     */
    private void annotateMacroOperator(@NotNull PsiElement token, @NotNull AnnotationHolder holder) {
        if (PsiTreeUtil.findFirstParent(token, e -> e.getNode() != null
                && e.getNode().getElementType() == MQL4Elements.PREPROCESSOR_DEFINE_BLOCK) != null) {
            return;
        }
        PsiElement next = token.getNextSibling();
        if ("#".equals(token.getText()) && next != null && next.getNode().getElementType() == MQL4Elements.IDENTIFIER) {
            // #region, #pragma ...: MetaEditor's error 109. (#region still folds, see MQL4FoldingBuilder.)
            holder.newAnnotation(HighlightSeverity.ERROR, "Invalid preprocessor command '#" + next.getText() + "'")
                    .range(token)
                    .create();
            return;
        }
        holder.newAnnotation(HighlightSeverity.ERROR, "'" + token.getText() + "' is only valid in a #define body")
                .range(token)
                .create();
    }

    private void annotateEventHandler(@NotNull MQL4FunctionElement func, @NotNull AnnotationHolder holder) {
        String name = func.getFunctionName();
        if (name == null || !MqlEventHandlers.NAMES.contains(name)) return;

        ASTNode nameNode = func.getNode().findChildByType(MQL4Elements.IDENTIFIER);
        if (nameNode == null) return;

        holder.newSilentAnnotation(HighlightSeverity.INFORMATION)
                .range(nameNode)
                .textAttributes(EVENT_HANDLER_NAME)
                .create();
    }

    private void annotateInputParameter(@NotNull PsiElement varDecl, @NotNull AnnotationHolder holder) {
        ASTNode node = varDecl.getNode();
        ASTNode child = node.getFirstChildNode();
        boolean isInput = false;
        while (child != null) {
            if (child.getElementType() == MQL4Elements.INPUT_KEYWORD
                    || child.getElementType() == MQL4Elements.SINPUT_KEYWORD) {
                isInput = true;
                break;
            }
            child = child.getTreeNext();
        }
        if (!isInput) return;

        ASTNode defList = node.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (defList == null) return;

        // Annotate EVERY declarator in the list, not just the first. `input int a, b, c;` parses as a
        // single VAR_DECLARATION_STATEMENT whose VAR_DEFINITION_LIST holds one VAR_DEFINITION per name;
        // findChildByType returned only `a`, leaving b/c un-highlighted.
        for (ASTNode def = defList.getFirstChildNode(); def != null; def = def.getTreeNext()) {
            if (def.getElementType() != MQL4Elements.VAR_DEFINITION) continue;
            ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
            if (id == null) continue;
            holder.newSilentAnnotation(HighlightSeverity.INFORMATION)
                    .range(id)
                    .textAttributes(INPUT_PARAMETER)
                    .create();
        }
    }
}
