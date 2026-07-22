/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.inspection;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionEP;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.LocalQuickFix;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.codeInspection.ProblemHighlightType;
import com.intellij.codeInspection.QuickFix;
import com.intellij.ide.projectView.ProjectView;
import com.intellij.openapi.Disposable;
import com.intellij.openapi.application.ApplicationManager;
import com.intellij.openapi.application.ReadAction;
import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.extensions.ExtensionPointName;
import com.intellij.openapi.progress.ProcessCanceledException;
import com.intellij.openapi.progress.ProgressManager;
import com.intellij.openapi.progress.util.ProgressIndicatorUtils;
import com.intellij.openapi.project.DumbService;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.search.FileTypeIndex;
import com.intellij.psi.search.GlobalSearchScope;
import com.limemojito.oss.mql.MQL4FileType;
import com.limemojito.oss.mql.MQL5FileType;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import com.limemojito.oss.mql.healing.db.HealingDatabase;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.AtomicMoveNotSupportedException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class MqlProblemsLoggerService implements Disposable {

    private static final Logger LOG = Logger.getInstance(MqlProblemsLoggerService.class);
    private static final String LOG_FILE_NAME = "mql-problems.log";
    private static final String TASKS_FILE_NAME = "mql-tasks.md";
    private static final DateTimeFormatter TIMESTAMP_FORMAT = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final ExtensionPointName<LocalInspectionEP> LOCAL_INSPECTION_EP =
            new ExtensionPointName<>("com.intellij.localInspection");
    private static final long YIELD_SLEEP_MS = 5;
    private static final int BATCH_SIZE = 5;

    private static final Map<String, String> FIX_HINTS = Map.ofEntries(
            // Trading Safety
            Map.entry("UncheckedOrderSend", "Check OrderSend() return value: if(!OrderSend(request, result)) { Print(\"Error: \", GetLastError()); }"),
            Map.entry("UncheckedHandle", "Check handle after creation: if(handle == INVALID_HANDLE) { Print(\"Error: \", GetLastError()); }"),
            Map.entry("MissingIndicatorRelease", "Add IndicatorRelease(handle) in OnDeinit()"),
            Map.entry("ArrayAccessWithoutSizeCheck", "Check ArraySize() before accessing: if(ArraySize(arr) > index) { ... }"),
            Map.entry("MissingInputValidation", "Validate input parameters in OnInit(): if(InpParam <= 0) return INIT_PARAMETERS_INCORRECT;"),
            Map.entry("MissingFileClose", "Add FileClose(handle) after file operations"),
            Map.entry("UncheckedCopyRates", "Check CopyRates/CopyBuffer return: if(CopyRates(...) <= 0) { Print(\"Copy failed\"); return; }"),
            Map.entry("DoubleIndicatorRelease", "Remove duplicate IndicatorRelease() call"),
            Map.entry("DeleteWithoutNullCheck", "Add NULL check before delete: if(ptr != NULL) { delete ptr; ptr = NULL; }"),
            // Function Signature
            Map.entry("MissingOnInitReturn", "Change OnInit() return type from void to int and return INIT_SUCCEEDED"),
            Map.entry("EmptyEventHandler", "Add implementation or remove the empty event handler"),
            Map.entry("MissingConstParameter", "Add 'const' qualifier to reference parameter: const Type &param"),
            Map.entry("LargeStructByValue", "Pass large struct by reference: void Func(const MqlTradeRequest &request)"),
            Map.entry("MissingDestructor", "Add destructor: ~ClassName() { /* cleanup */ }"),
            Map.entry("VirtualWithoutDestructor", "Add virtual destructor: virtual ~ClassName() { }"),
            // Class Structure
            Map.entry("PublicDataMember", "Make data member private and add getter/setter methods"),
            Map.entry("MissingPropertyDescription", "Add #property description \"Your description here\""),
            Map.entry("MissingPropertyVersion", "Add #property version \"1.00\""),
            Map.entry("ExcessiveGlobalVariables", "Encapsulate related globals into a struct or class"),
            Map.entry("ImmutableInputParameter", "Copy input to a local variable: double localParam = InpParam;"),
            // Naming & Style
            Map.entry("FunctionNamingConvention", "Rename function to PascalCase: MyFunctionName()"),
            Map.entry("VariableNamingConvention", "Rename variable to follow convention (camelCase or with prefix)"),
            Map.entry("ClassNamingConvention", "Rename class with 'C' prefix: class CMyClass"),
            Map.entry("MissingFunctionDocComment", "Add documentation comment before function: //--- Description"),
            // Type Safety
            Map.entry("NarrowingReturnType", "Match return type to actual returned value type to avoid precision loss"),
            Map.entry("UninitializedVariable", "Add initializer: int count = 0; double value = 0.0;"),
            Map.entry("ImplicitCast", "Add explicit cast: (int)doubleValue or (double)intValue"),
            // Performance
            Map.entry("ArrayResizeInLoop", "Move ArrayResize() before the loop and pre-allocate with reserve parameter"),
            Map.entry("PrintInOnTick", "Guard with condition: if(enableLogging) Print(...); or use Comment() sparingly"),
            Map.entry("SleepInEventHandler", "Remove Sleep() from event handler — use Timer events instead"),
            Map.entry("RedundantCalculationInOnTick", "Cache calculation result in a static/global variable, recalculate only on new bar"),
            Map.entry("StringConcatInLoop", "Use StringConcatenate() or StringAdd() instead of '+' in loops"),
            Map.entry("SuboptimalContainer", "Consider using more efficient data structures or access patterns"),
            Map.entry("MissingArrayPreallocation", "Pre-allocate array: ArrayResize(arr, expectedSize, reserveSize)"),
            Map.entry("LazyEvaluationMiss", "Reorder conditions to check cheap/likely-false conditions first"),
            // Security & Data
            Map.entry("AccountInfoExposure", "Avoid logging sensitive account info; use masked output if needed"),
            Map.entry("HardcodedCredentials", "Move credentials to input parameters or encrypted configuration"),
            Map.entry("SafeApiUsage", "Add volume validation: double lot = NormalizeDouble(volume, 2); check against SymbolInfoDouble()"),
            Map.entry("FileOperationValidation", "Check return value of file read/write operations"),
            Map.entry("DeterministicSeed", "Use MathSrand(GetTickCount()) for non-deterministic random seed"),
            // Advanced Patterns
            Map.entry("StackOverflowRisk", "Add recursion depth limit or convert to iterative approach"),
            Map.entry("DanglingObjectReference", "Set pointer to NULL after object is deleted or goes out of scope"),
            Map.entry("StaleHandleUsage", "Set handle to INVALID_HANDLE after IndicatorRelease() and check before use"),
            Map.entry("IncompleteClass", "Implement copy constructor and assignment operator, or delete them"),
            Map.entry("GlobalVariableConflict", "Use a single function to manage GlobalVariableSet() access, or use a mutex pattern"),
            Map.entry("MissingErrorRecovery", "Add retry logic with Sleep() and attempt counter for failed OrderSend()"),
            Map.entry("OverComplexErrorHandling", "Simplify nested error checks — extract into helper function"),
            Map.entry("UnsafeArrayCopy", "Validate source/destination sizes before ArrayCopy()"),
            Map.entry("ModernMQL5Idiom", "Replace deprecated MQL4 function with MQL5 equivalent"),
            Map.entry("DataConsistency", "Use NormalizeDouble() for price comparisons: if(NormalizeDouble(a-b, _Digits) == 0)"),
            Map.entry("TimeseriesDirection", "Add ArraySetAsSeries(array, true) after CopyRates/CopyBuffer"),
            Map.entry("SecureCodingPatterns", "Apply secure coding pattern — see inspection description for details"),
            // Memory & Allocation
            Map.entry("ObjectCreationInOnTick", "Move object creation to OnInit() and reuse in OnTick()"),
            Map.entry("ArrayResizeReturnCheck", "Check ArrayResize() return: if(ArrayResize(arr, size) < 0) { Print(\"Error\"); }"),
            Map.entry("NullAfterDelete", "Set pointer to NULL after delete: delete ptr; ptr = NULL;"),
            Map.entry("IndicatorCreationInOnTick", "Move indicator handle creation to OnInit()"),
            Map.entry("NewKeywordInLoop", "Move 'new' allocation outside loop; reuse objects or use object pool"),
            Map.entry("MissingNewBarCheck", "Add new bar check: static datetime lastBar = 0; if(iTime(_Symbol,0,0) == lastBar) return; lastBar = iTime(_Symbol,0,0);"),
            Map.entry("UnconditionalOrderLoop", "Add conditions to order loop: check spread, time, signal before sending orders"),
            // Control Flow
            Map.entry("NoGoto", "Replace 'goto' with structured control flow (loops, functions, break/continue)"),
            Map.entry("SuspiciousSemicolon", "Remove suspicious semicolon after if/for/while, or add braces for empty body"),
            Map.entry("EmptyLoopBody", "Add loop body implementation or add a comment explaining intentional empty loop"),
            Map.entry("MissingDefaultCase", "Add 'default: break;' case to the switch statement"),
            Map.entry("MissingBreakInSwitch", "Add 'break;' at end of case, or add '// fallthrough' comment if intentional"),
            Map.entry("InfiniteLoopRisk", "Add loop termination condition or break statement"),
            // Code Complexity
            Map.entry("DeepNesting", "Extract deeply nested code into separate functions"),
            Map.entry("LongFunction", "Split long function into smaller, focused functions"),
            Map.entry("TooManyParameters", "Group related parameters into a struct"),
            Map.entry("UnusedParameter", "Remove unused parameter or prefix with /* unused */"),
            Map.entry("TodoFixme", "Resolve the TODO/FIXME item or create a tracking issue"),
            // Trading-Specific
            Map.entry("MagicNumber", "Replace hardcoded values with named constants or input parameters"),
            Map.entry("ReturnValueIgnored", "Check return value: if(!FunctionCall()) { Print(\"Error\"); }"),
            Map.entry("VirtualCallInConstructor", "Move virtual method call out of constructor/destructor into a separate Init() method"),
            Map.entry("RepeatedApiCall", "Cache API call result: static double cachedSpread = 0; recalculate on new bar only"),
            // Preprocessor
            Map.entry("PreprocessorProperty", "Review #property directive syntax and values")
    );

    private final Project project;
    private final ScheduledExecutorService executor;
    private volatile ScheduledFuture<?> pendingScan;

    // Cache: file URL -> (modStamp, problems)
    private final ConcurrentHashMap<String, CachedFileResult> cache = new ConcurrentHashMap<>();
    // Guards all access to dirtyFileUrls (contents and reference swap)
    private final Object dirtyLock = new Object();
    // Guards cancel+reschedule of pendingScan
    private final Object scheduleLock = new Object();
    // Dirty files needing re-scan (null = full scan needed); access only under dirtyLock
    private Set<String> dirtyFileUrls;
    // Track which file URLs had problems on the previous scan, for icon refresh
    private volatile Set<String> previousProblemUrls = new HashSet<>();

    public MqlProblemsLoggerService(Project project) {
        this.project = project;
        this.executor = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "MQL-Problems-Logger");
            t.setDaemon(true);
            t.setPriority(Thread.MIN_PRIORITY);
            return t;
        });
    }

    public static MqlProblemsLoggerService getInstance(@NotNull Project project) {
        return project.getService(MqlProblemsLoggerService.class);
    }

    /**
     * Returns true if the file at the given URL has cached problems.
     * O(1) ConcurrentHashMap lookup, safe for UI thread.
     */
    public boolean hasProblems(@NotNull String fileUrl) {
        CachedFileResult cached = cache.get(fileUrl);
        return cached != null && !cached.problems().isEmpty();
    }

    public void scanAllFiles() {
        if (project.isDisposed()) return;
        synchronized (dirtyLock) {
            dirtyFileUrls = null; // null = full scan
        }
        executor.submit(this::doScan);
    }

    public void scheduleScan() {
        if (project.isDisposed()) return;
        synchronized (scheduleLock) {
            ScheduledFuture<?> prev = pendingScan;
            if (prev != null) {
                prev.cancel(false);
            }
            pendingScan = executor.schedule(this::doScan, 1000, TimeUnit.MILLISECONDS);
        }
    }

    public void markDirty(@NotNull Collection<String> fileUrls) {
        synchronized (dirtyLock) {
            Set<String> current = dirtyFileUrls;
            if (current == null) return; // already pending full scan
            current.addAll(fileUrls);
        }
    }

    private void doScan() {
        if (project.isDisposed()) return;
        if (DumbService.isDumb(project)) {
            DumbService.getInstance(project).runWhenSmart(this::scanAllFiles);
            return;
        }

        try {
            // Collect the file list in a short read action
            Set<VirtualFile> allFiles = ReadAction.compute(() -> {
                Set<VirtualFile> files = new LinkedHashSet<>();
                files.addAll(FileTypeIndex.getFiles(MQL4FileType.INSTANCE, GlobalSearchScope.projectScope(project)));
                files.addAll(FileTypeIndex.getFiles(MQL5FileType.INSTANCE, GlobalSearchScope.projectScope(project)));
                return files;
            });

            // Atomically snapshot the dirty set and reset it, then scan over the snapshot
            Set<String> dirty;
            synchronized (dirtyLock) {
                dirty = dirtyFileUrls;
                dirtyFileUrls = new LinkedHashSet<>();
            }

            String basePath = project.getBasePath();
            if (basePath == null) return;

            List<LocalInspectionTool> tools = ReadAction.compute(this::discoverInspections);

            // Prune cache entries for deleted/renamed files so the report stays current
            Set<String> currentUrls = new LinkedHashSet<>();
            for (VirtualFile vf : allFiles) {
                currentUrls.add(vf.getUrl());
            }
            cache.keySet().retainAll(currentUrls);

            // Build batches of files that need scanning
            List<VirtualFile> filesToScan = new ArrayList<>();
            for (VirtualFile vf : allFiles) {
                String url = vf.getUrl();
                long modStamp = vf.getModificationStamp();

                if (dirty != null) {
                    CachedFileResult cached = cache.get(url);
                    if (cached != null && cached.modStamp == modStamp && !dirty.contains(url)) {
                        continue;
                    }
                }
                filesToScan.add(vf);
            }

            // Process files in batches of BATCH_SIZE per ReadAction
            for (int i = 0; i < filesToScan.size(); i += BATCH_SIZE) {
                if (project.isDisposed()) return;

                List<VirtualFile> batch = filesToScan.subList(i,
                        Math.min(i + BATCH_SIZE, filesToScan.size()));
                processBatch(batch, basePath, tools);

                // Yield between batches to let write actions through
                if (i + BATCH_SIZE < filesToScan.size()) {
                    Thread.sleep(YIELD_SLEEP_MS);
                }
            }

            // Build report from cache
            writeReport();
            writeTaskFile();
            syncToHealingDatabase();

            // Refresh project tree icons if problem state changed
            refreshIconsIfChanged();

        } catch (ProcessCanceledException e) {
            // Normal during shutdown
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            LOG.warn("MQL Problems Logger scan failed", e);
        }
    }

    private void processBatch(@NotNull List<VirtualFile> files, @NotNull String basePath,
                              @NotNull List<LocalInspectionTool> tools) throws InterruptedException {
        // Cancellable read with write-action priority: a pending write action (e.g. the user
        // typing) cancels the read via ProgressManager.checkCanceled() and we retry the batch
        // after yielding, so the EDT is never blocked for the duration of a batch.
        boolean success = false;
        while (!success) {
            if (project.isDisposed()) return;
            success = ProgressIndicatorUtils.runInReadActionWithWriteActionPriority(() -> {
                for (VirtualFile vf : files) {
                    if (project.isDisposed()) return;
                    List<ProblemInfo> problems = scanSingleFile(vf, basePath, tools);
                    if (problems != null) {
                        String relativePath = getRelativePath(basePath, vf);
                        cache.put(vf.getUrl(), new CachedFileResult(vf.getModificationStamp(),
                                relativePath, problems));
                    }
                }
            });
            if (!success) {
                // A write action interrupted the read; yield briefly before retrying
                Thread.sleep(YIELD_SLEEP_MS);
            }
        }
    }

    private void refreshIconsIfChanged() {
        Set<String> currentProblemUrls = new HashSet<>();
        for (Map.Entry<String, CachedFileResult> entry : cache.entrySet()) {
            if (!entry.getValue().problems().isEmpty()) {
                currentProblemUrls.add(entry.getKey());
            }
        }

        Set<String> prev = previousProblemUrls;
        if (!currentProblemUrls.equals(prev)) {
            previousProblemUrls = currentProblemUrls;
            ApplicationManager.getApplication().invokeLater(() -> {
                if (!project.isDisposed()) {
                    ProjectView projectView = ProjectView.getInstance(project);
                    projectView.refresh();
                }
            });
        }
    }

    @Nullable
    private List<ProblemInfo> scanSingleFile(@NotNull VirtualFile vf, @NotNull String basePath,
                                              @NotNull List<LocalInspectionTool> tools) {
        PsiManager psiManager = PsiManager.getInstance(project);
        PsiFile psiFile = psiManager.findFile(vf);
        if (psiFile == null) return null;

        InspectionManager inspectionManager = InspectionManager.getInstance(project);
        PsiDocumentManager docManager = PsiDocumentManager.getInstance(project);
        Document doc = docManager.getDocument(psiFile);
        List<ProblemInfo> fileProblems = new ArrayList<>();

        for (LocalInspectionTool tool : tools) {
            ProgressManager.checkCanceled();
            try {
                ProblemDescriptor[] problems = tool.checkFile(psiFile, inspectionManager, false);
                if (problems != null) {
                    for (ProblemDescriptor pd : problems) {
                        PsiElement elem = pd.getPsiElement();
                        int line = -1;
                        if (doc != null && elem != null && elem.isValid()) {
                            line = doc.getLineNumber(elem.getTextOffset()) + 1;
                        }
                        String severity = mapSeverity(pd.getHighlightType());
                        String shortName = tool.getShortName();
                        String hint = null;
                        QuickFix<?>[] fixes = pd.getFixes();
                        if (fixes != null && fixes.length > 0) {
                            hint = fixes[0].getName();
                        }
                        if (hint == null) {
                            hint = FIX_HINTS.get(shortName);
                        }
                        fileProblems.add(new ProblemInfo(line, severity, pd.getDescriptionTemplate(), shortName, hint));
                    }
                }
            } catch (ProcessCanceledException e) {
                throw e;
            } catch (Exception e) {
                LOG.debug("Inspection " + tool.getShortName() + " failed on " + vf.getName(), e);
            }
        }

        fileProblems.sort((a, b) -> {
            int sevCmp = Integer.compare(severityRank(a.severity), severityRank(b.severity));
            return sevCmp != 0 ? sevCmp : Integer.compare(a.line, b.line);
        });

        return fileProblems;
    }

    @NotNull
    private List<LocalInspectionTool> discoverInspections() {
        List<LocalInspectionTool> tools = new ArrayList<>();
        for (LocalInspectionEP ep : LOCAL_INSPECTION_EP.getExtensionList()) {
            if ("MQL4".equals(ep.language)) {
                try {
                    tools.add((LocalInspectionTool) ep.instantiateTool());
                } catch (Exception e) {
                    LOG.debug("Failed to instantiate inspection: " + ep.getShortName(), e);
                }
            }
        }
        return tools;
    }

    private void writeReport() {
        String basePath = project.getBasePath();
        if (basePath == null) return;

        int totalErrors = 0;
        int totalWarnings = 0;
        int totalWeakWarnings = 0;
        List<FileSection> filesWithProblems = new ArrayList<>();
        List<String> cleanFiles = new ArrayList<>();

        for (Map.Entry<String, CachedFileResult> entry : cache.entrySet()) {
            CachedFileResult cached = entry.getValue();
            List<ProblemInfo> problems = cached.problems;

            if (problems.isEmpty()) {
                cleanFiles.add(cached.relativePath);
            } else {
                int worstRank = Integer.MAX_VALUE;
                StringBuilder fileSb = new StringBuilder();
                fileSb.append("\n--- ").append(cached.relativePath)
                        .append(" (").append(problems.size()).append(" problems) ---\n");
                for (ProblemInfo p : problems) {
                    String lineStr = p.line > 0 ? String.valueOf(p.line) : "?";
                    fileSb.append("  Line ").append(lineStr).append(": [").append(p.severity).append("] ")
                            .append(p.message).append(" (").append(p.inspectionName).append(")\n");
                    if (p.fixHint != null && !p.fixHint.isEmpty()) {
                        fileSb.append("    Fix: ").append(p.fixHint).append("\n");
                    }
                    switch (p.severity) {
                        case "ERROR" -> totalErrors++;
                        case "WARNING" -> totalWarnings++;
                        case "WEAK WARNING" -> totalWeakWarnings++;
                    }
                    int rank = severityRank(p.severity);
                    if (rank < worstRank) worstRank = rank;
                }
                filesWithProblems.add(new FileSection(worstRank, problems.size(), fileSb.toString()));
            }
        }

        // Sort: worst severity first, then most problems first
        filesWithProblems.sort((a, b) -> {
            int sevCmp = Integer.compare(a.worstSeverityRank, b.worstSeverityRank);
            return sevCmp != 0 ? sevCmp : Integer.compare(b.problemCount, a.problemCount);
        });

        int total = totalErrors + totalWarnings + totalWeakWarnings;

        StringBuilder sb = new StringBuilder();
        sb.append("=== MQL Problems Report ===\n");
        sb.append("Updated: ").append(LocalDateTime.now().format(TIMESTAMP_FORMAT)).append("\n");
        sb.append("Total: ").append(total).append(" problems (")
                .append(totalErrors).append(" errors, ")
                .append(totalWarnings).append(" warnings, ")
                .append(totalWeakWarnings).append(" weak warnings)\n");

        for (FileSection section : filesWithProblems) {
            sb.append(section.content);
        }

        if (!cleanFiles.isEmpty()) {
            sb.append("\n=== No problems ===\n");
            for (String clean : cleanFiles) {
                sb.append(clean).append("\n");
            }
        }

        Path logPath = Path.of(basePath, LOG_FILE_NAME);
        Path tempPath = Path.of(basePath, LOG_FILE_NAME + ".tmp");

        try {
            Files.writeString(tempPath, sb.toString(), StandardCharsets.UTF_8);
            try {
                Files.move(tempPath, logPath, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(tempPath, logPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            LOG.warn("Failed to write " + LOG_FILE_NAME, e);
            try {
                Files.deleteIfExists(tempPath);
            } catch (IOException ignored) {
            }
        }
    }

    private void writeTaskFile() {
        String basePath = project.getBasePath();
        if (basePath == null) return;

        int totalErrors = 0;
        int totalWarnings = 0;
        int totalWeakWarnings = 0;

        // Collect per-file task entries, sorted by severity then problem count
        List<FileSection> fileSections = new ArrayList<>();
        List<String> cleanFiles = new ArrayList<>();

        // Count by inspection type for summary
        Map<String, Integer> inspectionCounts = new java.util.TreeMap<>();

        for (Map.Entry<String, CachedFileResult> entry : cache.entrySet()) {
            CachedFileResult cached = entry.getValue();
            List<ProblemInfo> problems = cached.problems;

            if (problems.isEmpty()) {
                cleanFiles.add(cached.relativePath);
                continue;
            }

            int worstRank = Integer.MAX_VALUE;
            StringBuilder fileSb = new StringBuilder();
            fileSb.append("\n### ").append(cached.relativePath)
                    .append(" (").append(problems.size()).append(" issues)\n\n");

            for (ProblemInfo p : problems) {
                String lineStr = p.line > 0 ? String.valueOf(p.line) : "?";
                String icon = switch (p.severity) {
                    case "ERROR" -> "!!!";
                    case "WARNING" -> "!!";
                    default -> "!";
                };
                fileSb.append("- [ ] **Line ").append(lineStr).append("** ")
                        .append(icon).append(" ").append(p.message)
                        .append(" `").append(p.inspectionName).append("`\n");
                if (p.fixHint != null && !p.fixHint.isEmpty()) {
                    fileSb.append("  - Fix: ").append(p.fixHint).append("\n");
                }
                switch (p.severity) {
                    case "ERROR" -> totalErrors++;
                    case "WARNING" -> totalWarnings++;
                    case "WEAK WARNING" -> totalWeakWarnings++;
                }
                inspectionCounts.merge(p.inspectionName, 1, Integer::sum);
                int rank = severityRank(p.severity);
                if (rank < worstRank) worstRank = rank;
            }

            fileSections.add(new FileSection(worstRank, problems.size(), fileSb.toString()));
        }

        fileSections.sort((a, b) -> {
            int sevCmp = Integer.compare(a.worstSeverityRank, b.worstSeverityRank);
            return sevCmp != 0 ? sevCmp : Integer.compare(b.problemCount, a.problemCount);
        });

        int total = totalErrors + totalWarnings + totalWeakWarnings;

        StringBuilder sb = new StringBuilder();
        sb.append("# MQL5 Safety Tasks\n\n");
        sb.append("*Auto-generated by RiggWire plugin — ").append(LocalDateTime.now().format(TIMESTAMP_FORMAT)).append("*\n\n");
        sb.append("**").append(total).append(" open issues** — ");
        sb.append(totalErrors).append(" errors, ");
        sb.append(totalWarnings).append(" warnings, ");
        sb.append(totalWeakWarnings).append(" weak warnings\n\n");

        // Summary by inspection type
        sb.append("## Issue Summary\n\n");
        sb.append("| Inspection | Count |\n");
        sb.append("|---|---|\n");
        inspectionCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .forEach(e -> sb.append("| ").append(e.getKey()).append(" | ").append(e.getValue()).append(" |\n"));
        sb.append("\n");

        // File sections
        sb.append("## Tasks by File\n");
        for (FileSection section : fileSections) {
            sb.append(section.content);
        }

        if (!cleanFiles.isEmpty()) {
            sb.append("\n## Clean Files\n\n");
            for (String clean : cleanFiles) {
                sb.append("- [x] ~~").append(clean).append("~~\n");
            }
        }

        Path taskPath = Path.of(basePath, TASKS_FILE_NAME);
        Path tempPath = Path.of(basePath, TASKS_FILE_NAME + ".tmp");

        try {
            Files.writeString(tempPath, sb.toString(), StandardCharsets.UTF_8);
            try {
                Files.move(tempPath, taskPath, StandardCopyOption.REPLACE_EXISTING, StandardCopyOption.ATOMIC_MOVE);
            } catch (AtomicMoveNotSupportedException e) {
                Files.move(tempPath, taskPath, StandardCopyOption.REPLACE_EXISTING);
            }
        } catch (IOException e) {
            LOG.warn("Failed to write " + TASKS_FILE_NAME, e);
            try {
                Files.deleteIfExists(tempPath);
            } catch (IOException ignored) {
            }
        }
    }

    private void syncToHealingDatabase() {
        try {
            HealingDatabase db = HealingDatabase.getInstance(project);
            Map<String, List<HealingDatabase.ProblemSnapshot>> fileProblems = new HashMap<>();
            for (Map.Entry<String, CachedFileResult> entry : cache.entrySet()) {
                String fileUrl = entry.getKey();
                CachedFileResult cached = entry.getValue();
                List<HealingDatabase.ProblemSnapshot> snapshots = new ArrayList<>();
                for (ProblemInfo p : cached.problems()) {
                    snapshots.add(new HealingDatabase.ProblemSnapshot(
                            cached.relativePath(), p.line(), p.severity(),
                            p.message(), p.inspectionName(), p.fixHint()
                    ));
                }
                if (!snapshots.isEmpty()) {
                    fileProblems.put(fileUrl, snapshots);
                }
            }
            db.syncProblems(fileProblems);
        } catch (Exception e) {
            LOG.debug("Failed to sync to healing database", e);
        }
    }

    @NotNull
    private static String getRelativePath(@NotNull String basePath, @NotNull VirtualFile file) {
        String filePath = file.getPath();
        if (filePath.startsWith(basePath)) {
            String rel = filePath.substring(basePath.length());
            if (rel.startsWith("/")) {
                rel = rel.substring(1);
            }
            return rel;
        }
        return filePath;
    }

    @NotNull
    private static String mapSeverity(@NotNull ProblemHighlightType type) {
        return switch (type) {
            case ERROR, GENERIC_ERROR -> "ERROR";
            case GENERIC_ERROR_OR_WARNING, WARNING -> "WARNING";
            case WEAK_WARNING -> "WEAK WARNING";
            default -> "INFO";
        };
    }

    private static int severityRank(String severity) {
        return switch (severity) {
            case "ERROR" -> 0;
            case "WARNING" -> 1;
            case "WEAK WARNING" -> 2;
            default -> 3;
        };
    }

    @Override
    public void dispose() {
        executor.shutdownNow();
        cache.clear();
    }

    private record ProblemInfo(int line, String severity, String message, String inspectionName, String fixHint) {
    }

    private record FileSection(int worstSeverityRank, int problemCount, String content) {
    }

    private record CachedFileResult(long modStamp, String relativePath, List<ProblemInfo> problems) {
    }
}
