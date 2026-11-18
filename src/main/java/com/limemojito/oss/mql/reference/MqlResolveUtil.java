/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.reference;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.roots.ProjectRootModificationTracker;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.openapi.vfs.VirtualFileManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.GlobalSearchScope;
import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.intellij.psi.util.PsiTreeUtil;
import org.jetbrains.annotations.NotNull;
import com.limemojito.oss.mql.index.MQL4ClassNameIndex;
import com.limemojito.oss.mql.index.MQL4DefineNameIndex;
import com.limemojito.oss.mql.index.MQL4TypedefNameIndex;
import com.limemojito.oss.mql.index.MQL4EnumFieldNameIndex;
import com.limemojito.oss.mql.index.MQL4EnumNameIndex;
import com.limemojito.oss.mql.index.MQL4FunctionNameIndex;
import com.limemojito.oss.mql.index.MQL4GlobalVarNameIndex;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4File;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4DefineElement;
import com.limemojito.oss.mql.psi.impl.MQL4NamespaceElement;
import com.limemojito.oss.mql.psi.impl.MQL4TypedefElement;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumElement;
import com.limemojito.oss.mql.psi.impl.MQL4EnumFieldElement;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement;

import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Resolution order per REVAMP_PLAN.md #3b:
 * <ol>
 *     <li>lexical scope walk (locals + parameters, up through enclosing {} blocks/function)</li>
 *     <li>same file + #include closure (functions, classes, enums, global/field variables); for a
 *     header, then the closures of the files that include it</li>
 *     <li>project-wide stub indexes (functions, classes) -- dialect filtering left as TODO</li>
 * </ol>
 * Built-ins are deliberately NOT resolved to PSI here (that needs the synthetic-PSI std-lib
 * catalog planned for Phase 6); {@link MqlReference#isSoft()} keeps them from ever being treated
 * as an error once an "unresolved reference" check exists.
 */
public final class MqlResolveUtil {

    private MqlResolveUtil() {
    }

    /**
     * A template parameter of a declaration enclosing {@code identifier}: each enclosing element
     * whose previous sibling is a {@code template<...>} header (a class and its members, a function,
     * an out-of-line member definition) offers that header's parameters, innermost first, so a
     * member template's own {@code T} hides its class's. A parameter wins over any global name.
     */
    @org.jetbrains.annotations.Nullable
    public static com.limemojito.oss.mql.psi.impl.MQL4TemplateParameterElement resolveTemplateParameter(
            @NotNull PsiElement identifier, @NotNull String name) {
        for (PsiElement e = identifier; e != null && !(e instanceof PsiFile); e = e.getParent()) {
            PsiElement header = templateHeaderBefore(e);
            if (header == null) {
                continue;
            }
            for (PsiElement child = header.getFirstChild(); child != null; child = child.getNextSibling()) {
                if (child instanceof com.limemojito.oss.mql.psi.impl.MQL4TemplateParameterElement parameter
                        && name.equals(parameter.getName())) {
                    return parameter;
                }
            }
        }
        return null;
    }

    /**
     * The template header that heads the declaration {@code e} belongs to, looking back past what can
     * sit between them: modifiers ({@code static}, {@code virtual}, {@code const}) and, when a body
     * parsed apart from its signature, that signature. Stops at a {@code ;}, {@code }} or {@code :}
     * that ends an earlier declaration or an access label.
     */
    @org.jetbrains.annotations.Nullable
    private static PsiElement templateHeaderBefore(@NotNull PsiElement e) {
        PsiElement s = PsiTreeUtil.skipWhitespacesAndCommentsBackward(e);
        for (int i = 0; s != null && i < 8; i++, s = PsiTreeUtil.skipWhitespacesAndCommentsBackward(s)) {
            if (s.getNode().getElementType() == MQL4Elements.TEMPLATE_HEADER) {
                return s;
            }
            String text = s.getText();
            if (text.isEmpty() || text.endsWith(";") || text.endsWith("}") || text.endsWith(":")) {
                return null;
            }
        }
        return null;
    }

    @NotNull
    public static List<PsiElement> resolve(@NotNull PsiElement identifier, @NotNull String name) {
        if (isMacroParameter(identifier, name)) {
            return new ArrayList<>(); // `a` in `#define MAX(a,b) ...` names no declaration
        }
        PsiElement prev = PsiTreeUtil.prevVisibleLeaf(identifier);
        if (prev != null && prev.getNode().getElementType() == MQL4Elements.COLON_COLON) {
            List<PsiElement> qualified = resolveQualified(identifier, name, prev);
            if (qualified != null) {
                return qualified;
            }
        }
        List<PsiElement> offsetofMember = resolveOffsetofMember(identifier, name, prev);
        if (offsetofMember != null) {
            return offsetofMember;
        }
        if (prev == null || prev.getNode().getElementType() != MQL4Elements.DOT) {
            PsiElement parameter = resolveTemplateParameter(identifier, name);
            if (parameter != null) {
                List<PsiElement> single = new ArrayList<>(1);
                single.add(parameter);
                return single;
            }
        }
        PsiElement local = resolveLocal(identifier, name);
        if (local != null) {
            List<PsiElement> single = new ArrayList<>(1);
            single.add(local);
            return single;
        }
        // Enclosing-class member: a BARE use inside a method (`return value;` / `Helper();`) binds to
        // the class's own field/method (inherited too) before any global — otherwise a field rename
        // would update obj.field/this.field but silently miss these bare in-method uses (broken code).
        PsiElement member = resolveEnclosingClassMember(identifier, name);
        if (member != null) {
            List<PsiElement> single = new ArrayList<>(1);
            single.add(member);
            return single;
        }
        return resolveNonLocal(identifier, name);
    }

    @org.jetbrains.annotations.Nullable
    private static PsiElement resolveEnclosingClassMember(@NotNull PsiElement identifier, @NotNull String name) {
        MQL4ClassElement cls = enclosingClass(identifier);
        if (cls == null) {
            return null;
        }
        List<PsiElement> members = resolveMemberInClassHierarchy(cls, name);
        return members.isEmpty() ? null : members.get(0);
    }

    /**
     * The class whose members a bare name in {@code element} sees: the class whose body contains it,
     * or {@code X} for a body or initializer list of an out-of-line {@code X::Method(...)} (OOP-1).
     * Null elsewhere, including an out-of-line method's return and argument types.
     */
    @org.jetbrains.annotations.Nullable
    public static MQL4ClassElement enclosingClass(@NotNull PsiElement element) {
        MQL4ClassElement cls = PsiTreeUtil.getParentOfType(element, MQL4ClassElement.class);
        if (cls != null) {
            ASTNode inner = cls.getInnerBlockNode();
            return inner != null && PsiTreeUtil.isAncestor(inner.getPsi(), element, false) ? cls : null;
        }
        MQL4FunctionElement function = PsiTreeUtil.getParentOfType(element, MQL4FunctionElement.class);
        String className = function == null ? null : MqlPsiUtil.outOfLineClassName(function);
        if (className == null || !MqlPsiUtil.isAfterArguments(function, element)) {
            return null;
        }
        return findClassByName(className, element.getProject(), element);
    }

    /**
     * {@code ::name} and {@code X::name}. A bare {@code ::name} skips locals and members for the
     * file-level declaration (V-2). {@code X::name} looks in class {@code X} (its members, inherited
     * too: {@code CBase::Method()}, {@code int CCounter::s_total = 0;}) or namespace {@code X}. Null
     * when {@code X} is neither, so an enum constant ({@code ENUM_X::VALUE}) resolves as before.
     */
    @org.jetbrains.annotations.Nullable
    private static List<PsiElement> resolveQualified(@NotNull PsiElement identifier, @NotNull String name, @NotNull PsiElement colons) {
        PsiElement qualifier = PsiTreeUtil.prevVisibleLeaf(colons);
        if (qualifier == null || qualifier.getNode().getElementType() != MQL4Elements.IDENTIFIER) {
            return resolveNonLocal(identifier, name);
        }
        MQL4ClassElement cls = findClassByName(qualifier.getText(), identifier.getProject(), identifier);
        if (cls != null) {
            List<PsiElement> members = resolveMemberInClassHierarchy(cls, name);
            if (!members.isEmpty()) {
                return members;
            }
        }
        List<PsiElement> inNamespace = new ArrayList<>();
        for (PsiElement hit : resolveNonLocal(identifier, name)) {
            MQL4NamespaceElement ns = PsiTreeUtil.getParentOfType(hit, MQL4NamespaceElement.class);
            if (ns != null && qualifier.getText().equals(ns.getName())
                    || qualifier.getText().equalsIgnoreCase(importModuleOf(hit))) {
                inNamespace.add(hit); // Ns::Name, or kernel32::GetLastError after #import "kernel32.dll"
            }
        }
        return inNamespace.isEmpty() ? null : inNamespace;
    }

    /**
     * The module name a declaration inside {@code #import "path\\kernel32.dll"} is called through
     * ({@code kernel32::GetLastError()}): the file name without folder or extension; null outside an
     * import. The parser leaves {@code #import} lines as tokens, so this looks back from the
     * declaration's file-level element to the nearest {@code #import}: one with a path opens the
     * block, a bare one closes it.
     */
    @org.jetbrains.annotations.Nullable
    public static String importModuleOf(@NotNull PsiElement declaration) {
        PsiElement top = declaration;
        while (top.getParent() != null && !(top.getParent() instanceof PsiFile)) {
            top = top.getParent();
        }
        for (PsiElement p = top.getPrevSibling(); p != null; p = p.getPrevSibling()) {
            if (p.getNode().getElementType() == MQL4Elements.IMPORT_PP_KEYWORD) {
                PsiElement path = PsiTreeUtil.nextVisibleLeaf(p);
                return path != null && path.getNode().getElementType() == MQL4Elements.STRING_LITERAL
                        && path.getTextOffset() < top.getTextOffset() ? moduleName(path.getText()) : null;
            }
        }
        return null;
    }

    /** {@code "..\\Libraries\\Foo.ex5"} -> {@code Foo}. */
    @NotNull
    static String moduleName(@NotNull String literal) {
        String s = literal.replace("\"", "");
        s = s.substring(Math.max(s.lastIndexOf('\\'), s.lastIndexOf('/')) + 1);
        int dot = s.lastIndexOf('.');
        return dot > 0 ? s.substring(0, dot) : s;
    }

    /** Module names ({@code kernel32}) of every {@code #import} in {@code file}'s include closure. */
    @NotNull
    public static Set<String> importModulesVisibleFrom(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            Set<String> modules = new java.util.TreeSet<>(String.CASE_INSENSITIVE_ORDER);
            for (PsiFile f : MqlVisibleNames.includeClosure(file)) {
                for (PsiElement e = f.getFirstChild(); e != null; e = e.getNextSibling()) {
                    if (e.getNode().getElementType() == MQL4Elements.IMPORT_PP_KEYWORD) {
                        PsiElement path = PsiTreeUtil.nextVisibleLeaf(e);
                        if (path != null && path.getNode().getElementType() == MQL4Elements.STRING_LITERAL) {
                            modules.add(moduleName(path.getText()));
                        }
                    }
                }
            }
            return CachedValueProvider.Result.create(modules, PsiModificationTracker.MODIFICATION_COUNT);
        });
    }

    /** {@code m} in {@code offsetof(S, m)}: the member of struct {@code S}. */
    @org.jetbrains.annotations.Nullable
    private static List<PsiElement> resolveOffsetofMember(@NotNull PsiElement identifier, @NotNull String name,
                                                          @org.jetbrains.annotations.Nullable PsiElement comma) {
        if (comma == null || comma.getNode().getElementType() != MQL4Elements.COMMA) {
            return null;
        }
        PsiElement type = PsiTreeUtil.prevVisibleLeaf(comma);
        PsiElement open = type == null ? null : PsiTreeUtil.prevVisibleLeaf(type);
        PsiElement keyword = open == null ? null : PsiTreeUtil.prevVisibleLeaf(open);
        if (keyword == null || open.getNode().getElementType() != MQL4Elements.L_ROUND_BRACKET
                || type.getNode().getElementType() != MQL4Elements.IDENTIFIER || !"offsetof".equals(keyword.getText())) {
            return null;
        }
        MQL4ClassElement cls = findClassByName(type.getText(), identifier.getProject(), identifier);
        return cls == null ? null : resolveMemberInClassHierarchy(cls, name);
    }

    private static boolean isMacroParameter(@NotNull PsiElement identifier, @NotNull String name) {
        MQL4DefineElement define = PsiTreeUtil.getParentOfType(identifier, MQL4DefineElement.class);
        return define != null && define.getParameterNames().contains(name);
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
            } else if (MqlPsiUtil.forHeaderOf(parent) != null) {
                // for(int i=0; ...): the init-clause declaration is scoped to the header and body
                PsiElement match = findVarInBlockChildren(MqlPsiUtil.forHeaderOf(parent), name);
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
                if (match != null && !isMultiplication(child)) {
                    return match;
                }
            }
        }
        return null;
    }

    /** Statements being checked by {@link #isMultiplication}, so {@code a * a;} can't recurse. */
    private static final ThreadLocal<Set<ASTNode>> MULTIPLICATION_CHECKS = ThreadLocal.withInitial(java.util.HashSet::new);

    /**
     * True for {@code a * b;} where {@code a} is a variable in scope: the parser reads it as a pointer
     * declaration of {@code b} (it can't tell types from variables), but it is a multiplication
     * (MetaEditor's warning 95), so it declares nothing. A class named {@code a} keeps the declaration.
     */
    private static boolean isMultiplication(@NotNull ASTNode declaration) {
        ASTNode type = declaration.getFirstChildNode();
        ASTNode star = type == null ? null : type.getTreeNext();
        while (star != null && MQL4TokenSets.COMMENTS_OR_WS.contains(star.getElementType())) {
            star = star.getTreeNext();
        }
        if (type == null || type.getElementType() != MQL4Elements.IDENTIFIER
                || star == null || star.getElementType() != MQL4Elements.MUL) {
            return false;
        }
        ASTNode list = declaration.findChildByType(MQL4Elements.VAR_DEFINITION_LIST);
        if (list == null || list.findChildByType(MQL4Elements.COMMA) != null
                || declaration.findChildByType(MQL4Elements.EQ) != null
                || (list.findChildByType(MQL4Elements.VAR_DEFINITION) != null
                && list.findChildByType(MQL4Elements.VAR_DEFINITION).findChildByType(MQL4Elements.EQ) != null)) {
            return false;
        }
        Set<ASTNode> inProgress = MULTIPLICATION_CHECKS.get();
        if (!inProgress.add(declaration)) {
            return false;
        }
        try {
            PsiElement typeLeaf = type.getPsi();
            return resolveLocal(typeLeaf, type.getText()) != null
                    && findClassByName(type.getText(), typeLeaf.getProject(), typeLeaf) == null;
        } finally {
            inProgress.remove(declaration);
        }
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
        List<PsiElement> hits = new ArrayList<>();
        Project project = identifier.getProject();

        // Tier 2: same file + #include closure. All three symbol kinds (functions/classes, then
        // enum types, then -- only if nothing matched -- global variables) are resolved by querying
        // the stub indexes over the ALREADY-COMPUTED closure scope, replacing the former full-AST
        // walk of every closure file. The category order (and the global-only-if-empty gate) matches
        // the previous closure loops, and this whole block still sits BEFORE the built-in-doc
        // short-circuit below so a project symbol shadowing a built-in name still wins.
        GlobalSearchScope closureScope = closureScopeFor(file);
        if (closureScope != null) {
            collectInClosureScope(name, project, closureScope, hits);
            // A header is compiled inside each .mq5/.mq4 that includes it, so it also sees what
            // that includer declared or included before it (sibling headers, the EA's globals).
            if (hits.isEmpty()) {
                GlobalSearchScope includerScope = includerScopeFor(file);
                if (includerScope != null) {
                    collectInClosureScope(name, project, includerScope, hits);
                }
            }
        } else {
            // Non-physical PSI (intention-preview copies, code fragments) has no VirtualFile-backed
            // closure scope, so the stub indexes can't serve it. Fall back to the exact AST walk the
            // old code ran unconditionally, over this file's #include closure, so enum/global
            // resolution keeps working in previews. (Functions/classes were index-only even in the
            // old code, so -- as before -- they aren't resolved here and fall through to tier 3.)
            Set<PsiFile> closure = includeClosure(file);
            for (PsiFile f : closure) {
                for (MQL4EnumElement e : PsiTreeUtil.findChildrenOfType(f, MQL4EnumElement.class)) {
                    com.intellij.openapi.progress.ProgressManager.checkCanceled();
                    if (name.equals(e.getName())) {
                        hits.add(e);
                    }
                }
            }
            if (hits.isEmpty()) {
                for (PsiFile f : closure) {
                    ASTNode fNode = f.getNode();
                    PsiElement v = fNode == null ? null : findVarInBlockChildren(fNode, name);
                    if (v != null) {
                        hits.add(v);
                    }
                }
            }
            if (hits.isEmpty()) {
                for (PsiFile f : closure) {
                    collectFirstPerFile(PsiTreeUtil.findChildrenOfType(f, MQL4DefineElement.class), name, hits);
                }
            }
            // Enum-constant tier (last), mirroring the index path above: scan the closure enums'
            // fields directly since the stub index can't serve non-physical PSI.
            if (hits.isEmpty()) {
                for (PsiFile f : closure) {
                    for (MQL4EnumElement e : PsiTreeUtil.findChildrenOfType(f, MQL4EnumElement.class)) {
                        com.intellij.openapi.progress.ProgressManager.checkCanceled();
                        collectEnumFieldsNamed(e, name, hits);
                    }
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
        // The project first: the indexed MetaTrader Include folders can hold stale copies of its headers.
        collectIndexed(name, project, GlobalSearchScope.projectScope(project), hits);
        if (hits.isEmpty()) {
            collectIndexed(name, project, GlobalSearchScope.allScope(project), hits);
        }
        if (hits.isEmpty()) {
            collectFirstPerFile(MqlScopes.projectFirst(MQL4DefineNameIndex.getInstance().getKey(), name, project, MQL4DefineElement.class), name, hits);
        }
        return hits;
    }

    /** The closure tiers of {@link #resolveNonLocal}, in order, over one closure scope. */
    private static void collectInClosureScope(@NotNull String name, @NotNull Project project,
                                              @NotNull GlobalSearchScope scope, @NotNull List<PsiElement> hits) {
        collectIndexed(name, project, scope, hits);
        for (MQL4EnumElement e : MQL4EnumNameIndex.getInstance().getElements(name, project, scope)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            if (name.equals(e.getName())) {
                hits.add(e);
            }
        }
        if (hits.isEmpty()) {
            collectClosureGlobals(name, project, scope, hits);
        }
        if (hits.isEmpty()) {
            collectFirstPerFile(MQL4DefineNameIndex.getInstance().getElements(name, project, scope), name, hits);
        }
        // Enum-constant tier (LAST closure tier): a bare use of a constant (`RED`, or `Color::RED`
        // whose member leaf is still `RED`) binds to its enum-field declaration. Gated on an empty
        // result so it never overrides a function/class/enum-type/global/local that already claimed
        // the name; poly-resolves if two enums in the closure both declare it (safe, never a pick).
        if (hits.isEmpty()) {
            for (MQL4EnumElement e : MQL4EnumFieldNameIndex.getInstance().getElements(name, project, scope)) {
                com.intellij.openapi.progress.ProgressManager.checkCanceled();
                collectEnumFieldsNamed(e, name, hits);
            }
        }
    }

    /**
     * The document-first declaration named {@code name} per file: {@code #ifdef}/{@code #else}
     * branches often define the same macro twice, and both are one name to the reader.
     */
    private static <T extends PsiElement & com.intellij.psi.PsiNamedElement> void collectFirstPerFile(
            @NotNull java.util.Collection<T> candidates, @NotNull String name, @NotNull List<PsiElement> hits) {
        Map<PsiFile, T> firstPerFile = new java.util.LinkedHashMap<>();
        for (T candidate : candidates) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            if (!name.equals(candidate.getName())) {
                continue;
            }
            T prev = firstPerFile.get(candidate.getContainingFile());
            if (prev == null || candidate.getTextOffset() < prev.getTextOffset()) {
                firstPerFile.put(candidate.getContainingFile(), candidate);
            }
        }
        hits.addAll(firstPerFile.values());
    }

    /**
     * Adds the closure's matching top-level global-variable definitions to {@code hits}, keeping at
     * most ONE per file -- the document-first one -- exactly like the old per-file {@code putIfAbsent}
     * map. The stub index yields every top-level definition of {@code name} (including both branches
     * of an {@code #ifdef}/{@code #else} pair, which are direct file children), so without this
     * collapse a same-file duplicate would flip a single navigable target into a poly-resolve chooser.
     */
    private static void collectClosureGlobals(@NotNull String name,
                                              @NotNull Project project,
                                              @NotNull GlobalSearchScope scope,
                                              @NotNull List<PsiElement> hits) {
        Map<PsiFile, MQL4VarDefinitionElement> firstPerFile = new java.util.LinkedHashMap<>();
        for (MQL4VarDefinitionElement v : MQL4GlobalVarNameIndex.getInstance().getElements(name, project, scope)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            if (!name.equals(v.getName())) {
                continue;
            }
            PsiFile vf = v.getContainingFile();
            MQL4VarDefinitionElement prev = firstPerFile.get(vf);
            if (prev == null || v.getTextOffset() < prev.getTextOffset()) {
                firstPerFile.put(vf, v);
            }
        }
        hits.addAll(firstPerFile.values());
    }

    /**
     * Adds every {@code ENUM_FIELD} of {@code enumElement} whose name equals {@code name} to
     * {@code hits}. Scans the ENUM_FIELDS_LIST node children by element type (rather than the PSI
     * {@code getFields()} cast) so a malformed enum containing a stray error element can't throw.
     * An enum normally declares a name at most once, but all matches are added so a duplicate stays a
     * visible poly-resolve rather than an arbitrary pick.
     */
    private static void collectEnumFieldsNamed(@NotNull MQL4EnumElement enumElement, @NotNull String name, @NotNull List<PsiElement> hits) {
        ASTNode list = enumElement.getNode().findChildByType(MQL4Elements.ENUM_FIELDS_LIST);
        if (list == null) {
            return;
        }
        for (ASTNode field = list.getFirstChildNode(); field != null; field = field.getTreeNext()) {
            if (field.getElementType() == MQL4Elements.ENUM_FIELD) {
                PsiElement psi = field.getPsi();
                if (psi instanceof MQL4EnumFieldElement fld && name.equals(fld.getName())) {
                    hits.add(fld);
                }
            }
        }
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
            MQL4ClassElement base = findClassByName(baseName, cls.getProject(), cls);
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
            MQL4ClassElement base = findClassByName(baseName, cls.getProject(), cls);
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
            MQL4ClassElement base = findClassByName(name, cls.getProject(), cls);
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
    public static List<String> baseClassNames(@NotNull MQL4ClassElement cls) {
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

    /**
     * The single class named {@code name} unambiguously visible from {@code context}, or {@code null}.
     * <p>
     * Duplicate class names are common in MQL repos (MQL4/MQL5 dual trees, {@code *_old.mqh} backups,
     * vendored library copies). To avoid a nondeterministic wrong target (and the corrupting rename
     * that follows), this prefers the context's {@code #include} closure — the classes actually
     * reachable from the reference site — exactly like {@link #resolveNonLocal}. It returns a match
     * ONLY when it is unambiguous: the single class in the closure, or (if the closure has none) the
     * single class project-wide. More than one candidate in the chosen scope → {@code null} (no jump,
     * no rename), which is safe: a missed target beats a wrong one. Null in dumb mode.
     */
    @org.jetbrains.annotations.Nullable
    public static MQL4ClassElement findClassByName(@NotNull String name, @NotNull Project project,
                                                   @org.jetbrains.annotations.Nullable PsiElement context) {
        if (com.intellij.openapi.project.DumbService.isDumb(project)) {
            return null;
        }
        if (context != null) {
            PsiFile file = context.getContainingFile();
            if (file != null) {
                // Per-file memo (name -> class), invalidated on any PSI change like includeClosure.
                // Base-class chains and many member accesses re-query the same names from the same
                // file; caching the UNAMBIGUOUS single result avoids re-hitting the class index.
                // Ambiguous (-> null) and genuine misses (-> null) are never stored as positives.
                Map<String, MQL4ClassElement> memo = classResolutionMemo(file);
                MQL4ClassElement cached = memo.get(name);
                if (cached != null) {
                    return cached;
                }
                MQL4ClassElement resolved = resolveClassByName(name, project, file);
                if (resolved != null) {
                    memo.put(name, resolved);
                }
                return resolved;
            }
        }
        // No context / not in the closure: accept only an unambiguous project-wide match.
        return lookupClassProjectFirst(name, project);
    }

    /**
     * The class named {@code name} visible from {@code file}: unambiguous match in the file's
     * #include closure if any; otherwise (closure has none) the unambiguous project-wide match.
     * A closure with several matches yields {@code null} (ambiguous — no fall-through). This is the
     * exact phase-5-hardening semantics {@link #findClassByName} previously inlined.
     */
    @org.jetbrains.annotations.Nullable
    private static MQL4ClassElement resolveClassByName(@NotNull String name, @NotNull Project project, @NotNull PsiFile file) {
        GlobalSearchScope closureScope = closureScopeFor(file);
        if (closureScope != null) {
            ClassLookup inClosure = lookupClassInScope(name, project, closureScope);
            if (inClosure.match != null) {
                return inClosure.match;
            }
            if (inClosure.ambiguous) {
                // Ambiguous within the closure -> don't fall through to an arbitrary project pick.
                return null;
            }
        }
        GlobalSearchScope includerScope = includerScopeFor(file);
        if (includerScope != null) {
            ClassLookup inIncluders = lookupClassInScope(name, project, includerScope);
            if (inIncluders.match != null || inIncluders.ambiguous) {
                return inIncluders.match;
            }
        }
        return lookupClassProjectFirst(name, project);
    }

    /** Backward-compatible context-less lookup — unambiguous project-wide match only. */
    @org.jetbrains.annotations.Nullable
    public static MQL4ClassElement findClassByName(@NotNull String name, @NotNull Project project) {
        return findClassByName(name, project, null);
    }

    /** Tri-state class-index scan result: a unique match, or ambiguous (several), or none. */
    private static final class ClassLookup {
        static final ClassLookup NONE = new ClassLookup(null, false);
        static final ClassLookup AMBIGUOUS = new ClassLookup(null, true);
        @org.jetbrains.annotations.Nullable
        final MQL4ClassElement match;
        final boolean ambiguous;

        private ClassLookup(@org.jetbrains.annotations.Nullable MQL4ClassElement match, boolean ambiguous) {
            this.match = match;
            this.ambiguous = ambiguous;
        }

        static ClassLookup unique(@NotNull MQL4ClassElement match) {
            return new ClassLookup(match, false);
        }
    }

    /** The unambiguous class in the project, or else in the indexed MetaTrader Include folders. */
    @org.jetbrains.annotations.Nullable
    private static MQL4ClassElement lookupClassProjectFirst(@NotNull String name, @NotNull Project project) {
        ClassLookup own = lookupClassInScope(name, project, GlobalSearchScope.projectScope(project));
        if (own.match != null || own.ambiguous) {
            return own.match;
        }
        return lookupClassInScope(name, project, GlobalSearchScope.allScope(project)).match;
    }

    /**
     * ONE pass over the class index for {@code name} in {@code scope}, classifying the result as the
     * unique match, {@link ClassLookup#AMBIGUOUS} (two or more), or {@link ClassLookup#NONE}. Merges
     * what was previously a {@code uniqueClassInScope} query followed by an identical
     * {@code anyClassInScope} query into a single index lookup.
     */
    @NotNull
    private static ClassLookup lookupClassInScope(@NotNull String name, @NotNull Project project, @NotNull GlobalSearchScope scope) {
        // A forward declaration (class CFoo;) names the class but has no members: the definition
        // wins, and only a lone forward declaration is returned as itself.
        MQL4ClassElement found = null;
        MQL4ClassElement forward = null;
        boolean forwardAmbiguous = false;
        for (MQL4ClassElement c : MQL4ClassNameIndex.getInstance().getElements(name, project, scope)) {
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            if (name.equals(c.getTypeName())) {
                if (c.getInnerBlockNode() == null) {
                    forwardAmbiguous |= forward != null;
                    forward = c;
                    continue;
                }
                if (found != null) {
                    return ClassLookup.AMBIGUOUS;
                }
                found = c;
            }
        }
        if (found != null) {
            return ClassLookup.unique(found);
        }
        return forward == null ? ClassLookup.NONE : forwardAmbiguous ? ClassLookup.AMBIGUOUS : ClassLookup.unique(forward);
    }

    /**
     * Per-context-file memo of resolved class names, cached until any PSI change (same dependency as
     * {@link #includeClosure}). A {@link ConcurrentHashMap} because resolution runs off multiple
     * threads; only unambiguous positive results are ever stored (never nulls), so a hit is always a
     * genuine unique match. Recomputed empty on invalidation, so a stored positive is never stale.
     */
    @NotNull
    private static Map<String, MQL4ClassElement> classResolutionMemo(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () ->
                CachedValueProvider.Result.create(new ConcurrentHashMap<String, MQL4ClassElement>(),
                        PsiModificationTracker.MODIFICATION_COUNT));
    }

    private static void collectIndexed(@NotNull String name, @NotNull Project project, @NotNull GlobalSearchScope scope, @NotNull List<PsiElement> out) {
        for (MQL4FunctionElement f : MQL4FunctionNameIndex.getInstance().getElements(name, project, scope)) {
            if (name.equals(f.getFunctionName())) {
                out.add(f);
            }
        }
        for (MQL4ClassElement c : MQL4ClassNameIndex.getInstance().getElements(name, project, scope)) {
            if (name.equals(c.getTypeName())) {
                out.add(c);
            }
        }
        for (MQL4TypedefElement t : MQL4TypedefNameIndex.getInstance().getElements(name, project, scope)) {
            if (name.equals(t.getName())) {
                out.add(t);
            }
        }
    }

    /**
     * The #include-closure search scope for {@code file}, cached on the file (same PSI-change
     * dependency as {@link #includeClosure}) so the fresh {@code List} +
     * {@link GlobalSearchScope#filesScope} allocation isn't repeated on every resolve / member
     * access / class lookup from that file. Reused by both {@link #resolveNonLocal} and
     * {@link #resolveClassByName}.
     */
    @org.jetbrains.annotations.Nullable
    private static GlobalSearchScope closureScopeFor(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () ->
                CachedValueProvider.Result.create(closureScope(file.getProject(), includeClosure(file)),
                        PsiModificationTracker.MODIFICATION_COUNT));
    }

    /**
     * For a header, the union of the {@code #include} closures of the project {@code .mq5}/{@code .mq4}
     * files that include it, cached like {@link #closureScopeFor}; {@code null} for anything else.
     */
    @org.jetbrains.annotations.Nullable
    private static GlobalSearchScope includerScopeFor(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            Set<PsiFile> union = new LinkedHashSet<>();
            for (PsiFile includer : MqlVisibleNames.includers(file)) {
                union.addAll(includeClosure(includer));
            }
            union.remove(file);
            return CachedValueProvider.Result.create(union.isEmpty() ? null : closureScope(file.getProject(), union),
                    PsiModificationTracker.MODIFICATION_COUNT, VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS);
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
            com.intellij.openapi.progress.ProgressManager.checkCanceled();
            PsiFile current = queue.poll();
            // B-Stage-1: union the cached per-file "direct includes" edge list instead of re-walking
            // the PSI tree + regex-resolving each #include here. Only files whose OWN edges were
            // invalidated (normally just the one being typed in) recompute; every other closure file
            // is an O(1) cache hit. The visited-set cycle guard preserves the exact same closure
            // contents AND document-order as the former inline BFS.
            for (PsiFile target : directIncludes(current)) {
                if (visited.add(target)) {
                    queue.add(target);
                }
            }
        }
        return visited;
    }

    /**
     * The files that {@code file} directly {@code #include}s (resolved, nulls skipped), in document
     * order, cached per file. This isolates the expensive per-file work — the
     * {@link PsiTreeUtil#findChildrenOfType} tree walk plus a regex/reference
     * {@link MQL4PreprocessorIncludeBlock#resolveIncludedFile()} per include — from the cheap
     * closure assembly in {@link #computeIncludeClosure}. It rarely changes, so it recomputes only
     * when its own inputs change, not on every keystroke anywhere in the project.
     *
     * <p>Dependencies are exactly the three inputs that can change a file's resolved edge set:</p>
     * <ol>
     *   <li>{@code file} itself — its PSI, so editing/adding/removing an {@code #include} line (or
     *       any text change that shifts the include paths) re-derives the edges;</li>
     *   <li>{@link VirtualFileManager#VFS_STRUCTURE_MODIFICATIONS} — any create/delete/rename/move
     *       of a file in the VFS, so a formerly-missing include target appearing (or a target being
     *       removed/renamed) changes how a path resolves and re-derives the edges;</li>
     *   <li>{@link ProjectRootModificationTracker} for the project — mirrors how
     *       {@code MqlIncludeRoots.candidateIncludeRoots} caches, so an Include-root / SDK change
     *       (which changes angle-bracket {@code <...>} resolution) re-derives the edges.</li>
     * </ol>
     * This edge list therefore always equals what an inline resolve would produce at that moment;
     * the closure cache above still keys on {@code MODIFICATION_COUNT}, so WHEN the closure rebuilds
     * is unchanged — only the per-rebuild cost drops. No new staleness class is introduced.
     */
    @NotNull
    private static List<PsiFile> directIncludes(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> {
            List<PsiFile> out = new ArrayList<>();
            for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(file, MQL4PreprocessorIncludeBlock.class)) {
                com.intellij.openapi.progress.ProgressManager.checkCanceled();
                PsiFile target = include.resolveIncludedFile();
                if (target != null) {
                    out.add(target);
                }
            }
            return CachedValueProvider.Result.create(out,
                    file,
                    VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS,
                    ProjectRootModificationTracker.getInstance(file.getProject()));
        });
    }
}
