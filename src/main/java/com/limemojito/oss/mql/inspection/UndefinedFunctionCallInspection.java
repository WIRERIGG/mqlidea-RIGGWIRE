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
import com.intellij.psi.PsiNamedElement;
import com.intellij.openapi.vfs.VirtualFileManager;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.util.SmartList;
import com.limemojito.oss.mql.MqlBuiltinFunctions;
import com.limemojito.oss.mql.MqlBuiltinTypes;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4DefineElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import com.limemojito.oss.mql.psi.impl.MQL4TypedefElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * A global call ({@code Foo(...)}) to a name that is no built-in and is declared nowhere the
 * resolver looks: locals and parameters, the enclosing class, the {@code #include} closure, then
 * the whole project. That is MetaEditor's error 256, "undeclared identifier".
 *
 * <p>A file with an {@code #include} that doesn't resolve is skipped whole: the missing header could
 * declare any name. Member and scoped calls ({@code obj.Foo()}, {@code X::Foo()}) are not checked,
 * and neither are {@code #define} and {@code #import} bodies.</p>
 */
public class UndefinedFunctionCallInspection extends MQL5SafetyInspectionBase {

    private static final TokenSet SKIPPED_BLOCKS = TokenSet.create(MQL4Elements.PREPROCESSOR_DEFINE_BLOCK,
            MQL4Elements.PREPROCESSOR_IMPORT_BLOCK, MQL4Elements.OPERATOR_NAME);

    @Override
    public ProblemDescriptor[] checkFile(@NotNull PsiFile file, @NotNull InspectionManager manager, boolean isOnTheFly) {
        for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(file, MQL4PreprocessorIncludeBlock.class)) {
            if (include.resolveIncludedFile() == null) {
                return ProblemDescriptor.EMPTY_ARRAY;
            }
        }
        List<ProblemDescriptor> problems = new SmartList<>();
        visit(file.getNode(), manager, isOnTheFly, problems);
        return problems.toArray(ProblemDescriptor.EMPTY_ARRAY);
    }

    private void visit(@NotNull ASTNode node, @NotNull InspectionManager manager, boolean isOnTheFly,
                       @NotNull List<ProblemDescriptor> problems) {
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType type = child.getElementType();
            if (SKIPPED_BLOCKS.contains(type)) {
                continue;
            }
            if (type == MQL4Elements.IDENTIFIER) {
                if (isUndefinedCall(child)) {
                    problems.add(createProblem(manager, child.getPsi(),
                            "'" + child.getText() + "' - undeclared identifier", isOnTheFly));
                }
            } else if (child.getFirstChildNode() != null) {
                visit(child, manager, isOnTheFly, problems);
            }
        }
    }

    private static boolean isUndefinedCall(@NotNull ASTNode identifier) {
        if (!StatementAst.isCallIdentifier(identifier)) {
            return false;
        }
        String name = identifier.getText();
        if (MQL4DocumentationProvider.getEntryByText(name) != null || MqlBuiltinFunctions.contains(name)
                || MqlBuiltinTypes.MQL5_TYPES.contains(name) || "offsetof".equals(name)) {
            return false;
        }
        PsiElement psi = identifier.getPsi();
        ASTNode parent = identifier.getTreeParent();
        PsiElement prev = PsiTreeUtil.prevVisibleLeaf(psi);
        if ((parent != null && parent.getElementType() == MQL4Elements.VAR_DEFINITION)
                || (prev != null && prev.getNode().getElementType() == MQL4Elements.IDENTIFIER)) {
            return false; // CFoo obj(1, 2): `Type name(` declares, it doesn't call
        }
        MQL4FunctionElement function = PsiTreeUtil.getParentOfType(psi, MQL4FunctionElement.class);
        if (function != null && function.getNameIdentifier() != null
                && function.getNameIdentifier().getNode() == identifier) {
            return false; // the name of a function declaration or definition
        }
        return MqlResolveUtil.resolve(psi, name).isEmpty() && !closureNames(psi.getContainingFile()).contains(name);
    }

    /**
     * Every name declared in the file and its {@code #include} closure, read from the PSI. The
     * resolver serves the closure from the stub indexes, which don't cover a header outside the
     * project ({@code <MQLTA Utils.mqh>} in MT5's own {@code MQL5/Include}), so its functions
     * would look undeclared without this.
     */
    @NotNull
    private static Set<String> closureNames(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            Set<String> names = new HashSet<>();
            Set<PsiFile> seen = new HashSet<>();
            Deque<PsiFile> queue = new ArrayDeque<>();
            queue.add(file);
            while (!queue.isEmpty()) {
                PsiFile current = queue.poll();
                if (!seen.add(current)) {
                    continue;
                }
                for (PsiElement declaration : PsiTreeUtil.findChildrenOfAnyType(current, MQL4FunctionElement.class,
                        MQL4ClassElement.class, MQL4VarDefinitionElement.class, MQL4DefineElement.class, MQL4TypedefElement.class)) {
                    ProgressManager.checkCanceled();
                    String name = ((PsiNamedElement) declaration).getName();
                    if (name != null) {
                        names.add(name);
                    }
                }
                for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(current, MQL4PreprocessorIncludeBlock.class)) {
                    PsiFile target = include.resolveIncludedFile();
                    if (target != null) {
                        queue.add(target);
                    }
                }
            }
            return CachedValueProvider.Result.create(names, PsiModificationTracker.getInstance(file.getProject()),
                    VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS);
        });
    }
}
