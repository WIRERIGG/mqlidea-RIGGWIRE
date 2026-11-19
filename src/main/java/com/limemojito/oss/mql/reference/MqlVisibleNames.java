/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.VirtualFileManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.PsiNamedElement;
import com.intellij.psi.search.FileTypeIndex;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.stubs.StubIndex;
import com.intellij.psi.stubs.StubIndexKey;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.intellij.psi.util.PsiTreeUtil;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL5FileType;
import com.limemojito.oss.mql.index.MQL4IndexKeys;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4DefineElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import com.limemojito.oss.mql.psi.impl.MQL4TypedefElement;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;

/**
 * Whether a name is declared anywhere a file can see, for the "undeclared identifier" checks. It
 * is deliberately lenient: a name counts if any of these declares it.
 * <ol>
 *     <li>the file and its {@code #include} closure, read from the PSI. The resolver serves the
 *     closure from the stub indexes, which don't cover headers outside the project (MT5's own
 *     {@code MQL5/Include}).</li>
 *     <li>for a header, the closure of each project {@code .mq5}/{@code .mq4} that includes it:
 *     MetaEditor compiles a header inside its includer, so it sees what the includer included
 *     before it.</li>
 *     <li>any project file, through the stub indexes (not the indexed MetaTrader Include folders).</li>
 * </ol>
 */
public final class MqlVisibleNames {

    private record Index<T extends PsiElement>(StubIndexKey<String, T> key, Class<T> type) {
        boolean has(@NotNull String name, @NotNull Project project, @NotNull GlobalSearchScope scope) {
            return !StubIndex.getInstance().processElements(key, name, project, scope, type, e -> false);
        }
    }

    private static final List<Index<?>> INDEXES = List.of(
            new Index<>(MQL4IndexKeys.FUNCTION_NAME_INDEX_KEY, MQL4FunctionElement.class),
            new Index<>(MQL4IndexKeys.CLASS_NAME_INDEX_KEY, MQL4ClassElement.class),
            new Index<>(MQL4IndexKeys.ENUM_NAME_INDEX_KEY, MQL4EnumElement.class),
            new Index<>(MQL4IndexKeys.ENUM_FIELD_NAME_INDEX_KEY, MQL4EnumElement.class),
            new Index<>(MQL4IndexKeys.GLOBAL_VAR_NAME_INDEX_KEY, MQL4VarDefinitionElement.class),
            new Index<>(MQL4IndexKeys.TYPEDEF_NAME_INDEX_KEY, MQL4TypedefElement.class),
            new Index<>(MQL4IndexKeys.DEFINE_NAME_INDEX_KEY, MQL4DefineElement.class));

    private static final java.util.regex.Pattern WORD = java.util.regex.Pattern.compile("[A-Za-z_]\\w*");

    private MqlVisibleNames() {
    }

    public static boolean isDeclared(@NotNull String name, @NotNull PsiFile file) {
        return isDeclared(name, file, false);
    }

    /**
     * As {@link #isDeclared(String, PsiFile)}; with {@code skipLoopVariables}, a {@code for(int i = ...)} init variable
     * doesn't count: in MQL5 it is scoped to its loop (MetaEditor 5 reports {@code i} after the loop as undeclared).
     */
    public static boolean isDeclared(@NotNull String name, @NotNull PsiFile file, boolean skipLoopVariables) {
        if (names(file, skipLoopVariables).contains(name)) {
            return true;
        }
        for (PsiFile includer : includers(file)) {
            if (names(includer, skipLoopVariables).contains(name)) {
                return true;
            }
        }
        Project project = file.getProject();
        // Project files only: a header in the indexed MetaTrader Include folders counts only once
        // something includes it, and the closures above already cover that.
        GlobalSearchScope scope = GlobalSearchScope.projectScope(project);
        for (Index<?> index : INDEXES) {
            if (index.has(name, project, scope)) {
                return true;
            }
        }
        return false;
    }

    /** Every name declared in {@code file} and its {@code #include} closure. */
    @NotNull
    public static Set<String> closureNames(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> CachedValueProvider.Result.create(collectNames(file, false),
                PsiModificationTracker.getInstance(file.getProject()), VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS));
    }

    @NotNull
    private static Set<String> closureNamesOutsideLoops(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> CachedValueProvider.Result.create(collectNames(file, true),
                PsiModificationTracker.getInstance(file.getProject()), VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS));
    }

    @NotNull
    private static Set<String> names(@NotNull PsiFile file, boolean skipLoopVariables) {
        return skipLoopVariables ? closureNamesOutsideLoops(file) : closureNames(file);
    }

    @NotNull
    private static Set<String> collectNames(@NotNull PsiFile file, boolean skipLoopVariables) {
        Set<String> names = new HashSet<>();
        for (PsiFile current : closureFiles(file)) {
            for (PsiElement declaration : PsiTreeUtil.findChildrenOfAnyType(current, MQL4FunctionElement.class,
                    MQL4ClassElement.class, MQL4VarDefinitionElement.class, MQL4DefineElement.class,
                    MQL4TypedefElement.class, MQL4EnumElement.class, MQL4EnumFieldElement.class,
                    com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement.class)) {
                ProgressManager.checkCanceled();
                String name = ((PsiNamedElement) declaration).getName();
                if (name != null && !(skipLoopVariables && isLoopVariable(declaration))) {
                    names.add(name);
                }
                if (skipLoopVariables && declaration instanceof MQL4DefineElement) {
                    // #define foreach(T, c) for(Iter<T> it(c); ...): the body isn't parsed, and 'it' is used beside the call
                    java.util.regex.Matcher word = WORD.matcher(declaration.getText());
                    while (word.find()) {
                        names.add(word.group());
                    }
                }
            }
        }
        return names;
    }

    /** A variable declared in a {@code for(...)} header's init clause. */
    private static boolean isLoopVariable(@NotNull PsiElement declaration) {
        if (!(declaration instanceof MQL4VarDefinitionElement)) {
            return false;
        }
        PsiElement statement = declaration.getParent();
        while (statement != null && statement.getNode().getElementType() != com.limemojito.oss.mql.psi.MQL4Elements.VAR_DECLARATION_STATEMENT) {
            statement = statement instanceof PsiFile ? null : statement.getParent(); // VAR_DEFINITION -> VAR_DEFINITION_LIST -> statement
        }
        PsiElement header = statement == null ? null : statement.getParent();
        return header != null && MqlPsiUtil.forHeaderOf(header.getParent()) == header.getNode();
    }

    /** {@code file} and every file its {@code #include}s reach, {@code file} first. */
    @NotNull
    public static Set<PsiFile> includeClosure(@NotNull PsiFile file) {
        return closureFiles(file);
    }

    /** The project's {@code .mq5}/{@code .mq4} programs whose {@code #include} closure reaches {@code header}. */
    @NotNull
    public static List<PsiFile> programsIncluding(@NotNull PsiFile header) {
        return includers(header);
    }

    /** {@code file} and every file its {@code #include}s reach. */
    @NotNull
    private static Set<PsiFile> closureFiles(@NotNull PsiFile file) {
        Set<PsiFile> seen = new LinkedHashSet<>();
        Deque<PsiFile> queue = new ArrayDeque<>();
        queue.add(file);
        while (!queue.isEmpty()) {
            PsiFile current = queue.poll();
            if (!seen.add(current)) {
                continue;
            }
            for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(current, MQL4PreprocessorIncludeBlock.class)) {
                PsiFile target = include.resolveIncludedFile();
                if (target != null) {
                    queue.add(target);
                }
            }
        }
        return seen;
    }

    /** The project's {@code .mq5}/{@code .mq4} files whose {@code #include} closure reaches {@code header}. */
    @NotNull
    static List<PsiFile> includers(@NotNull PsiFile header) {
        VirtualFile vf = header.getVirtualFile();
        if (vf == null || !"mqh".equalsIgnoreCase(vf.getExtension())) {
            return List.of();
        }
        Project project = header.getProject();
        return CachedValuesManager.getCachedValue(header, () -> {
            List<PsiFile> out = new java.util.ArrayList<>();
            GlobalSearchScope scope = GlobalSearchScope.projectScope(project);
            Set<VirtualFile> roots = new HashSet<>(FileTypeIndex.getFiles(MQL5FileType.INSTANCE, scope));
            roots.addAll(FileTypeIndex.getFiles(MQL4FileType.INSTANCE, scope));
            PsiManager manager = PsiManager.getInstance(project);
            for (VirtualFile root : roots) {
                ProgressManager.checkCanceled();
                String ext = root.getExtension();
                if (!"mq5".equalsIgnoreCase(ext) && !"mq4".equalsIgnoreCase(ext)) {
                    continue;
                }
                PsiFile rootFile = manager.findFile(root);
                if (rootFile != null && closureFiles(rootFile).contains(header)) {
                    out.add(rootFile);
                }
            }
            return CachedValueProvider.Result.create(out, PsiModificationTracker.getInstance(project),
                    VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS);
        });
    }
}
