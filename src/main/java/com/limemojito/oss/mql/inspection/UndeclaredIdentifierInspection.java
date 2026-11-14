/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.lang.ASTNode;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import com.limemojito.oss.mql.reference.MqlTypeResolver;
import com.limemojito.oss.mql.reference.MqlVisibleNames;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * MetaEditor's error 256, "undeclared identifier", for names that aren't calls: a variable,
 * constant or type nothing declares ({@code x = undefinedVar;}), and a member a class doesn't have
 * ({@code obj.NoSuchMethod()}, {@code obj.noSuchField}). Global calls are
 * {@link UndefinedFunctionCallInspection}'s.
 *
 * <p>A member is checked only when the receiver's class and every class it derives from are
 * declared in the project or its headers: a base class from a missing header or a template could
 * supply any member. Skipped as for calls (see {@link UndeclaredNames}), and also {@code #property}
 * lines, {@code #include} paths and {@code #ifdef} names.</p>
 */
public class UndeclaredIdentifierInspection extends MQL5SafetyInspectionBase {

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        if (UndeclaredNames.hasUnresolvedInclude(file)) {
            return ProblemDescriptor.EMPTY_ARRAY;
        }
        List<ProblemDescriptor> problems = new SmartList<>();
        UndeclaredNames.forEachIdentifier(file, identifier -> {
            if (isUndeclared(identifier)) {
                problems.add(createProblem(manager, identifier.getPsi(),
                        "'" + identifier.getText() + "' - undeclared identifier", isOnTheFly));
            }
        });
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private static boolean isUndeclared(@NotNull ASTNode identifier) {
        IElementType prev = UndeclaredNames.prevType(identifier);
        if (prev == MQL4Elements.DOT) {
            return isMissingMember(identifier);
        }
        if (prev == MQL4Elements.COLON_COLON || StatementAst.isCallIdentifier(identifier)
                || UndeclaredNames.isDeclarationName(identifier)) {
            return false;
        }
        String name = identifier.getText();
        if (UndeclaredNames.isBuiltin(name)) {
            return false;
        }
        PsiElement psi = identifier.getPsi();
        return MqlResolveUtil.resolve(psi, name).isEmpty() && !MqlVisibleNames.isDeclared(name, psi.getContainingFile());
    }

    private static boolean isMissingMember(@NotNull ASTNode member) {
        PsiElement dot = PsiTreeUtil.prevVisibleLeaf(member.getPsi());
        PsiElement qualifier = dot == null ? null : PsiTreeUtil.prevVisibleLeaf(dot);
        MQL4ClassElement receiver = qualifier == null ? null : MqlTypeResolver.resolveQualifierClass(qualifier);
        if (receiver == null || !hierarchyKnown(receiver, new HashSet<>())) {
            return false;
        }
        return MqlResolveUtil.resolveMemberInClassHierarchy(receiver, member.getText()).isEmpty();
    }

    /** True when every base class of {@code cls}, all the way up, is a class the project declares. */
    private static boolean hierarchyKnown(@NotNull MQL4ClassElement cls, @NotNull Set<MQL4ClassElement> seen) {
        if (!seen.add(cls) || seen.size() > 16) {
            return seen.size() <= 16;
        }
        for (String baseName : MqlResolveUtil.baseClassNames(cls)) {
            MQL4ClassElement base = findBase(baseName, cls);
            if (base == null || !hierarchyKnown(base, seen)) {
                return false;
            }
        }
        return true;
    }

    @Nullable
    private static MQL4ClassElement findBase(@NotNull String name, @NotNull MQL4ClassElement from) {
        return MqlResolveUtil.findClassByName(name, from.getProject(), from);
    }
}
