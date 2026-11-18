/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package gate;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.intellij.codeInsight.daemon.impl.HighlightInfo;
import com.intellij.codeInspection.LocalInspectionEP;
import com.intellij.codeInspection.LocalInspectionTool;
import com.intellij.lang.annotation.HighlightSeverity;
import com.intellij.openapi.application.WriteAction;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.project.RootsChangeRescanningInfo;
import com.intellij.openapi.roots.ex.ProjectRootManagerEx;
import com.intellij.openapi.util.EmptyRunnable;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiErrorElement;
import com.intellij.psi.PsiFile;
import com.intellij.psi.PsiManager;
import com.intellij.psi.util.PsiTreeUtil;
import com.intellij.testFramework.IndexingTestUtil;
import com.intellij.testFramework.fixtures.BasePlatformTestCase;
import com.limemojito.oss.mql.reference.MqlIncludeRoots;
import com.limemojito.oss.mql.reference.MqlVisibleNames;
import gate.HarnessCompare.MetaEditorDiag;
import gate.HarnessCompare.Outcome;
import gate.HarnessCompare.PluginDiag;
import gate.HarnessCompare.Result;
import gate.HarnessCompare.Verdict;

import java.io.IOException;
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
 * Scores the plugin against MetaEditor's verdicts (specs/001-metaeditor-harness; run by
 * {@code tools/harness/harness.sh}, a no-op without {@code MQL_HARNESS}). For each source in
 * {@code tools/harness/corpus.json}, loads its files plus the Standard Library as project files,
 * highlights every judged program and the source headers it includes at ERROR severity (parser,
 * annotators and the default-on error inspections), compares with the verdicts the referee stored
 * ({@code metaeditor_verdicts.py}, index {@code ~/.cache/mqlidea-harness/current.json}) and writes
 * {@code build/harness-report.md}. Open-source counts may not rise above
 * {@code src/test/resources/gate/harness-baseline.properties}; {@code MQL_HARNESS_UPDATE=1}
 * rewrites it. Held-out sources are scored only with {@code MQL_HARNESS_HELDOUT=1}.
 */
public class HarnessTest extends BasePlatformTestCase {

    private static final Path BASELINE = Paths.get("src/test/resources/gate/harness-baseline.properties");
    private static final Path REPORT = Paths.get("build/harness-report.md");
    private static final List<String> STDLIB = List.of("Arrays", "Canvas", "ChartObjects", "Charts", "Controls", "Expert",
            "Files", "Generic", "Graphics", "Indicators", "Math", "OpenCL", "Strings", "Tools", "Trade", "WinAPI",
            "Object.mqh", "StdLibErr.mqh", "VirtualKeys.mqh", "MovingAverages.mqh");

    public void testPluginAgainstMetaEditor() throws Exception {
        String corpusPath = System.getenv("MQL_HARNESS");
        if (corpusPath == null || corpusPath.isBlank()) {
            return;
        }
        Path home = Paths.get(System.getProperty("user.home"));
        Path store = Paths.get(System.getenv().getOrDefault("MQL_HARNESS_STORE", home.resolve(".cache/mqlidea-harness/verdicts").toString()));
        JsonObject current = JsonParser.parseString(Files.readString(store.getParent().resolve("current.json"))).getAsJsonObject();
        Path mql5 = Paths.get(System.getenv().getOrDefault("MT5_MQL5",
                home.resolve("Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5").toString()));
        boolean heldout = "1".equals(System.getenv("MQL_HARNESS_HELDOUT"));

        Map<String, Map<String, String>> keys = new TreeMap<>(); // source -> program -> key
        for (JsonElement e : current.getAsJsonArray("programs")) {
            JsonObject o = e.getAsJsonObject();
            keys.computeIfAbsent(o.get("source").getAsString(), k -> new TreeMap<>()).put(o.get("program").getAsString(), o.get("key").getAsString());
        }
        int build = current.get("metaeditor_build").getAsInt();

        enableDefaultErrorInspections();
        loadMetaTraderInclude(mql5.resolve("Include"));
        List<Result> results = new ArrayList<>();
        Map<String, String> roles = new TreeMap<>();
        long highlightMillis = 0;
        int highlighted = 0;
        for (JsonElement e : JsonParser.parseString(Files.readString(Paths.get(corpusPath))).getAsJsonObject().getAsJsonArray("sources")) {
            JsonObject source = e.getAsJsonObject();
            String name = source.get("name").getAsString();
            String role = source.get("role").getAsString();
            if (role.equals("heldout") && !heldout || !keys.containsKey(name)) {
                continue;
            }
            roles.put(name, role);
            Path repo = Paths.get(source.get("path").getAsString().replaceFirst("^~", home.toString()));
            boolean allInclude = source.has("link_metatrader_include") && source.get("link_metatrader_include").getAsBoolean();
            Loaded loaded = load(name, repo, strings(source.getAsJsonArray("include_roots")), allInclude);
            try {
                for (Map.Entry<String, String> program : keys.get(name).entrySet()) {
                    Verdict verdict = readVerdict(store, program.getValue(), name, program.getKey(), build);
                    VirtualFile vf = loaded.byRepoPath().get(program.getKey());
                    if (verdict.excluded() || vf == null) {
                        results.add(HarnessCompare.classify(verdict.excluded() ? verdict
                                : new Verdict(name, program.getKey(), "no-log", List.of()), List.of()));
                        continue;
                    }
                    long start = System.nanoTime();
                    List<PluginDiag> plugin = pluginErrors(vf, loaded);
                    highlightMillis += (System.nanoTime() - start) / 1_000_000;
                    highlighted++;
                    results.add(HarnessCompare.classify(withRepoFiles(verdict), plugin));
                }
            } finally {
                unload(loaded);
            }
        }
        String report = HarnessCompare.report(results, roles)
                + "\n## Run\n\n- MetaEditor build: " + build
                + "\n- referee run complete: " + current.get("complete").getAsBoolean()
                + "\n- MetaTrader's MQL5 folder untouched by the referee: " + current.get("metatrader_untouched").getAsBoolean()
                + "\n- MQL4 sources: no referee (MetaTrader 5's MetaEditor can't compile MQL4)\n";
        Files.createDirectories(REPORT.getParent());
        Files.writeString(REPORT, report, StandardCharsets.UTF_8);
        System.out.println("harness: " + highlighted + " programs highlighted in " + highlightMillis + " ms ("
                + (highlighted == 0 ? 0 : highlightMillis / highlighted) + " ms each); report " + REPORT);
        ratchet(results, roles);
    }

    /** One source as project files: the repo under src/NAME, MetaTrader's Include (or its Standard Library) under include/. */
    private record Loaded(VirtualFile root, Map<String, VirtualFile> byRepoPath, Map<VirtualFile, String> repoPathOf) {
    }

    /** MetaTrader's Include once: the Standard Library under include/, everything else (the user's own headers) under include-user/. */
    private void loadMetaTraderInclude(Path mtInclude) throws IOException {
        for (Path p : mqlFiles(mtInclude)) {
            String rel = mtInclude.relativize(p).toString();
            boolean stdlib = STDLIB.stream().anyMatch(s -> rel.equals(s) || rel.startsWith(s + "/"));
            myFixture.addFileToProject((stdlib ? "include/" : "include-user/") + rel, read(p));
        }
    }

    private Loaded load(String name, Path repo, List<String> includeRoots, boolean allInclude) throws IOException {
        Map<String, VirtualFile> byRepoPath = new TreeMap<>();
        Map<VirtualFile, String> repoPathOf = new LinkedHashMap<>();
        String base = "src/" + name.replace(' ', '_');
        for (Path p : mqlFiles(repo)) {
            String rel = repo.relativize(p).toString();
            VirtualFile vf = myFixture.addFileToProject(base + "/" + rel, read(p)).getVirtualFile();
            byRepoPath.put(rel, vf);
            repoPathOf.put(vf, rel);
        }
        List<VirtualFile> roots = new ArrayList<>();
        roots.add(myFixture.getTempDirFixture().getFile("include"));
        VirtualFile user = myFixture.getTempDirFixture().getFile("include-user");
        if (allInclude && user != null) {
            roots.add(user);
        }
        for (String r : includeRoots) {
            VirtualFile dir = myFixture.getTempDirFixture().getFile(r.equals(".") ? base : base + "/" + r);
            if (dir != null) {
                roots.add(dir);
            }
        }
        MqlIncludeRoots.setTestRoots(roots);
        WriteAction.run(() -> ProjectRootManagerEx.getInstanceEx(getProject())
                .makeRootsChange(EmptyRunnable.getInstance(), RootsChangeRescanningInfo.TOTAL_RESCAN));
        IndexingTestUtil.waitUntilIndexesAreReady(getProject());
        return new Loaded(myFixture.getTempDirFixture().getFile(base), byRepoPath, repoPathOf);
    }

    private void unload(Loaded loaded) throws IOException {
        MqlIncludeRoots.setTestRoots(null);
        WriteAction.runAndWait(() -> {
            if (loaded.root() != null) {
                loaded.root().delete(this);
            }
        });
    }

    /** Errors the plugin reports in {@code program} and in the source's own headers it includes. */
    private List<PluginDiag> pluginErrors(VirtualFile program, Loaded loaded) {
        PsiFile programPsi = PsiManager.getInstance(getProject()).findFile(program);
        Set<VirtualFile> files = new HashSet<>();
        files.add(program);
        if (programPsi != null) {
            for (PsiFile f : MqlVisibleNames.includeClosure(programPsi)) {
                if (f.getVirtualFile() != null && loaded.repoPathOf().containsKey(f.getVirtualFile())) {
                    files.add(f.getVirtualFile());
                }
            }
        }
        List<PluginDiag> out = new ArrayList<>();
        for (VirtualFile vf : files.stream().sorted((a, b) -> a.getPath().compareTo(b.getPath())).toList()) {
            myFixture.openFileInEditor(vf);
            PsiFile psi = myFixture.getFile();
            Document doc = PsiDocumentManager.getInstance(getProject()).getDocument(psi);
            Set<Integer> parseErrorOffsets = PsiTreeUtil.findChildrenOfType(psi, PsiErrorElement.class).stream()
                    .map(x -> x.getTextRange().getStartOffset()).collect(Collectors.toSet());
            for (HighlightInfo info : myFixture.doHighlighting(HighlightSeverity.ERROR)) {
                if (info.getSeverity().compareTo(HighlightSeverity.ERROR) < 0 || doc == null) {
                    continue;
                }
                String tool = info.getInspectionToolId();
                String kind = tool != null ? "inspection" : parseErrorOffsets.contains(info.getStartOffset()) ? "parse" : "annotator";
                String id = tool != null ? tool : kind.equals("parse") ? "PsiErrorElement" : "annotator";
                out.add(new PluginDiag(loaded.repoPathOf().get(vf), doc.getLineNumber(info.getStartOffset()) + 1, kind, id,
                        String.valueOf(info.getDescription())));
            }
        }
        return out;
    }

    private void enableDefaultErrorInspections() {
        List<LocalInspectionTool> tools = new ArrayList<>();
        for (LocalInspectionEP ep : LocalInspectionEP.LOCAL_INSPECTION.getExtensionList()) {
            if ("MQL4".equals(ep.language) && ep.enabledByDefault && "ERROR".equalsIgnoreCase(ep.level)
                    && ep.instantiateTool() instanceof LocalInspectionTool tool) {
                tools.add(tool);
            }
        }
        myFixture.enableInspections(tools.toArray(new LocalInspectionTool[0]));
    }

    private static Verdict readVerdict(Path store, String key, String source, String program, int build) throws IOException {
        Path p = store.resolve(key + ".json");
        if (!Files.exists(p)) {
            return new Verdict(source, program, "no-log", List.of());
        }
        JsonObject v = JsonParser.parseString(Files.readString(p)).getAsJsonObject();
        assertEquals("verdict from another MetaEditor build (FR-020): " + p, build, v.get("metaeditor_build").getAsInt());
        if ("excluded".equals(v.get("status").getAsString())) {
            return new Verdict(source, program, v.get("excluded_reason").getAsString(), List.of());
        }
        List<MetaEditorDiag> diags = new ArrayList<>();
        for (JsonElement d : v.getAsJsonArray("diagnostics")) {
            JsonObject o = d.getAsJsonObject();
            diags.add(new MetaEditorDiag(o.get("file").getAsString(), o.get("line").getAsInt(),
                    "error".equals(o.get("severity").getAsString()), o.get("code").getAsInt(), o.get("message").getAsString()));
        }
        return new Verdict(source, program, null, diags);
    }

    /** MetaEditor's errors inside the Standard Library or unknown files never match a plugin file: dropped from the comparison. */
    private static Verdict withRepoFiles(Verdict v) {
        return new Verdict(v.source(), v.program(), v.excludedReason(), v.diagnostics().stream()
                .filter(d -> !d.file().startsWith("<")).toList());
    }

    private static void ratchet(List<Result> results, Map<String, String> roles) throws IOException {
        Map<Outcome, Long> open = HarnessCompare.counts(results.stream().filter(r -> "open".equals(roles.get(r.source()))).toList());
        Properties now = new Properties();
        open.forEach((o, n) -> now.setProperty("open." + HarnessCompare.label(o), String.valueOf(n)));
        if ("1".equals(System.getenv("MQL_HARNESS_UPDATE")) || !Files.exists(BASELINE)) {
            StringBuilder sb = new StringBuilder("# MetaEditor harness baseline (counts only). MQL_HARNESS_UPDATE=1 tools/harness/harness.sh rewrites it.\n");
            now.stringPropertyNames().stream().sorted().forEach(k -> sb.append(k).append('=').append(now.getProperty(k)).append('\n'));
            Files.writeString(BASELINE, sb.toString());
            return;
        }
        Properties base = new Properties();
        try (var in = Files.newBufferedReader(BASELINE)) {
            base.load(in);
        }
        List<String> worse = new ArrayList<>();
        for (String k : List.of("open.false-error", "open.missed-error", "open.disjoint-errors")) {
            long was = Long.parseLong(base.getProperty(k, "0"));
            long is = Long.parseLong(now.getProperty(k, "0"));
            if (is > was) {
                worse.add(k + ": " + was + " -> " + is);
            }
        }
        assertTrue("harness regressions (see " + REPORT + "):\n" + String.join("\n", worse), worse.isEmpty());
    }

    private static List<Path> mqlFiles(Path dir) throws IOException {
        if (!Files.isDirectory(dir)) {
            return List.of();
        }
        try (Stream<Path> s = Files.walk(dir)) {
            return s.filter(p -> !p.toString().contains("/.git/") && p.toString().matches("(?i).*\\.(mq5|mqh)$")).sorted().toList();
        }
    }

    private static List<String> strings(JsonArray a) {
        List<String> out = new ArrayList<>();
        a.forEach(x -> out.add(x.getAsString()));
        return out;
    }

    private static String read(Path p) throws IOException {
        byte[] b = Files.readAllBytes(p);
        if (b.length >= 2 && (b[0] & 0xff) == 0xff && (b[1] & 0xff) == 0xfe) {
            return new String(b, 2, b.length - 2, StandardCharsets.UTF_16LE);
        }
        return new String(b, StandardCharsets.UTF_8);
    }
}
