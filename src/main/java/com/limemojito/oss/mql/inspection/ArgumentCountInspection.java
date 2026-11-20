/*
 * Copyright (c) 2026.  RIGGWIRE Trading Systems.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.index.MQL4DefineNameIndex;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import com.limemojito.oss.mql.reference.MqlVisibleNames;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * A call whose argument count no function of that name can take: {@code CalcLot(risk, sl, 0)} when every
 * {@code CalcLot} has two parameters. MetaEditor rejects it with error 199 "wrong parameters count".
 * <p>
 * Every function, method and constructor of that name the call can see is counted (the file's
 * {@code #include} closure and, for a header, that of each program including it), with the defaults a
 * declaration gives. Not checked: built-in functions (no verified catalog of their parameter counts yet),
 * member calls ({@code obj.Method(...)}), names that are also a {@code #define} macro or a variable (a
 * function pointer), and files whose {@code #include}s the plugin can't all read.
 */
public class ArgumentCountInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (UndeclaredNames.hasUnresolvedInclude(file)) {
            return ProblemDescriptor.EMPTY_ARRAY;
        }
        Map<String, List<int[]>> arities = arities(file);
        GlobalSearchScope scope = GlobalSearchScope.allScope(file.getProject());
        List<ProblemDescriptor> problems = new SmartList<>();
        UndeclaredNames.forEachIdentifier(file, id -> {
            if (!StatementAst.isCallIdentifier(id) || UndeclaredNames.isDeclarationName(id)) return;
            ASTNode before = StatementAst.prevNonTrivia(id);
            if (before != null && (before.getElementType() == MQL4Elements.DOT || before.getElementType() == MQL4Elements.COLON_COLON)) {
                return; // obj.Method(...), Base::Method(...): the member's class decides, and built-in types have members too
            }
            String name = id.getText();
            List<int[]> ranges = arities.get(name);
            if (ranges == null || UndeclaredNames.isBuiltin(name)) return;
            int args = argCount(id);
            if (args < 0) return;
            if (ranges.stream().anyMatch(r -> args >= r[0] && args <= r[1])) return;
            if (!MQL4DefineNameIndex.getInstance().getElements(name, file.getProject(), scope).isEmpty()) return;
            PsiElement psi = id.getPsi();
            if (MqlResolveUtil.resolve(psi, name).stream().anyMatch(e -> !(e instanceof MQL4FunctionElement))) return;
            problems.add(createProblem(manager, psi, "wrong parameters count: " + args + " passed, '" + name + "' takes "
                    + describe(ranges), isOnTheFly));
        });
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    /** Function name -> each overload's {required, all} parameter counts, over every file the calls can see. */
    private Map<String, List<int[]>> arities(@NotNull PsiFile file) {
        Set<PsiFile> files = new LinkedHashSet<>(MqlVisibleNames.includeClosure(file));
        for (PsiFile program : MqlVisibleNames.programsIncluding(file)) {
            files.addAll(MqlVisibleNames.includeClosure(program));
        }
        Map<String, List<int[]>> out = new HashMap<>();
        for (PsiFile f : files) {
            for (MQL4FunctionElement func : PsiTreeUtil.findChildrenOfType(f, MQL4FunctionElement.class)) {
                String name = func.getFunctionName();
                if (name.equals(MQL4FunctionElement.UNKNOWN_NAME)) continue;
                List<ASTNode> params = getFunctionArgs(func);
                if (params.size() == 1 && params.get(0).getText().trim().equals("void")) {
                    params = List.of();
                }
                int required = (int) params.stream().filter(p -> p.findChildByType(MQL4Elements.EQ) == null).count();
                out.computeIfAbsent(name, k -> new ArrayList<>()).add(new int[]{required, params.size()});
            }
        }
        return out;
    }

    /**
     * The call's argument count. An initializer's tokens are flat (no bracket block), so there the
     * top-level commas up to the matching {@code )} are counted; -1 when the {@code (...)} can't be found.
     */
    private static int argCount(@NotNull ASTNode id) {
        ASTNode next = id.getTreeNext();
        while (next != null && StatementAst.isTrivia(next)) next = next.getTreeNext();
        if (next == null) return -1;
        if (next.getElementType() == MQL4Elements.BRACKETS_BLOCK) return StatementAst.callArgCount(id);
        if (next.getElementType() != MQL4Elements.L_ROUND_BRACKET) return -1;
        int depth = 0, commas = 0;
        boolean content = false;
        for (ASTNode n = next; n != null; n = n.getTreeNext()) {
            IElementType t = n.getElementType();
            if (StatementAst.isTrivia(n)) continue;
            if (t == MQL4Elements.L_ROUND_BRACKET || t == MQL4Elements.L_SQUARE_BRACKET || t == MQL4Elements.L_CURLY_BRACKET) {
                if (depth++ > 0) content = true;
            } else if (t == MQL4Elements.R_ROUND_BRACKET || t == MQL4Elements.R_SQUARE_BRACKET || t == MQL4Elements.R_CURLY_BRACKET) {
                if (--depth == 0) return content || commas > 0 ? commas + 1 : 0;
                content = true;
            } else if (t == MQL4Elements.COMMA && depth == 1) {
                commas++;
            } else if (t == MQL4Elements.SEMICOLON) {
                return -1;
            } else {
                content = true;
            }
        }
        return -1; // the ')' is past this node's siblings
    }

    private static String describe(@NotNull List<int[]> ranges) {
        Set<String> shown = new LinkedHashSet<>();
        for (int[] r : ranges) {
            shown.add(r[0] == r[1] ? Integer.toString(r[0]) : r[0] + " to " + r[1]);
        }
        return String.join(" or ", shown);
    }
}
