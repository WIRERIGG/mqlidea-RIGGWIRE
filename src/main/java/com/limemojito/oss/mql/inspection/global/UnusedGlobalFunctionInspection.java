/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection.global;

import com.intellij.analysis.AnalysisScope;
import com.intellij.codeInspection.CommonProblemDescriptor;
import com.intellij.codeInspection.GlobalInspectionContext;
import com.intellij.codeInspection.GlobalInspectionTool;
import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.ProblemDescriptionsProcessor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.reference.RefElement;
import com.intellij.codeInspection.reference.RefManager;
import com.intellij.lang.ASTNode;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.project.DumbService;
import com.intellij.openapi.project.Project;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiElementVisitor;
import com.intellij.psi.PsiFile;
import com.intellij.psi.search.searches.ReferencesSearch;
import com.intellij.util.Query;
import com.limemojito.oss.mql.psi.MQL4Elements;
import com.limemojito.oss.mql.psi.MQL4File;
import com.limemojito.oss.mql.psi.MqlEventHandlers;
import com.limemojito.oss.mql.psi.impl.MQL4FunctionElement;
import org.jetbrains.annotations.NotNull;

import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Cross-file "dead code" inspection: a top-level project function that is <em>defined</em> (not just
 * declared) but never referenced anywhere reachable from the project's {@code #include} closure.
 * <p>
 * This is a {@link GlobalInspectionTool} rather than a {@link com.intellij.codeInspection.LocalInspectionTool}
 * because "is this function used <em>somewhere in the project</em>" cannot be answered from a single
 * file's PSI — it needs a project-wide usage search. The plugin registers no {@code RefManager}
 * extension for MQL, so the platform's reference graph never materialises {@code RefElement}s for our
 * functions; we therefore do <b>not</b> use the graph ({@link #isGraphNeeded()} is {@code false}) and
 * instead drive a {@link ReferencesSearch} usage-search per candidate function (see
 * {@link #isReferencedInProject}). {@code ReferencesSearch} spans the whole project, which includes
 * every {@code #include}-reachable file, so a call in an included {@code .mqh} counts as a use.
 * <p>
 * <b>Whitelist</b> (never flagged, {@link #isWhitelisted}):
 * <ul>
 *   <li>Event handlers ({@code OnInit}/{@code OnTick}/{@code OnStart}/{@code OnCalculate}/... — the
 *       whole {@link MqlEventHandlers#NAMES} set): the terminal calls these; they have no in-code
 *       caller, so flagging them would nag every EA/indicator/script.</li>
 *   <li>Functions whose name is declared inside an {@code #import} block in the same file — the
 *       library/DLL import boundary; the implementation may live outside the visible sources.</li>
 * </ul>
 * Default-OFF and {@code WEAK WARNING} (see plugin.xml), matching the plugin's cautious posture:
 * without full member-access resolution a function only ever called as {@code obj.Method()} could be
 * a false positive, so this stays opt-in.
 * <p>
 * The core decision ({@link #isUnusedGlobalFunction}) is a pure, side-effect-free static helper so it
 * is unit-testable directly against a multi-file fixture without having to drive the full global
 * inspection pipeline.
 */
public final class UnusedGlobalFunctionInspection extends GlobalInspectionTool {

    @Override
    public boolean isGraphNeeded() {
        // We do not consult the platform reference graph (no RefManager extension exists for MQL);
        // building it would be wasted work.
        return false;
    }

    @Override
    public boolean isReadActionNeeded() {
        // runInspection performs PSI reads and a ReferencesSearch; it must hold a read action.
        return true;
    }

    @Override
    public void runInspection(@NotNull AnalysisScope scope,
                              @NotNull InspectionManager manager,
                              @NotNull GlobalInspectionContext globalContext,
                              @NotNull ProblemDescriptionsProcessor problemDescriptionsProcessor) {
        final RefManager refManager = globalContext.getRefManager();
        scope.accept(new PsiElementVisitor() {
            @Override
            public void visitFile(@NotNull PsiFile psiFile) {
                if (!(psiFile instanceof MQL4File)) {
                    return;
                }
                ProgressManager.checkCanceled();
                for (MQL4FunctionElement fn : topLevelFunctionDefinitions(psiFile)) {
                    ProgressManager.checkCanceled();
                    if (!isUnusedGlobalFunction(fn)) {
                        continue;
                    }
                    PsiElement anchor = fn.getNameIdentifier();
                    if (anchor == null) {
                        anchor = fn;
                    }
                    // Attach the problem to the file's RefElement (the grouping node in the batch
                    // Inspection Results tree) while the descriptor still points at the function's
                    // name for highlighting/navigation.
                    RefElement fileRef = refManager.getReference(psiFile);
                    if (fileRef == null) {
                        continue;
                    }
                    CommonProblemDescriptor descriptor = manager.createProblemDescriptor(
                            anchor,
                            "Global function '" + fn.getFunctionName()
                                    + "' is never used in the project's #include closure",
                            false,
                            LocalQuickFix.EMPTY_ARRAY,
                            ProblemHighlightType.LIKE_UNUSED_SYMBOL);
                    problemDescriptionsProcessor.addProblemElement(fileRef, descriptor);
                }
            }
        });
    }

    // ---- Testable core logic ------------------------------------------------------------------

    /**
     * The definitive test: {@code fn} is a top-level function definition that is neither an entry
     * point/whitelisted symbol nor referenced anywhere in the project. Pure and side-effect free
     * (beyond the read-only index/usage search), so it can be asserted directly in a unit test.
     */
    public static boolean isUnusedGlobalFunction(@NotNull MQL4FunctionElement fn) {
        return isCandidate(fn) && !isWhitelisted(fn) && !isReferencedInProject(fn);
    }

    /**
     * A flaggable candidate: a real, named, top-level function <em>definition</em> (not a forward
     * declaration, not a class method, not a destructor, not the unknown-name recovery node).
     */
    public static boolean isCandidate(@NotNull MQL4FunctionElement fn) {
        if (fn.isDeclaration()) {
            return false;
        }
        // Top-level only: a class/struct method's parent node is the CLASS_INNER_BLOCK, and an
        // #import declaration's parent is the PREPROCESSOR_IMPORT_BLOCK; only a file-level function
        // has the file itself as its direct PSI parent.
        if (!(fn.getParent() instanceof MQL4File)) {
            return false;
        }
        String name = fn.getFunctionName();
        return name != null
                && !name.isEmpty()
                && !MQL4FunctionElement.UNKNOWN_NAME.equals(name)
                && !name.startsWith("~");
    }

    /** True when {@code fn} must never be flagged even if unreferenced (see class doc). */
    public static boolean isWhitelisted(@NotNull MQL4FunctionElement fn) {
        String name = fn.getFunctionName();
        if (MqlEventHandlers.NAMES.contains(name)) {
            return true;
        }
        return importedFunctionNames(fn.getContainingFile()).contains(name);
    }

    /** True when any project reference resolves to {@code fn} (a call site, including in an #include). */
    public static boolean isReferencedInProject(@NotNull MQL4FunctionElement fn) {
        Project project = fn.getProject();
        // In dumb mode the usage search would throw; conservatively treat the function as used so we
        // never flag it while indices are unavailable.
        if (DumbService.isDumb(project)) {
            return true;
        }
        Query<com.intellij.psi.PsiReference> usages = ReferencesSearch.search(fn);
        return usages.findFirst() != null;
    }

    // ---- Helpers ------------------------------------------------------------------------------

    /** Every top-level function definition in {@code file} (never class methods / import decls). */
    @NotNull
    static List<MQL4FunctionElement> topLevelFunctionDefinitions(@NotNull PsiFile file) {
        java.util.List<MQL4FunctionElement> out = new java.util.ArrayList<>();
        for (PsiElement child = file.getFirstChild(); child != null; child = child.getNextSibling()) {
            if (child instanceof MQL4FunctionElement fn && !fn.isDeclaration()) {
                out.add(fn);
            }
        }
        return out;
    }

    /**
     * Names of functions declared inside an {@code #import} block in {@code file} — the DLL/library
     * import boundary. A same-named top-level definition is the implementation of an
     * imported/exported entry and must not be flagged.
     * <p>
     * The parser does not wrap an {@code #import} block in a composite PSI node — the
     * {@code #import} keyword, its string literal, and the enclosed function declarations are all
     * flat direct children of the file. So this walks the file's top-level children tracking whether
     * we are inside an import section: an {@code #import} keyword <em>followed by a string literal</em>
     * opens one ({@code #import "lib.ex5"}); an {@code #import} keyword <em>not</em> followed by a
     * string closes it (the bare {@code #import} terminator). Every function declaration seen while
     * open is collected.
     */
    @NotNull
    private static Set<String> importedFunctionNames(@NotNull PsiFile file) {
        Set<String> names = new HashSet<>();
        ASTNode fileNode = file.getNode();
        if (fileNode == null) {
            return names;
        }
        boolean insideImport = false;
        for (ASTNode child = fileNode.getFirstChildNode(); child != null; child = child.getTreeNext()) {
            ProgressManager.checkCanceled();
            if (child.getElementType() == MQL4Elements.IMPORT_PP_KEYWORD) {
                ASTNode next = nextNonWhitespace(child);
                insideImport = next != null && next.getElementType() == MQL4Elements.STRING_LITERAL;
                continue;
            }
            if (insideImport) {
                PsiElement psi = child.getPsi();
                if (psi instanceof MQL4FunctionElement fn && fn.isDeclaration()) {
                    String n = fn.getFunctionName();
                    if (n != null && !n.isEmpty()) {
                        names.add(n);
                    }
                }
            }
        }
        return names;
    }

    @org.jetbrains.annotations.Nullable
    private static ASTNode nextNonWhitespace(@NotNull ASTNode node) {
        ASTNode sibling = node.getTreeNext();
        while (sibling != null && sibling.getPsi() instanceof com.intellij.psi.PsiWhiteSpace) {
            sibling = sibling.getTreeNext();
        }
        return sibling;
    }
}
