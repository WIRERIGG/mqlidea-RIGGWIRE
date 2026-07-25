/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.intellij.psi.util.PsiTreeUtil;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.index.MQL4ClassNameIndex;
import com.limemojito.oss.mql.index.MQL4FunctionNameIndex;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4File;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * Resolution order per REVAMP_PLAN.md #3b:
 * <ol>
 *     <li>lexical scope walk (locals + parameters, up through enclosing {} blocks/function)</li>
 *     <li>same file + #include closure (functions, classes, enums, global/field variables)</li>
 *     <li>project-wide stub indexes (functions, classes) -- dialect filtering left as TODO</li>
 * </ol>
 * Built-ins are deliberately NOT resolved to PSI here (that needs the synthetic-PSI std-lib
 * catalog planned for Phase 6); {@link MqlReference#isSoft()} keeps them from ever being treated
 * as an error once an "unresolved reference" check exists.
 */
public final class MqlResolveUtil {

    private MqlResolveUtil() {
    }

    @NotNull
    public static List<PsiElement> resolve(@NotNull PsiElement identifier, @NotNull String name) {
        PsiElement local = resolveLocal(identifier, name);
        if (local != null) {
            List<PsiElement> single = new ArrayList<>(1);
            single.add(local);
            return single;
        }
        return resolveNonLocal(identifier, name);
    }

    // ---- Tier 1: lexical scope (locals + parameters) --------------------------------------

    private static PsiElement resolveLocal(@NotNull PsiElement identifier, @NotNull String name) {
        PsiElement parent = identifier.getParent();
        while (parent != null) {
            if (parent instanceof MQL4FunctionElement) {
                PsiElement match = findParam((MQL4FunctionElement) parent, name);
                if (match != null) {
                    return match;
                }
            } else if (MqlPsiUtil.isCodeBlock(parent)) {
                PsiElement match = findVarInBlockChildren(parent.getNode(), name);
                if (match != null) {
                    return match;
                }
            }
            parent = parent.getParent();
        }
        return null;
    }

    private static PsiElement findParam(@NotNull MQL4FunctionElement function, @NotNull String name) {
        ASTNode argsList = function.getNode().findChildByType(MQL4Elements.FUNCTION_ARGS_LIST);
        if (argsList == null) {
            return null;
        }
        for (ASTNode arg = argsList.getFirstChildNode(); arg != null; arg = arg.getTreeNext()) {
            if (arg.getElementType() == MQL4Elements.FUNCTION_ARG) {
                PsiElement psi = arg.getPsi();
                if (psi instanceof com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement
                        && name.equals(((com.limemojito.oss.mql.psi.impl.MQL4FunctionArgElement) psi).getName())) {
                    return psi;
                }
            }
        }
        return null;
    }

    /**
     * Scans the DIRECT children of a code block only (never recursing into nested blocks --
     * those are separate nested scopes reached, if at all, by further steps of the caller's
     * parent-chain walk) for a VAR_DECLARATION_STATEMENT defining {@code name}.
     */
    private static PsiElement findVarInBlockChildren(@NotNull ASTNode blockNode, @NotNull String name) {
        for (ASTNode child = blockNode.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                PsiElement match = findVarDefinitionInDeclaration(child, name);
                if (match != null) {
                    return match;
                }
            }
        }
        return null;
    }

    /** The VAR_DEFINITION named {@code name} inside a VAR_DECLARATION_STATEMENT, or null. */
    private static PsiElement findVarDefinitionInDeclaration(@NotNull ASTNode varDeclarationStatement, @NotNull String name) {
        ASTNode list = varDeclarationStatement.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (list == null) {
            return null;
        }
        for (ASTNode def = list.getFirstChildNode(); def != null; def = def.getTreeNext()) {
            if (def.getElementType() == MQL4Elements.VAR_DEFINITION) {
                PsiElement psi = def.getPsi();
                if (psi instanceof com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement varDef
                        && name.equals(varDef.getName())) {
                    return psi;
                }
            }
        }
        return null;
    }

    // ---- Tier 2/3: same file + #include closure, then project-wide indexes ----------------

    @NotNull
    private static List<PsiElement> resolveNonLocal(@NotNull PsiElement identifier, @NotNull String name) {
        PsiFile file = identifier.getContainingFile();
        if (!(file instanceof MQL4File)) {
            return java.util.Collections.emptyList();
        }
        Set<PsiFile> closure = includeClosure(file);
        List<PsiElement> hits = new ArrayList<>();
        Project project = identifier.getProject();

        GlobalSearchScope closureScope = closureScope(project, closure);
        if (closureScope != null) {
            collectIndexed(name, project, closureScope, hits);
        }
        for (PsiFile f : closure) {
            List<PsiElement> enums = enumsByName(f).get(name);
            if (enums != null) {
                hits.addAll(enums);
            }
        }
        if (hits.isEmpty()) {
            for (PsiFile f : closure) {
                PsiElement v = topLevelVarsByName(f).get(name);
                if (v != null) {
                    hits.add(v);
                }
            }
        }
        if (!hits.isEmpty()) {
            return hits;
        }

        // Skip the project-wide allScope stub query for documented built-ins (Print, ArraySize, …) —
        // the common case in real EA code. They're never project symbols, so the query always misses;
        // leaving them unresolved (soft) avoids an index lookup per built-in identifier per resolve.
        if (com.limemojito.oss.mql.doc.MQL4DocumentationProvider.getEntryByText(name) != null) {
            return hits;
        }

        // Tier 3: project-wide stub indexes (functions/classes only survive as stubs today; a
        // project-wide global-variable index, sketched in REVAMP_PLAN.md #3b, is a TODO).
        collectIndexed(name, project, GlobalSearchScope.allScope(project), hits);
        return hits;
    }

    // ---- Phase 5: member-access support (fields + methods inside a class, incl. inheritance) ------

    /** Bounds the base-class walk so a (malformed) inheritance cycle can never loop forever. */
    private static final int MAX_INHERITANCE_DEPTH = 5;

    /**
     * Fields and methods named {@code name} declared directly in {@code cls}'s inner block. May
     * return several PSI elements (overloaded methods); a field and a method never collide by MQL
     * rules but both are returned if present so the caller can poly-resolve rather than crash.
     */
    @NotNull
    public static List<PsiElement> resolveMemberInClass(@NotNull MQL4ClassElement cls, @NotNull String name) {
        List<PsiElement> out = new ArrayList<>();
        collectMembersNamed(cls, name, out);
        return out;
    }

    /**
     * As {@link #resolveMemberInClass} but, when the member is not declared on {@code cls} itself,
     * walks up the {@code CLASS_INHERITANCE_LIST} base classes (resolved via the class index),
     * depth- and visited-bounded so multi-level inheritance works without looping.
     */
    @NotNull
    public static List<PsiElement> resolveMemberInClassHierarchy(@NotNull MQL4ClassElement cls, @NotNull String name) {
        List<PsiElement> out = new ArrayList<>();
        collectMemberInHierarchy(cls, name, out, new java.util.HashSet<>(), 0);
        return out;
    }

    private static void collectMemberInHierarchy(@NotNull MQL4ClassElement cls,
                                                 @NotNull String name,
                                                 @NotNull List<PsiElement> out,
                                                 @NotNull Set<MQL4ClassElement> visited,
                                                 int depth) {
        if (depth > MAX_INHERITANCE_DEPTH || !visited.add(cls)) {
            return;
        }
        collectMembersNamed(cls, name, out);
        if (!out.isEmpty()) {
            return; // nearest declaration wins
        }
        for (String baseName : baseClassNames(cls)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            MQL4ClassElement base = findClassByName(baseName, cls.getProject());
            if (base != null) {
                collectMemberInHierarchy(base, name, out, visited, depth + 1);
                if (!out.isEmpty()) {
                    return;
                }
            }
        }
    }

    private static void collectMembersNamed(@NotNull MQL4ClassElement cls, @NotNull String name, @NotNull List<PsiElement> out) {
        ASTNode inner = cls.getInnerBlockNode();
        if (inner == null) {
            return;
        }
        for (ASTNode child = inner.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            if (child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                PsiElement field = findVarDefinitionInDeclaration(child, name);
                if (field != null) {
                    out.add(field);
                }
            } else {
                PsiElement psi = child.getPsi();
                if (psi instanceof MQL4FunctionElement fn && name.equals(fn.getFunctionName())) {
                    out.add(fn);
                }
            }
        }
    }

    /**
     * Every member (fields + methods) of {@code cls} and its (bounded) base classes -- used by
     * dot-completion. Order is this-class-first, then bases, so nearer members rank ahead.
     */
    @NotNull
    public static List<PsiElement> collectAllMembers(@NotNull MQL4ClassElement cls) {
        List<PsiElement> out = new ArrayList<>();
        collectAllMembers(cls, out, new java.util.HashSet<>(), 0);
        return out;
    }

    private static void collectAllMembers(@NotNull MQL4ClassElement cls,
                                          @NotNull List<PsiElement> out,
                                          @NotNull Set<MQL4ClassElement> visited,
                                          int depth) {
        if (depth > MAX_INHERITANCE_DEPTH || !visited.add(cls)) {
            return;
        }
        ASTNode inner = cls.getInnerBlockNode();
        if (inner != null) {
            for (ASTNode child = inner.getFirstChildNode(); child != null; child = child.getTreeNext()) {
                if (child.getElementType() == MQL4Elements.VAR_DECLARATION_STATEMENT) {
                    ASTNode list = child.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
                    if (list != null) {
                        for (ASTNode def = list.getFirstChildNode(); def != null; def = def.getTreeNext()) {
                            if (def.getElementType() == MQL4Elements.VAR_DEFINITION) {
                                out.add(def.getPsi());
                            }
                        }
                    }
                } else {
                    PsiElement psi = child.getPsi();
                    if (psi instanceof MQL4FunctionElement) {
                        out.add(psi);
                    }
                }
            }
        }
        for (String baseName : baseClassNames(cls)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            MQL4ClassElement base = findClassByName(baseName, cls.getProject());
            if (base != null) {
                collectAllMembers(base, out, visited, depth + 1);
            }
        }
    }

    /**
     * The direct base classes of {@code cls} that resolve to a project class (Phase 6a: Go to
     * Super). Order mirrors the inheritance list; unresolvable base names are skipped.
     */
    @NotNull
    public static List<MQL4ClassElement> directBaseClasses(@NotNull MQL4ClassElement cls) {
        List<MQL4ClassElement> out = new ArrayList<>();
        for (String name : baseClassNames(cls)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            MQL4ClassElement base = findClassByName(name, cls.getProject());
            if (base != null) {
                out.add(base);
            }
        }
        return out;
    }

    /**
     * The overridden member(s) named {@code name} declared in a base class of {@code cls} (Phase 6a:
     * Go to Super for an overriding method). Searches only the base hierarchy -- never {@code cls}
     * itself -- so an overriding method jumps to the declaration it overrides, not to itself.
     */
    @NotNull
    public static List<PsiElement> findSuperMembers(@NotNull MQL4ClassElement cls, @NotNull String name) {
        List<PsiElement> out = new ArrayList<>();
        for (MQL4ClassElement base : directBaseClasses(cls)) {
            out.addAll(resolveMemberInClassHierarchy(base, name));
            if (!out.isEmpty()) {
                return out;
            }
        }
        return out;
    }

    /** Base-class type names read from {@code cls}'s CLASS_INHERITANCE_LIST / CLASS_INHERITANCE_ITEM. */
    @NotNull
    private static List<String> baseClassNames(@NotNull MQL4ClassElement cls) {
        ASTNode list = cls.getNode().findChildByType(MQL4Elements.CLASS_INHERITANCE_LIST);
        if (list == null) {
            return java.util.Collections.emptyList();
        }
        List<String> names = new ArrayList<>();
        for (ASTNode item = list.getFirstChildNode(); item != null; item = item.getTreeNext()) {
            if (item.getElementType() == MQL4Elements.CLASS_INHERITANCE_ITEM) {
                ASTNode id = item.findChildByType(MQL4Elements.IDENTIFIER);
                if (id != null) {
                    names.add(id.getText());
                }
            }
        }
        return names;
    }

    /** The single project/closure class named {@code name}, or {@code null} (also null in dumb mode). */
    @org.jetbrains.annotations.Nullable
    public static MQL4ClassElement findClassByName(@NotNull String name, @NotNull Project project) {
        if (com.intellij.openapi.project.DumbService.isDumb(project)) {
            return null;
        }
        for (MQL4ClassElement c : MQL4ClassNameIndex.getInstance().get(name, project, GlobalSearchScope.allScope(project))) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            if (name.equals(c.getTypeName())) {
                return c;
            }
        }
        return null;
    }

    private static void collectIndexed(@NotNull String name, @NotNull Project project, @NotNull GlobalSearchScope scope, @NotNull List<PsiElement> out) {
        for (MQL4FunctionElement f : MQL4FunctionNameIndex.getInstance().get(name, project, scope)) {
            if (name.equals(f.getFunctionName())) {
                out.add(f);
            }
        }
        for (MQL4ClassElement c : MQL4ClassNameIndex.getInstance().get(name, project, scope)) {
            if (name.equals(c.getTypeName())) {
                out.add(c);
            }
        }
    }

    /**
     * Per-file map of enum type name → enum element(s), cached until the file itself changes.
     * Replaces a full {@code findChildrenOfType} tree walk of every closure file on every resolve.
     */
    @NotNull
    private static Map<String, List<PsiElement>> enumsByName(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            Map<String, List<PsiElement>> map = new HashMap<>();
            for (MQL4EnumElement e : PsiTreeUtil.findChildrenOfType(file, MQL4EnumElement.class)) {
                String n = e.getName();
                if (n != null) {
                    map.computeIfAbsent(n, k -> new ArrayList<>()).add(e);
                }
            }
            return CachedValueProvider.Result.create(map, file);
        });
    }

    /**
     * Per-file map of top-level variable name → its (first) definition, cached until the file changes.
     * Replaces a per-name top-level scan of every closure file on every resolve.
     */
    @NotNull
    private static Map<String, PsiElement> topLevelVarsByName(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            Map<String, PsiElement> map = new HashMap<>();
            ASTNode fileNode = file.getNode();
            if (fileNode != null) {
                for (ASTNode child = fileNode.getFirstChildNode(); child != null; child = child.getTreeNext()) {
                    if (child.getElementType() != MQL4Elements.VAR_DECLARATION_STATEMENT) {
                        continue;
                    }
                    ASTNode list = child.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
                    if (list == null) {
                        continue;
                    }
                    for (ASTNode def = list.getFirstChildNode(); def != null; def = def.getTreeNext()) {
                        if (def.getElementType() != MQL4Elements.VAR_DEFINITION) {
                            continue;
                        }
                        PsiElement psi = def.getPsi();
                        if (psi instanceof com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement varDef) {
                            String n = varDef.getName();
                            if (n != null) {
                                map.putIfAbsent(n, psi);
                            }
                        }
                    }
                }
            }
            return CachedValueProvider.Result.create(map, file);
        });
    }

    @org.jetbrains.annotations.Nullable
    private static GlobalSearchScope closureScope(@NotNull Project project, @NotNull Set<PsiFile> closure) {
        List<VirtualFile> files = new ArrayList<>();
        for (PsiFile f : closure) {
            VirtualFile vf = f.getVirtualFile();
            if (vf != null) {
                files.add(vf);
            }
        }
        return files.isEmpty() ? null : GlobalSearchScope.filesScope(project, files);
    }

    /**
     * Every file reachable from {@code root} by following #include chains, transitively, with a
     * visited-set cycle guard. Always includes {@code root} itself.
     *
     * <p>P1.3: cached on {@code root} (invalidated on any PSI change) so the multi-file #include BFS
     * isn't rebuilt on every identifier Ctrl-click/highlight/annotation pass — the biggest resolve
     * cost on projects that include the MQL5 Standard Library.
     */
    @NotNull
    private static Set<PsiFile> includeClosure(@NotNull PsiFile root) {
        return CachedValuesManager.getCachedValue(root, () ->
                CachedValueProvider.Result.create(computeIncludeClosure(root), PsiModificationTracker.MODIFICATION_COUNT));
    }

    @NotNull
    private static Set<PsiFile> computeIncludeClosure(@NotNull PsiFile root) {
        Set<PsiFile> visited = new LinkedHashSet<>();
        Deque<PsiFile> queue = new ArrayDeque<>();
        visited.add(root);
        queue.add(root);
        while (!queue.isEmpty()) {
            PsiFile current = queue.poll();
            for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(current, MQL4PreprocessorIncludeBlock.class)) {
                PsiFile target = include.resolveIncludedFile();
                if (target != null && visited.add(target)) {
                    queue.add(target);
                }
            }
        }
        return visited;
    }
}
