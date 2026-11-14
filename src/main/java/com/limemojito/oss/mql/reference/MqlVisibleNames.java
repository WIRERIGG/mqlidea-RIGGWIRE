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
 *     <li>any project file, through the stub indexes.</li>
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

    private MqlVisibleNames() {
    }

    public static boolean isDeclared(@NotNull String name, @NotNull PsiFile file) {
        if (closureNames(file).contains(name)) {
            return true;
        }
        for (PsiFile includer : includers(file)) {
            if (closureNames(includer).contains(name)) {
                return true;
            }
        }
        Project project = file.getProject();
        GlobalSearchScope scope = GlobalSearchScope.allScope(project);
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
        return CachedValuesManager.getCachedValue(file, () -> {
            Set<String> names = new HashSet<>();
            for (PsiFile current : closureFiles(file)) {
                for (PsiElement declaration : PsiTreeUtil.findChildrenOfAnyType(current, MQL4FunctionElement.class,
                        MQL4ClassElement.class, MQL4VarDefinitionElement.class, MQL4DefineElement.class,
                        MQL4TypedefElement.class, MQL4EnumElement.class, MQL4EnumFieldElement.class)) {
                    ProgressManager.checkCanceled();
                    String name = ((PsiNamedElement) declaration).getName();
                    if (name != null) {
                        names.add(name);
                    }
                }
            }
            return CachedValueProvider.Result.create(names, PsiModificationTracker.getInstance(file.getProject()),
                    VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS);
        });
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
    private static List<PsiFile> includers(@NotNull PsiFile header) {
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
