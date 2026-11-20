/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package gate;

import com.intellij.codeInspection.InspectionManager;
import com.intellij.codeInspection.LocalInspectionEP;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.codeInspection.ProblemDescriptor;
import com.intellij.openapi.application.WriteAction;
import com.intellij.openapi.progress.ProcessCanceledException;
import com.intellij.openapi.project.RootsChangeRescanningInfo;
import com.intellij.openapi.roots.ex.ProjectRootManagerEx;
import com.intellij.openapi.util.EmptyRunnable;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiNameIdentifierOwner;
import com.intellij.psi.PsiPolyVariantReference;
import com.intellij.psi.PsiReference;
import com.intellij.psi.TokenType;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.IndexingTestUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.reference.MqlIncludeRoots;

import java.io.IOException;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.Charset;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.TreeMap;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Ratchet over real MQL corpora (run by {@code tools/corpus-gate.sh}; a no-op without
 * {@code MQL_CORPORA}). It loads each corpus as project files, with the corpus named
 * {@code include} as the {@code <...>} include root, and measures parse errors, bad characters,
 * how many references resolve, references to declared names that don't, and every MQL inspection's
 * problem count. Gated corpora must not get worse than {@code src/test/resources/gate/corpus-baseline.properties};
 * {@code MQL_GATE_UPDATE=1} rewrites it after a deliberate change. Corpora named {@code report:...}
 * are measured but never gated (a codebase that changes under us).
 *
 * <p>{@code MQL_CORPORA} is {@code name=dir[,dir...];name2=dir...}. MetaQuotes code is read from
 * the local install only; none of it is copied into this repository.</p>
 */
public class CorpusGateTest extends BasePlatformTestCase {

    private static final int SAMPLES = Integer.parseInt(java.util.Objects.requireNonNullElse(System.getenv("MQL_GATE_SAMPLES"), "25"));
    private static final Path BASELINE = Paths.get("src/test/resources/gate/corpus-baseline.properties");
    /**
     * Findings checked by hand to be real, which must keep being reported: {@code corpus.Inspection@path/suffix=min}.
     * Counts per file, never lines or code text (a MetaTrader update moves lines; MetaQuotes code stays out of
     * the repo). The baseline only stops counts rising, so it can't tell a fixed false positive from a check
     * gone blind; this floor can. MQL_GATE_UPDATE never writes it.
     */
    private static final Path MUST_REPORT = Paths.get("src/test/resources/gate/must-report.properties");

    private record Loaded(String corpus, VirtualFile vf) {
        PsiFile file(com.intellij.openapi.project.Project project) {
            return com.intellij.psi.PsiManager.getInstance(project).findFile(vf);
        }
    }

    public void testCorporaDoNotRegress() throws Exception {
        String spec = System.getenv("MQL_CORPORA");
        if (spec == null || spec.isBlank()) {
            return;
        }
        Map<String, List<Path>> corpora = parse(spec);
        List<Loaded> loaded = new ArrayList<>();
        VirtualFile includeRoot = null;
        for (Map.Entry<String, List<Path>> c : corpora.entrySet()) {
            String dirName = c.getKey().replace("report:", "");
            for (Path dir : c.getValue()) {
                List<Path> files;
                try (Stream<Path> s = Files.walk(dir)) {
                    files = s.filter(p -> p.toString().matches("(?i).*\\.(mq5|mqh|mq4)$")).sorted().collect(Collectors.toList());
                }
                for (Path p : files) {
                    if (dirName.equals("include") && !includeWanted(dir.relativize(p).toString())) {
                        continue;
                    }
                    String rel = dirName + "/" + dir.getFileName() + "/" + dir.relativize(p);
                    if (dirName.equals("include")) {
                        rel = "include/" + dir.relativize(p); // the include root keeps <Trade/Trade.mqh> paths
                    }
                    loaded.add(new Loaded(c.getKey(), myFixture.addFileToProject(rel, read(p)).getVirtualFile()));
                }
            }
            if (dirName.equals("include")) {
                includeRoot = myFixture.getTempDirFixture().getFile("include");
            }
        }
        if (includeRoot != null) {
            MqlIncludeRoots.setTestRoots(List.of(includeRoot));
        }
        try {
            WriteAction.run(() -> ProjectRootManagerEx.getInstanceEx(getProject())
                    .makeRootsChange(EmptyRunnable.getInstance(), RootsChangeRescanningInfo.TOTAL_RESCAN));
            IndexingTestUtil.waitUntilIndexesAreReady(getProject());
            measureAndCompare(loaded);
        } finally {
            MqlIncludeRoots.setTestRoots(null);
        }
    }

    private void measureAndCompare(List<Loaded> loaded) throws IOException {
        Map<String, Long> metrics = new TreeMap<>();
        Map<String, List<String>> samples = new TreeMap<>();
        Map<String, Long> perFile = new TreeMap<>(); // corpus.Inspection@path -> count
        Set<String> declared = new HashSet<>();
        for (Loaded l : loaded) {
            for (PsiNameIdentifierOwner n : PsiTreeUtil.findChildrenOfType(l.file(getProject()), PsiNameIdentifierOwner.class)) {
                if (n.getName() != null) {
                    declared.add(n.getName());
                    if (n instanceof com.limemojito.oss.mql.psi.impl.MQL4VarDefinitionElement
                            && (com.limemojito.oss.mql.MqlBuiltinFunctions.isBuiltinName(n.getName())
                            || com.limemojito.oss.mql.doc.MQL4DocumentationProvider.getEntryByText(n.getName()) != null)) {
                        // a variable named like a built-in function is a misparse (MACRO <newline> Print(...);)
                        add(metrics, l.corpus() + ".builtinNamedVariables", 1);
                        sample(samples, l.corpus() + ".builtinNamedVariables", l.vf().getPath() + ":"
                                + line(l.file(getProject()), n) + " " + n.getClass().getSimpleName() + " " + n.getName());
                    }
                }
            }
        }
        List<LocalInspectionTool> tools = new ArrayList<>();
        for (LocalInspectionEP ep : LocalInspectionEP.LOCAL_INSPECTION.getExtensionList()) {
            if ("MQL4".equals(ep.language) && ep.instantiateTool() instanceof LocalInspectionTool tool) {
                tools.add(tool);
            }
        }
        InspectionManager manager = InspectionManager.getInstance(getProject());
        for (Loaded l : loaded) {
            String c = l.corpus();
            PsiFile f = l.file(getProject());
            String where = f.getVirtualFile().getPath();
            add(metrics, c + ".files", 1);
            for (PsiErrorElement e : PsiTreeUtil.findChildrenOfType(f, PsiErrorElement.class)) {
                add(metrics, c + ".parseErrors", 1);
                sample(samples, c + ".parseErrors", where + ":" + line(f, e) + " " + e.getErrorDescription());
            }
            for (PsiElement leaf = PsiTreeUtil.firstChild(f); leaf != null; leaf = PsiTreeUtil.nextLeaf(leaf)) {
                if (leaf.getNode().getElementType() == TokenType.BAD_CHARACTER) {
                    add(metrics, c + ".badChars", 1);
                    sample(samples, c + ".badChars", where + ":" + line(f, leaf) + " '" + leaf.getText() + "'");
                }
            }
            Set<Integer> seen = new HashSet<>();
            for (PsiElement el : PsiTreeUtil.findChildrenOfType(f, PsiElement.class)) {
                for (PsiReference r : el.getReferences()) {
                    int off = el.getTextRange().getStartOffset() + r.getRangeInElement().getStartOffset();
                    if (!seen.add(off)) {
                        continue;
                    }
                    add(metrics, c + ".refs", 1);
                    boolean ok = r.resolve() != null
                            || (r instanceof PsiPolyVariantReference pv && pv.multiResolve(false).length > 0);
                    if (ok) {
                        add(metrics, c + ".resolved", 1);
                    } else if (declared.contains(r.getCanonicalText())) {
                        add(metrics, c + ".unresolvedDeclared", 1);
                        sample(samples, c + ".unresolvedDeclared", where + ":" + line(f, el) + " " + r.getCanonicalText());
                    }
                }
            }
            for (LocalInspectionTool tool : tools) {
                List<ProblemDescriptor> problems;
                try {
                    problems = com.intellij.openapi.progress.ProgressManager.getInstance().runProcess(
                            () -> tool.processFile(f, manager), new com.intellij.openapi.progress.EmptyProgressIndicator());
                } catch (ProcessCanceledException e) {
                    throw e;
                } catch (Throwable t) {
                    add(metrics, c + ".crash." + tool.getShortName(), 1);
                    sample(samples, c + ".crash." + tool.getShortName(), where + " " + t);
                    continue;
                }
                for (ProblemDescriptor p : problems) {
                    add(metrics, c + ".inspection." + tool.getShortName(), 1);
                    add(perFile, c + "." + tool.getShortName() + "@" + where, 1);
                    sample(samples, c + ".inspection." + tool.getShortName(),
                            where + ":" + (p.getLineNumber() + 1) + " " + p.getDescriptionTemplate());
                }
            }
        }
        writeReport(metrics, samples);
        checkMustReport(perFile, loaded);
        compare(metrics);
    }

    private static void checkMustReport(Map<String, Long> perFile, List<Loaded> loaded) throws IOException {
        if (!Files.exists(MUST_REPORT)) {
            return;
        }
        Properties floor = new Properties();
        floor.load(new StringReader(Files.readString(MUST_REPORT)));
        Set<String> corpora = new HashSet<>();
        loaded.forEach(l -> corpora.add(l.corpus()));
        List<String> missing = new ArrayList<>();
        for (String key : new java.util.TreeSet<>(floor.stringPropertyNames())) {
            String corpus = key.substring(0, key.indexOf('.'));
            if (!corpora.contains(corpus)) {
                continue; // that corpus wasn't measured in this run
            }
            String suffix = "/" + key.substring(key.indexOf('@') + 1);
            String prefix = key.substring(0, key.indexOf('@') + 1);
            boolean fileThere = loaded.stream().anyMatch(l -> l.corpus().equals(corpus) && l.vf().getPath().endsWith(suffix));
            long now = perFile.entrySet().stream().filter(e -> e.getKey().startsWith(prefix) && e.getKey().endsWith(suffix))
                    .mapToLong(Map.Entry::getValue).sum();
            long min = Long.parseLong(floor.getProperty(key).trim());
            if (!fileThere) {
                missing.add(key + ": file not in the corpus any more (MetaTrader update?): re-check by hand and edit " + MUST_REPORT);
            } else if (now < min) {
                missing.add(key + ": " + now + " reported, at least " + min + " expected (a check went blind?)");
            }
        }
        assertTrue("known real findings no longer reported:\n" + String.join("\n", missing), missing.isEmpty());
    }

    /** {@code MQL_INCLUDE_ONLY}: comma-separated path prefixes kept from the include corpus (all if unset). */
    private static boolean includeWanted(String rel) {
        String only = System.getenv("MQL_INCLUDE_ONLY");
        if (only == null || only.isBlank()) {
            return true;
        }
        for (String prefix : only.split(",")) {
            if (!prefix.isBlank() && rel.startsWith(prefix.trim())) {
                return true;
            }
        }
        return false;
    }

    /** Lower is better for every metric except resolved; files and refs are context. */
    private static boolean worse(String key, long now, long base) {
        if (key.endsWith(".files") || key.endsWith(".refs")) {
            return false;
        }
        return key.endsWith(".resolved") ? now < base : now > base;
    }

    private void compare(Map<String, Long> metrics) throws IOException {
        Map<String, Long> gated = new TreeMap<>();
        metrics.forEach((k, v) -> {
            if (!k.startsWith("report:")) {
                gated.put(k, v);
            }
        });
        List<String> crashes = gated.keySet().stream().filter(k -> k.contains(".crash.")).toList();
        // a crash is never a baseline: it is a bug, or a broken test sandbox (delete build/idea-sandbox/*/system-test)
        assertTrue("inspections crashed (see build/corpus-gate-report.txt): " + crashes, crashes.isEmpty());
        if ("1".equals(System.getenv("MQL_GATE_UPDATE"))) {
            Properties p = new Properties();
            gated.forEach((k, v) -> p.setProperty(k, Long.toString(v)));
            Files.createDirectories(BASELINE.getParent());
            StringWriter w = new StringWriter();
            p.store(w, "corpus gate baseline; regenerate with MQL_GATE_UPDATE=1 tools/corpus-gate.sh");
            List<String> lines = new ArrayList<>(List.of(w.toString().split("\n")));
            List<String> body = new ArrayList<>(lines.subList(2, lines.size()));
            body.sort(null);
            Files.writeString(BASELINE, lines.get(0) + "\n" + String.join("\n", body) + "\n");
            return;
        }
        assertTrue("no baseline at " + BASELINE.toAbsolutePath() + "; run with MQL_GATE_UPDATE=1", Files.exists(BASELINE));
        Properties base = new Properties();
        base.load(new StringReader(Files.readString(BASELINE)));
        List<String> regressions = new ArrayList<>();
        Set<String> keys = new java.util.TreeSet<>(gated.keySet());
        keys.addAll(base.stringPropertyNames());
        for (String k : keys) {
            if (base.getProperty(k) == null && corpusOf(k, base) == null) {
                continue; // a corpus the baseline doesn't know: measured, not gated
            }
            long now = gated.getOrDefault(k, 0L);
            long was = Long.parseLong(base.getProperty(k, "0"));
            if (worse(k, now, was)) {
                regressions.add(k + ": " + was + " -> " + now);
            }
        }
        assertTrue("corpus gate regressions (see build/corpus-gate-report.txt):\n" + String.join("\n", regressions), regressions.isEmpty());
    }

    private static String corpusOf(String key, Properties base) {
        String corpus = key.substring(0, key.indexOf('.'));
        return base.getProperty(corpus + ".files");
    }

    private static void writeReport(Map<String, Long> metrics, Map<String, List<String>> samples) throws IOException {
        StringBuilder out = new StringBuilder();
        metrics.forEach((k, v) -> out.append(k).append(" = ").append(v).append('\n'));
        out.append("\n# samples (first " + SAMPLES + " per metric; MQL_GATE_SAMPLES to change)\n");
        samples.forEach((k, v) -> {
            out.append("\n[").append(k).append("]\n");
            v.forEach(s -> out.append("  ").append(s).append('\n'));
        });
        Path report = Paths.get("build/corpus-gate-report.txt");
        Files.createDirectories(report.getParent());
        Files.writeString(report, out.toString());
    }

    private static Map<String, List<Path>> parse(String spec) {
        Map<String, List<Path>> out = new LinkedHashMap<>();
        for (String part : spec.split(";")) {
            if (part.isBlank()) {
                continue;
            }
            String[] kv = part.split("=", 2);
            List<Path> dirs = new ArrayList<>();
            for (String d : kv[1].split(",")) {
                Path p = Paths.get(d.trim());
                if (Files.isDirectory(p)) {
                    dirs.add(p);
                }
            }
            if (!dirs.isEmpty()) {
                out.put(kv[0].trim(), dirs);
            }
        }
        // the include corpus loads first so its folder exists before the others are indexed
        Map<String, List<Path>> ordered = new LinkedHashMap<>();
        out.forEach((k, v) -> {
            if (k.equals("include")) {
                ordered.put(k, v);
            }
        });
        ordered.putAll(out);
        return ordered;
    }

    private static String read(Path p) throws IOException {
        byte[] b = Files.readAllBytes(p);
        Charset cs = b.length > 1 && (b[0] & 0xff) == 0xFF && (b[1] & 0xff) == 0xFE ? StandardCharsets.UTF_16LE : StandardCharsets.UTF_8;
        return new String(b, cs).replace("﻿", "").replace("\r\n", "\n");
    }

    private static int line(PsiFile f, PsiElement e) {
        return f.getViewProvider().getDocument().getLineNumber(e.getTextRange().getStartOffset()) + 1;
    }

    private static void add(Map<String, Long> m, String k, long n) {
        m.merge(k, n, Long::sum);
    }

    private static void sample(Map<String, List<String>> s, String k, String v) {
        List<String> l = s.computeIfAbsent(k, x -> new ArrayList<>());
        if (l.size() < SAMPLES) {
            l.add(v);
        }
    }
}
