/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.CustomSuppressableInspectionTool;
import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.codeInspection.SuppressIntentionAction;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.util.SmartList;
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

    @Nullable
    @Override
    public SuppressIntentionAction[] getSuppressActions(@Nullable PsiElement psiElement) {
        return null;
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
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.GENERIC_ERROR_OR_WARNING, true);
    }

    @NotNull
    protected ProblemDescriptor createWarning(@NotNull InspectionManager manager,
                                              @NotNull PsiElement element,
                                              @NotNull String message) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WARNING, true);
    }

    @NotNull
    protected ProblemDescriptor createWeakWarning(@NotNull InspectionManager manager,
                                                  @NotNull PsiElement element,
                                                  @NotNull String message) {
        return manager.createProblemDescriptor(element, element, message,
                ProblemHighlightType.WEAK_WARNING, true);
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
        String text = bracketsBlock.getText().trim();
        if (text.length() <= 2) return true;
        String inner = text.substring(1, text.length() - 1).trim();
        return inner.isEmpty();
    }
}
