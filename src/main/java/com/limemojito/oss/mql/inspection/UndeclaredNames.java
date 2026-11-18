/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.tree.IElementType;
import com.intellij.psi.tree.TokenSet;
import com.intellij.psi.util.PsiTreeUtil;
import com.limemojito.oss.mql.MqlBuiltinFunctions;
import com.limemojito.oss.mql.MqlBuiltinTypes;
import com.limemojito.oss.mql.doc.MQL4DocumentationProvider;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4TokenSets;
import com.limemojito.oss.mql.psi.impl.MQL4PreprocessorIncludeBlock;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import com.intellij.psi.util.CachedValueProvider;
import com.intellij.psi.util.CachedValuesManager;
import com.intellij.psi.util.PsiModificationTracker;
import com.limemojito.oss.mql.doc.StructCatalog;
import com.limemojito.oss.mql.psi.impl.MQL4ClassElement;
import com.limemojito.oss.mql.reference.MqlResolveUtil;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Consumer;

/** What the "undeclared identifier" inspections share: which identifiers they look at, and built-ins. */
final class UndeclaredNames {

    /** Blocks whose identifiers aren't checked: macro bodies and #import declarations can name anything. */
    private static final TokenSet SKIPPED_BLOCKS = TokenSet.create(MQL4Elements.PREPROCESSOR_DEFINE_BLOCK,
            MQL4Elements.PREPROCESSOR_IMPORT_BLOCK, MQL4Elements.OPERATOR_NAME, MQL4Elements.PREPROCESSOR_PROPERTY_BLOCK,
            MQL4Elements.PREPROCESSOR_INCLUDE_BLOCK, MQL4Elements.PREPROCESSOR_UNDEF_BLOCK, MQL4Elements.TYPE_TEMPLATE_BLOCK);

    /** A name after one of these is a declaration ({@code int x}, {@code class C}, {@code enum E}). */
    private static final TokenSet DECLARING = TokenSet.orSet(MQL4TokenSets.DATA_TYPES, TokenSet.create(
            MQL4Elements.IDENTIFIER, MQL4Elements.TILDA, MQL4Elements.UNION_KEYWORD, MQL4Elements.TYPENAME_KEYWORD));

    /** After a {@code *} or {@code &} declarator, these end a declared name: {@code T *p = ...}, {@code f(T &a, ...)}. */
    private static final TokenSet AFTER_DECLARED_NAME = TokenSet.create(MQL4Elements.EQ, MQL4Elements.COMMA,
            MQL4Elements.R_ROUND_BRACKET, MQL4Elements.SEMICOLON, MQL4Elements.L_SQUARE_BRACKET);

    private UndeclaredNames() {
    }

    /**
     * A missing header could declare any name, so a file with one isn't checked at all. So could a
     * header too large for the IDE to parse (over {@code idea.max.intellisense.filesize}, 2.5 MB by
     * default): its declarations are never indexed.
     */
    static boolean hasUnresolvedInclude(@NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> CachedValueProvider.Result.create(
                closureHasUnseenInclude(file), PsiModificationTracker.MODIFICATION_COUNT,
                com.intellij.openapi.vfs.VirtualFileManager.VFS_STRUCTURE_MODIFICATIONS));
    }

    /**
     * True when any file in {@code file}'s include closure has an {@code #include} the plugin can't
     * see into: one that doesn't resolve, a file too large to parse, or a file that isn't MQL (a
     * {@code .h} header, which CLion gives to C++): its macros and declarations are invisible, so
     * checking names would guess.
     */
    private static boolean closureHasUnseenInclude(@NotNull PsiFile file) {
        for (PsiFile f : com.limemojito.oss.mql.reference.MqlVisibleNames.includeClosure(file)) {
            for (MQL4PreprocessorIncludeBlock include : PsiTreeUtil.findChildrenOfType(f, MQL4PreprocessorIncludeBlock.class)) {
                PsiFile target = include.resolveIncludedFile();
                if (target == null || !(target instanceof com.limemojito.oss.mql.psi.MQL4File) || (target.getVirtualFile() != null
                        && com.intellij.psi.SingleRootFileViewProvider.isTooLargeForIntelligence(target.getVirtualFile()))) {
                    return true;
                }
            }
        }
        return false;
    }

    /** Every IDENTIFIER outside the skipped blocks and the {@code #ifdef}/{@code #ifndef} condition names. */
    static void forEachIdentifier(@NotNull PsiFile file, @NotNull Consumer<ASTNode> action) {
        visit(file.getNode(), action);
    }

    private static void visit(@NotNull ASTNode node, @NotNull Consumer<ASTNode> action) {
        for (ASTNode child = node.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            IElementType type = child.getElementType();
            if (SKIPPED_BLOCKS.contains(type)) {
                continue;
            }
            if (type == MQL4Elements.IDENTIFIER) {
                IElementType prev = prevType(child);
                if (prev != MQL4Elements.IFDEF_PP_KEYWORD && prev != MQL4Elements.IFNDEF_PP_KEYWORD) {
                    action.accept(child);
                }
            } else if (child.getFirstChildNode() != null) {
                visit(child, action);
            }
        }
    }

    /**
     * Names a file declares outside the PSI the resolver sees: {@code #resource}
     * variables ({@code #resource "k.cl" as string src}) and parameters that an invoked macro's
     * expansion declares ({@code EVENT_MAP_BEGIN(C)} opens {@code OnEvent(const int id, ...)}).
     * (Template parameters are declarations scoped to their template and resolve directly.)
     */
    static boolean isDeclaredOutsidePsi(@NotNull String name, @NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> CachedValueProvider.Result.create(
                collectOutsidePsi(file), PsiModificationTracker.MODIFICATION_COUNT)).contains(name);
    }

    /**
     * True when {@code name} is generated by a token-pasting macro invoked in {@code file}:
     * {@code #define BOOL_PROP(P,O) bool set##P(bool v) ...} invoked as {@code BOOL_PROP(ShowOHLC, ...)}
     * declares {@code setShowOHLC}; {@code m_##Private} with {@code magic} declares {@code m_magic}.
     * The macro may be defined anywhere in the include closure.
     */
    static boolean isPastedByMacro(@NotNull String name, @NotNull PsiFile file) {
        return CachedValuesManager.getCachedValue(file, () -> CachedValueProvider.Result.create(
                collectPasted(file), PsiModificationTracker.MODIFICATION_COUNT)).contains(name);
    }

    /** {@code a ## B ## c}: identifiers joined by token pasting in a macro body. */
    private static final java.util.regex.Pattern PASTE = java.util.regex.Pattern.compile(
            "[A-Za-z_0-9]+(?:\\s*##\\s*[A-Za-z_0-9]+)+");

    private static Set<String> collectPasted(@NotNull PsiFile file) {
        java.util.Map<String, String> pasting = new java.util.HashMap<>(); // macro name -> its #define text
        for (PsiFile f : com.limemojito.oss.mql.reference.MqlVisibleNames.includeClosure(file)) {
            for (com.limemojito.oss.mql.psi.impl.MQL4DefineElement d
                    : PsiTreeUtil.findChildrenOfType(f, com.limemojito.oss.mql.psi.impl.MQL4DefineElement.class)) {
                if (d.getName() != null && d.getText().contains("##")) {
                    pasting.put(d.getName(), d.getText());
                }
            }
        }
        if (pasting.isEmpty()) {
            return Set.of();
        }
        Set<String> names = new HashSet<>();
        for (ASTNode leaf = firstLeaf(file.getNode()); leaf != null; leaf = nextLeaf(leaf)) {
            if (leaf.getElementType() != MQL4Elements.IDENTIFIER || !pasting.containsKey(leaf.getText())) {
                continue;
            }
            PsiElement open = PsiTreeUtil.nextVisibleLeaf(leaf.getPsi());
            if (open == null || open.getNode().getElementType() != MQL4Elements.L_ROUND_BRACKET) {
                continue; // the #define itself, or a use without arguments
            }
            List<String> args = new java.util.ArrayList<>();
            StringBuilder arg = new StringBuilder();
            int depth = 0;
            for (PsiElement n = open; n != null; n = PsiTreeUtil.nextVisibleLeaf(n)) {
                IElementType t = n.getNode().getElementType();
                if (t == MQL4Elements.L_ROUND_BRACKET && depth++ == 0) {
                    continue;
                }
                if (t == MQL4Elements.R_ROUND_BRACKET && --depth == 0) {
                    args.add(arg.toString().trim());
                    break;
                }
                if (t == MQL4Elements.COMMA && depth == 1) {
                    args.add(arg.toString().trim());
                    arg.setLength(0);
                } else {
                    arg.append(n.getText());
                }
            }
            names.addAll(pastedNames(pasting.get(leaf.getText()), leaf.getText(), args));
        }
        return names;
    }

    /** The identifiers {@code define} pastes together when invoked as {@code macro(args)}. */
    static Set<String> pastedNames(@NotNull String define, @NotNull String macro, @NotNull List<String> args) {
        int open = define.indexOf('(', define.indexOf(macro) + macro.length());
        int close = open < 0 ? -1 : define.indexOf(')', open);
        if (open < 0 || close < 0) {
            return Set.of();
        }
        List<String> params = java.util.Arrays.stream(define.substring(open + 1, close).split(","))
                .map(String::trim).toList();
        Set<String> out = new HashSet<>();
        java.util.regex.Matcher m = PASTE.matcher(define.substring(close + 1));
        while (m.find()) {
            StringBuilder name = new StringBuilder();
            for (String piece : m.group().split("\\s*##\\s*")) {
                int i = params.indexOf(piece);
                name.append(i >= 0 && i < args.size() ? args.get(i) : piece);
            }
            if (name.toString().matches("[A-Za-z_]\\w*")) {
                out.add(name.toString());
            }
        }
        return out;
    }

    /** {@code (const long& lparam,} in a macro body: group 1 is a parameter the expansion declares. */
    private static final java.util.regex.Pattern MACRO_BODY_PARAMETER = java.util.regex.Pattern.compile(
            "[(,]\\s*(?:const\\s+)?[A-Za-z_]\\w*\\s*[&*]?\\s*([A-Za-z_]\\w*)\\s*(?:\\[\\s*\\]\\s*)?(?=[,)=])");

    /** An upper-case name (the macro convention) is looked up as a possible macro invocation. */
    private static final java.util.regex.Pattern MACRO_NAME = java.util.regex.Pattern.compile("[A-Z][A-Z0-9_]+");

    private static Set<String> collectOutsidePsi(@NotNull PsiFile file) {
        Set<String> names = new HashSet<>();
        Set<String> macrosSeen = new HashSet<>();
        for (ASTNode leaf = firstLeaf(file.getNode()); leaf != null; leaf = nextLeaf(leaf)) {
            IElementType t = leaf.getElementType();
            if (t == MQL4Elements.IDENTIFIER && MACRO_NAME.matcher(leaf.getText()).matches()
                    && macrosSeen.add(leaf.getText())) {
                // EVENT_MAP_BEGIN(CBox) expands to bool CBox::OnEvent(const int id,const long& lparam,...) {
                for (PsiElement target : MqlResolveUtil.resolve(leaf.getPsi(), leaf.getText())) {
                    if (target instanceof com.limemojito.oss.mql.psi.impl.MQL4DefineElement define) {
                        String body = define.getText();
                        int open = body.indexOf('(', body.indexOf(leaf.getText()) + leaf.getText().length() + 1);
                        java.util.regex.Matcher m = MACRO_BODY_PARAMETER.matcher(open < 0 ? "" : body.substring(open));
                        while (m.find()) {
                            names.add(m.group(1));
                        }
                    }
                }
            } else if (t == MQL4Elements.RESOURCE_PP_KEYWORD) {
                String last = null;
                boolean as = false;
                for (ASTNode n = nextLeaf(leaf); n != null && !(isLineBreak(n)); n = nextLeaf(n)) {
                    if (n.getElementType() == MQL4Elements.IDENTIFIER) {
                        as |= "as".equals(n.getText());
                        last = n.getText();
                    }
                }
                if (as && last != null) {
                    names.add(last);
                }
            }
        }
        return names;
    }

    /** True for an identifier on a {@code #resource} line: its {@code as} and the names after it. */
    static boolean onResourceLine(@NotNull ASTNode identifier) {
        for (ASTNode n = prevLeaf(identifier); n != null; n = prevLeaf(n)) {
            if (isLineBreak(n)) {
                return false;
            }
            if (n.getElementType() == MQL4Elements.RESOURCE_PP_KEYWORD) {
                return true;
            }
        }
        return false;
    }

    /**
     * True when {@code name} is a member a class at {@code at} inherits from a built-in structure
     * ({@code struct CStamp : public MqlDateTime { int H() { return hour; } }}).
     */
    static boolean isInheritedBuiltinMember(@NotNull String name, @NotNull PsiElement at) {
        MQL4ClassElement cls = PsiTreeUtil.getParentOfType(at, MQL4ClassElement.class);
        if (cls == null) {
            cls = MqlResolveUtil.enclosingClass(at);
        }
        return cls != null && inheritsBuiltinMember(cls, name, new HashSet<>());
    }

    private static boolean inheritsBuiltinMember(@NotNull MQL4ClassElement cls, @NotNull String name, @NotNull Set<MQL4ClassElement> seen) {
        if (!seen.add(cls) || seen.size() > 16) {
            return false;
        }
        for (String base : MqlResolveUtil.baseClassNames(cls)) {
            StructCatalog.Members builtin = StructCatalog.of(base);
            if (builtin != null) {
                if (builtin.has(name)) {
                    return true;
                }
                continue;
            }
            MQL4ClassElement baseClass = MqlResolveUtil.findClassByName(base, cls.getProject(), cls);
            if (baseClass != null && inheritsBuiltinMember(baseClass, name, seen)) {
                return true;
            }
        }
        return false;
    }

    private static boolean isLineBreak(@NotNull ASTNode n) {
        return com.limemojito.oss.mql.parser.MQL4ParserDefinition.WHITE_SPACES.contains(n.getElementType()) && n.textContains('\n');
    }

    @Nullable
    private static ASTNode firstLeaf(@NotNull ASTNode node) {
        ASTNode n = node;
        while (n.getFirstChildNode() != null) {
            n = n.getFirstChildNode();
        }
        return n == node ? null : n;
    }

    @Nullable
    private static ASTNode nextLeaf(@NotNull ASTNode node) {
        return com.intellij.psi.impl.source.tree.TreeUtil.nextLeaf(node);
    }

    @Nullable
    private static ASTNode prevLeaf(@NotNull ASTNode node) {
        return com.intellij.psi.impl.source.tree.TreeUtil.prevLeaf(node);
    }

    static boolean isBuiltin(@NotNull String name) {
        return MQL4DocumentationProvider.getEntryByText(name) != null || MqlBuiltinFunctions.isBuiltinName(name)
                || MqlBuiltinTypes.MQL5_TYPES.contains(name) || "offsetof".equals(name);
    }

    /**
     * True for the name a declaration introduces rather than a use: a function, parameter, variable,
     * class or enum name ({@code int x}, {@code CFoo obj(1)}, {@code T *p = NULL}, {@code ~CFoo()}).
     */
    static boolean isDeclarationName(@NotNull ASTNode identifier) {
        PsiElement psi = identifier.getPsi();
        for (PsiElement owner = psi.getParent(); owner != null && !(owner instanceof PsiFile); owner = owner.getParent()) {
            if (owner instanceof PsiNameIdentifierOwner named && named.getNameIdentifier() != null) {
                if (named.getNameIdentifier().getNode() == identifier) {
                    return true;
                }
                break;
            }
        }
        ASTNode parent = identifier.getTreeParent();
        if (parent != null && parent.getElementType() == MQL4Elements.VAR_DEFINITION) {
            return true;
        }
        IElementType prev = prevType(identifier);
        if (prev != null && DECLARING.contains(prev)) {
            return true;
        }
        if (prev == MQL4Elements.MUL || prev == MQL4Elements.AND) {
            ASTNode declarator = prevNode(identifier);
            IElementType beforeDeclarator = declarator == null ? null : prevType(declarator);
            IElementType next = nextType(identifier);
            return beforeDeclarator != null && DECLARING.contains(beforeDeclarator)
                    && (next == null || AFTER_DECLARED_NAME.contains(next));
        }
        return false;
    }

    @Nullable
    static IElementType prevType(@NotNull ASTNode node) {
        ASTNode prev = prevNode(node);
        return prev == null ? null : prev.getElementType();
    }

    @Nullable
    private static ASTNode prevNode(@NotNull ASTNode node) {
        PsiElement prev = PsiTreeUtil.prevVisibleLeaf(node.getPsi());
        while (prev != null && MQL4TokenSets.COMMENTS_OR_WS.contains(prev.getNode().getElementType())) {
            prev = PsiTreeUtil.prevVisibleLeaf(prev);
        }
        return prev == null ? null : prev.getNode();
    }

    @Nullable
    static IElementType nextType(@NotNull ASTNode node) {
        PsiElement next = PsiTreeUtil.nextVisibleLeaf(node.getPsi());
        while (next != null && MQL4TokenSets.COMMENTS_OR_WS.contains(next.getNode().getElementType())) {
            next = PsiTreeUtil.nextVisibleLeaf(next);
        }
        return next == null ? null : next.getNode().getElementType();
    }
}
