/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.healing;

import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.healing.db.HealingDatabase;
import com.limemojito.oss.mql.healing.db.ProblemRecord;
import org.jetbrains.annotations.NotNull;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 * Writes {@code docs/MQL_HEALING_CATALOG.md}: an ordered, detailed catalog of every
 * unresolved problem and its suggested fix, straight from the healing database. Called at
 * the end of each healing pass so the catalog stays current with zero manual steps.
 *
 * <p>Best-effort: every failure is swallowed and logged so catalog generation can never
 * disrupt a healing cycle. Writes only into the project's existing {@code docs/} folder and
 * only touches this one markdown file — never any {@code .mq5}/{@code .mqh} source.</p>
 */
public final class HealingCatalogWriter {

    private static final Logger LOG = Logger.getInstance(HealingCatalogWriter.class);
    private static final String REL_PATH = "docs/MQL_HEALING_CATALOG.md";
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z");

    private HealingCatalogWriter() {
    }

    /**
     * Regenerates the catalog for {@code project} from {@code db}. Safe to call from any
     * background thread; performs no read actions and touches no PSI or the EDT.
     */
    public static void write(@NotNull Project project, @NotNull HealingDatabase db) {
        try {
            String basePath = project.getBasePath();
            if (basePath == null) {
                return;
            }
            Path docs = Path.of(basePath, "docs");
            if (!Files.isDirectory(docs)) {
                // Only ever write into an existing docs/ folder; do not create project structure.
                return;
            }

            List<ProblemRecord> problems = db.getUnresolvedProblems();
            Map<Long, String> diffs = db.getLatestDiffsByProblem();

            String content = render(problems, diffs);

            Path target = docs.resolve("MQL_HEALING_CATALOG.md");
            Path tmp = docs.resolve(".MQL_HEALING_CATALOG.md.tmp");
            Files.writeString(tmp, content, StandardCharsets.UTF_8);
            Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            LOG.info("Healing catalog written: " + REL_PATH + " (" + problems.size() + " problems, "
                    + diffs.size() + " fixes)");
        } catch (IOException | RuntimeException e) {
            LOG.warn("Failed to write healing catalog (non-fatal)", e);
        }
    }

    @NotNull
    private static String render(@NotNull List<ProblemRecord> problems, @NotNull Map<Long, String> diffs) {
        // Group by file (sorted), each file's problems ordered by line then id.
        Map<String, List<ProblemRecord>> byFile = new TreeMap<>();
        for (ProblemRecord p : problems) {
            byFile.computeIfAbsent(p.filePath(), k -> new ArrayList<>()).add(p);
        }
        for (List<ProblemRecord> list : byFile.values()) {
            list.sort(Comparator.comparingInt(ProblemRecord::line).thenComparingLong(ProblemRecord::id));
        }

        int withFix = 0;
        for (ProblemRecord p : problems) {
            if (diffs.containsKey(p.id())) {
                withFix++;
            }
        }

        StringBuilder sb = new StringBuilder(1 << 16);
        sb.append("# RIGGWIRE-EA-LIVE — MQL Code-Healing Catalog\n\n");
        sb.append("> **Generated:** ").append(ZonedDateTime.now().format(STAMP))
                .append("  ·  auto-written by the RIGGWIRE MQL plugin at the end of each healing pass.\n")
                .append("> **Snapshot:** ").append(problems.size()).append(" unresolved problems · ")
                .append(withFix).append(" with a suggested fix · ").append(byFile.size()).append(" files\n>\n")
                .append("> Regenerates automatically as healing runs — no manual step.\n\n");
        sb.append("---\n\n");

        sb.append("## ⚠️ Read this before applying anything\n\n");
        sb.append("1. **Governance.** `RIGGWIRE-EA-LIVE/CLAUDE.md` forbids direct create/modify/delete of ")
                .append("`.mq5`/`.mqh` source outside the `ea-code-gate` / os-eco pipeline — including the ")
                .append("plugin's \"Apply AI fix\" button. Treat these diffs as **input to `ea-code-gate`**, not a ")
                .append("patch set to apply raw.\n");
        sb.append("2. **AI suggestions, not verified fixes.** None are compiled or reviewed by default; review ")
                .append("each diff before staging it.\n");
        sb.append("3. **Overlaps.** A line may carry several inspections; reconcile per file before staging.\n\n");
        sb.append("| Marker | Meaning |\n|---|---|\n")
                .append("| 🔧 fix ready | A suggested diff was generated (below). Not compile-verified. |\n")
                .append("| — | No fix generated yet (still in the healing queue). |\n\n");
        sb.append("---\n\n## Contents\n\n");

        // TOC with explicit, renderer-independent anchors.
        int idx = 0;
        List<String> files = new ArrayList<>(byFile.keySet());
        for (String fp : files) {
            idx++;
            sb.append("- [`").append(fp).append("`](#f-").append(idx).append(") — ")
                    .append(byFile.get(fp).size()).append(" problems\n");
        }
        sb.append("\n---\n\n");

        // Per-file detail.
        idx = 0;
        for (String fp : files) {
            idx++;
            sb.append("## <a id=\"f-").append(idx).append("\"></a> `").append(fp).append("`\n\n");
            for (ProblemRecord p : byFile.get(fp)) {
                String diff = diffs.get(p.id());
                boolean hasFix = diff != null;
                sb.append("### ").append(fp).append(':').append(p.line())
                        .append(" — `").append(p.inspectionName()).append("`\n\n");
                sb.append("- **Severity:** ").append(p.severity()).append('\n');
                sb.append("- **Problem #:** ").append(p.id())
                        .append("  ·  **Status:** ").append(hasFix ? "🔧 fix ready" : "—").append('\n');
                sb.append("- **Message:** ").append(oneLine(p.message())).append('\n');
                if (p.fixHint() != null && !p.fixHint().isBlank()) {
                    sb.append("- **Fix hint:** ").append(oneLine(p.fixHint())).append('\n');
                }
                sb.append('\n');
                if (hasFix) {
                    sb.append("**Suggested fix:**\n\n```diff\n").append(stripFences(diff)).append("\n```\n\n");
                } else {
                    sb.append("_No fix generated yet._\n\n");
                }
            }
            sb.append("---\n\n");
        }

        // Appendix A — by inspection.
        Map<String, Integer> byInspection = new LinkedHashMap<>();
        for (ProblemRecord p : problems) {
            byInspection.merge(p.inspectionName(), 1, Integer::sum);
        }
        List<Map.Entry<String, Integer>> insp = new ArrayList<>(byInspection.entrySet());
        insp.sort(Map.Entry.<String, Integer>comparingByValue().reversed());
        sb.append("## Appendix A — problems by inspection type\n\n| Inspection | Count |\n|---|---|\n");
        for (Map.Entry<String, Integer> e : insp) {
            sb.append("| ").append(e.getKey()).append(" | ").append(e.getValue()).append(" |\n");
        }
        sb.append('\n');

        // Appendix B — by file.
        sb.append("## Appendix B — problems by file\n\n| File | Problems | With fix |\n|---|---|---|\n");
        for (String fp : files) {
            List<ProblemRecord> list = byFile.get(fp);
            int fixes = 0;
            for (ProblemRecord p : list) {
                if (diffs.containsKey(p.id())) {
                    fixes++;
                }
            }
            sb.append("| ").append(fp).append(" | ").append(list.size()).append(" | ").append(fixes).append(" |\n");
        }

        return sb.toString();
    }

    /** Collapses newlines so a message/hint stays on one markdown bullet line. */
    @NotNull
    private static String oneLine(@NotNull String s) {
        return s.replace('\r', ' ').replace('\n', ' ').trim();
    }

    /**
     * Drops any stray markdown fence line from a stored diff so it cannot prematurely close the
     * catalog's ```diff block. A valid unified diff never contains a line beginning with ```.
     */
    @NotNull
    private static String stripFences(@NotNull String diff) {
        StringBuilder out = new StringBuilder(diff.length());
        for (String line : diff.split("\n", -1)) {
            if (line.startsWith("```")) {
                continue;
            }
            if (out.length() > 0) {
                out.append('\n');
            }
            out.append(line);
        }
        return out.toString().strip();
    }
}
