/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.CustomSuppressableInspectionTool;
import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.codeInspection.SuppressIntentionAction;
import com.intellij.codeInspection.SuppressionUtil;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiComment;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.IncorrectOperationException;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.MqlDialect;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

public abstract class MQL5SafetyInspectionBase extends LocalInspectionTool implements CustomSuppressableInspectionTool {

    public static final Set<String> MQL5_EVENT_HANDLERS = Set.of(
            "OnInit", "OnDeinit", "OnTick", "OnTimer", "OnTrade",
            "OnTradeTransaction", "OnBookEvent", "OnChartEvent",
            "OnCalculate", "OnTester", "OnTesterInit", "OnTesterDeinit",
            "OnTesterPass", "OnStart"
    );

    public static final Set<String> MQL5_HANDLE_CREATORS = Set.of(
            "iCustom", "iMA", "iMACD", "iRSI", "iBands", "iATR",
            "iADX", "iCCI", "iDeMarker", "iEnvelopes", "iFractals",
            "iGator", "iIchimoku", "iMomentum", "iOBV", "iOsMA",
            "iSAR", "iStdDev", "iStochastic", "iWPR", "iVolumes",
            "iBearsPower", "iBullsPower", "iChaikin", "iForce",
            "iAlligator", "iAO", "iAC", "iFrAMA", "iAMA", "iDEMA",
            "iTEMA", "iTriX", "iVIDyA", "IndicatorCreate"
    );

    public static final Set<String> MQL5_FILE_OPEN_FUNCS = Set.of("FileOpen");
    public static final Set<String> MQL5_FILE_CLOSE_FUNCS = Set.of("FileClose");

    public static final Set<String> MQL5_COPY_FUNCS = Set.of(
            "CopyRates", "CopyTime", "CopyOpen", "CopyHigh", "CopyLow",
            "CopyClose", "CopyTickVolume", "CopyRealVolume", "CopySpread",
            "CopyBuffer", "CopyTicks", "CopyTicksRange"
    );

    /**
     * Comment-based suppression. Adds "Suppress for function/statement/file" quick-fixes and
     * recognises {@code //noinspection <InspectionId>} comments — previously advertised (via
     * {@link CustomSuppressableInspectionTool}) but returned {@code null}, so nothing could be
     * suppressed. A trading-safety linter with heuristic checks needs a per-site escape hatch or
     * users disable the whole inspection on the first false positive.
     */
    @Nullable
    @Override
    public SuppressIntentionAction[] getSuppressActions(@Nullable PsiElement psiElement) {
        String id = getID();
        return new SuppressIntentionAction[]{
                new MqlSuppressFix(id, false),
                new MqlSuppressFix(id, true),
        };
    }

    /**
     * Inserts a {@code //noinspection <id>} comment above the enclosing function (or at the top of
     * the file) — a self-contained suppression fix (the platform's {@code SuppressByCommentFix} is
     * not exported in the lang-only module).
     */
    private static final class MqlSuppressFix extends SuppressIntentionAction {
        private final String id;
        private final boolean fileLevel;

        MqlSuppressFix(@NotNull String id, boolean fileLevel) {
            this.id = id;
            this.fileLevel = fileLevel;
        }

        @NotNull
        @Override
        public String getText() {
            return fileLevel ? "Suppress '" + id + "' for file" : "Suppress '" + id + "' for function";
        }

        @NotNull
        @Override
        public String getFamilyName() {
            return "Suppress MQL inspection";
        }

        @Override
        public boolean isAvailable(@NotNull Project project, Editor editor, @NotNull PsiElement element) {
            return holderFor(element) != null;
        }

        @Override
        public void invoke(@NotNull Project project, Editor editor, @NotNull PsiElement element) throws IncorrectOperationException {
            PsiElement holder = holderFor(element);
            if (holder == null) {
                return;
            }
            PsiComment comment = SuppressionUtil.createComment(project, SuppressionUtil.SUPPRESS_INSPECTIONS_TAG_NAME + " " + id, holder.getLanguage());
            if (fileLevel) {
                PsiElement first = holder.getFirstChild();
                if (first != null) {
                    holder.addBefore(comment, first);
                } else {
                    holder.add(comment);
                }
            } else {
                PsiElement parent = holder.getParent();
                if (parent != null) {
                    parent.addBefore(comment, holder);
                }
            }
        }

        @Nullable
        private PsiElement holderFor(@NotNull PsiElement element) {
            return fileLevel
                    ? element.getContainingFile()
                    : PsiTreeUtil.getParentOfType(element, MQL4FunctionElement.class, false);
        }
    }

    @Override
    public boolean isSuppressedFor(@NotNull PsiElement element) {
        String id = getID();
        // Function-scoped: //noinspection <id> on the line above the enclosing function.
        MQL4FunctionElement function = PsiTreeUtil.getParentOfType(element, MQL4FunctionElement.class, false);
        if (function != null && SuppressionUtil.isSuppressedInStatement(element, id, MQL4FunctionElement.class)) {
            return true;
        }
        // File-scoped: a //noinspection <id> comment among the file's leading comments.
        return isSuppressedAtFileLevel(element.getContainingFile(), id);
    }

    private static final java.util.Map<String, java.util.regex.Pattern> SUPPRESS_PATTERNS = new java.util.concurrent.ConcurrentHashMap<>();

    private static boolean isSuppressedAtFileLevel(@Nullable PsiFile file, @NotNull String id) {
        if (file == null) {
            return false;
        }
        // Cache the compiled marker per inspection id — this runs per reported problem per inspection.
        java.util.regex.Pattern marker = SUPPRESS_PATTERNS.computeIfAbsent(id, k ->
                java.util.regex.Pattern.compile("\\bnoinspection\\b.*(\\b" + java.util.regex.Pattern.quote(k) + "\\b|\\bALL\\b)"));
        for (PsiElement child : file.getChildren()) {
            if (child instanceof com.intellij.psi.PsiComment comment) {
                if (marker.matcher(comment.getText()).find()) {
                    return true;
                }
                continue;
            }
            // Keep scanning across leading whitespace; stop once we reach real code.
            if (child instanceof com.intellij.psi.PsiWhiteSpace) {
                continue;
            }
            break;
        }
        return false;
    }

    /**
     * True when {@code file} should be treated as MQL4. Delegates to the central {@link MqlDialect}
     * resolver so {@code .mqh} headers inherit their project's dialect instead of matching neither
     * (which used to let MQL4-only advice leak onto MQL5 headers).
     */
    protected boolean isMql4Source(@NotNull PsiFile file) {
        return MqlDialect.isMql4(file);
    }

    /** True when {@code file} should be treated as MQL5 (includes {@code .mqh} unless the project is MQL4-only). */
    protected boolean isMql5Source(@NotNull PsiFile file) {
        return MqlDialect.isMql5(file);
    }

    @NotNull
    protected List<MQL4FunctionElement> findFunctions(@NotNull PsiFile file) {
        List<MQL4FunctionElement> result = new ArrayList<>();
        for (PsiElement child : file.getChildren()) {
            if (child instanceof MQL4FunctionElement func) {
                result.add(func);
            }
        }
        return result;
    }

    @NotNull
    protected List<MQL4FunctionElement> findFunctionsByName(@NotNull PsiFile file, @NotNull String name) {
        List<MQL4FunctionElement> result = new ArrayList<>();
        for (PsiElement child : file.getChildren()) {
            if (child instanceof MQL4FunctionElement func && name.equals(func.getFunctionName())) {
                result.add(func);
            }
        }
        return result;
    }

    @NotNull
    protected List<MQL4ClassElement> findClassElements(@NotNull PsiFile file) {
        List<MQL4ClassElement> result = new ArrayList<>();
        for (PsiElement child : file.getChildren()) {
            if (child instanceof MQL4ClassElement cls) {
                result.add(cls);
            }
        }
        return result;
    }

    @NotNull
    protected List<PsiElement> findTopLevelVarDeclarations(@NotNull PsiFile file) {
        List<PsiElement> result = new ArrayList<>();
        for (PsiElement child : file.getChildren()) {
            ProgressManager.checkCanceled();
            if (child.getNode().getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                result.add(child);
            }
        }
        return result;
    }

    @Nullable
    protected ASTNode findBracketsBlock(@NotNull PsiElement function) {
        return function.getNode().findChildByType(MQL4Elements.BRACKETS_BLOCK);
    }

    @NotNull
    protected ProblemDescriptor createProblem(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message) {
        return createProblem(manager, element, message, true);
    }

    @NotNull
    protected ProblemDescriptor createProblem(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message,
                                              boolean onTheFly) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.GENERIC_ERROR_OR_WARNING, onTheFly);
    }

    /**
     * Error-or-warning variant carrying one or more {@link LocalQuickFix}es (onTheFly always true —
     * the fixes are only meaningful for the interactive/editor case).
     */
    @NotNull
    protected ProblemDescriptor createProblem(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message,
                                              @NotNull LocalQuickFix... fixes) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.GENERIC_ERROR_OR_WARNING, true, fixes);
    }

    @NotNull
    protected ProblemDescriptor createWarning(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message) {
        return createWarning(manager, element, message, true);
    }

    @NotNull
    protected ProblemDescriptor createWarning(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message,
                                              boolean onTheFly) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WARNING, onTheFly);
    }

    /**
     * Warning variant carrying one or more {@link LocalQuickFix}es (onTheFly always true — the
     * fixes are only meaningful for the interactive/editor case).
     */
    @NotNull
    protected ProblemDescriptor createWarning(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message,
                                              @NotNull LocalQuickFix... fixes) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WARNING, true, fixes);
    }

    @NotNull
    protected ProblemDescriptor createWeakWarning(@NotNull InspectionManager manager,
                                                  @NotNull PsiElement element,
                                                  @NotNull String message) {
        return createWeakWarning(manager, element, message, true);
    }

    @NotNull
    protected ProblemDescriptor createWeakWarning(@NotNull InspectionManager manager,
                                                  @NotNull PsiElement element,
                                                  @NotNull String message,
                                                  boolean onTheFly) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WEAK_WARNING, onTheFly);
    }

    /**
     * Weak-warning variant carrying one or more {@link LocalQuickFix}es (onTheFly always true —
     * the fixes are only meaningful for the interactive/editor case).
     */
    @NotNull
    protected ProblemDescriptor createWeakWarning(@NotNull InspectionManager manager,
                                                  @NotNull PsiElement element,
                                                  @NotNull String message,
                                                  @NotNull LocalQuickFix... fixes) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WEAK_WARNING, true, fixes);
    }

    protected boolean isEventHandler(@NotNull MQL4FunctionElement function) {
        return MQL5_EVENT_HANDLERS.contains(function.getFunctionName());
    }

    @Nullable
    protected ASTNode getReturnTypeNode(@NotNull MQL4FunctionElement function) {
        ASTNode node = function.getNode();
        ASTNode lParen = node.findChildByType(MQL4Elements.L_ROUND_BRACKET);
        if (lParen == null) return null;
        ASTNode current = node.getFirstChildNode();
        while (current != null && current != lParen) {
            if (MQL4TokenSets.DATA_TYPES.contains(current.getElementType())) {
                return current;
            }
            current = current.getTreeNext();
        }
        return null;
    }

    @NotNull
    protected List<ASTNode> getFunctionArgs(@NotNull MQL4FunctionElement function) {
        List<ASTNode> args = new ArrayList<>();
        ASTNode argsList = function.getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        if (argsList == null) return args;
        ASTNode child = argsList.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.FUNCTION_ARG) {
                args.add(child);
            }
            child = child.getTreeNext();
        }
        return args;
    }

    protected boolean hasChildOfType(@NotNull ASTNode parent, @NotNull IElementType type) {
        return parent.findChildByType(type) != null;
    }

    protected boolean isInputVariable(@NotNull PsiElement varDecl) {
        ASTNode node = varDecl.getNode();
        ASTNode child = node.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.INPUT_KEYWORD) {
                return true;
            }
            child = child.getTreeNext();
        }
        return false;
    }

    protected boolean isStaticVariable(@NotNull PsiElement varDecl) {
        ASTNode node = varDecl.getNode();
        ASTNode child = node.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.STATIC_KEYWORD) {
                return true;
            }
            child = child.getTreeNext();
        }
        return false;
    }

    protected boolean isExternVariable(@NotNull PsiElement varDecl) {
        ASTNode node = varDecl.getNode();
        ASTNode child = node.getFirstChildNode();
        while (child != null) {
            if (child.getElementType() == MQL4Elements.EXTERN_KEYWORD) {
                return true;
            }
            child = child.getTreeNext();
        }
        return false;
    }

    @Nullable
    protected String getVariableName(@NotNull PsiElement varDecl) {
        ASTNode defList = varDecl.getNode().findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (defList == null) return null;
        ASTNode def = defList.findChildByType(MQL4Elements.VAR_DEFINITION);
        if (def == null) return null;
        ASTNode id = def.findChildByType(MQL4Elements.IDENTIFIER);
        return id != null ? id.getText() : null;
    }

    protected boolean hasPreprocessorProperty(@NotNull PsiFile file, @NotNull String propertyName) {
        for (PsiElement child : file.getChildren()) {
            if (child.getNode().getElementType() == MQL4Elements.PREPROCESSOR_PROPERTY_BLOCK) {
                String text = child.getText();
                if (text.contains(propertyName)) {
                    return true;
                }
            }
        }
        return false;
    }

    protected boolean bracketBlockIsEmpty(@NotNull ASTNode bracketsBlock) {
        // Token-based check (no full-block getText() copy). A block with only comments counts as
        // empty — appropriate for "the handler does no real work".
        return StatementAst.codeBlockIsEmpty(bracketsBlock);
    }
}
