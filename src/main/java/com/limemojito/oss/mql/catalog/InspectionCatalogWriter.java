/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package com.limemojito.oss.mql.catalog;

import com.intellij.openapi.diagnostic.Logger;
import com.intellij.openapi.project.Project;
import com.limemojito.oss.mql.inspection.MqlProblemsLoggerService;
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
 * Writes {@code docs/MQL_INSPECTION_CATALOG.md}: a human triage document listing every current
 * inspection finding, grouped by file then line. Rehomed from the legacy AI-healing pipeline's
 * {@code HealingCatalogWriter} per {@code docs/REVAMP_PLAN.md} Phase 2 &mdash; this version has no
 * dependency on any database, diff, or AI-generated content. It is fed directly by the slim
 * {@link MqlProblemsLoggerService}'s in-memory problem cache and is generated on demand (via the
 * "Generate MQL Inspection Catalog" action), not on a startup timer.
 *
 * <p>Best-effort: every failure is swallowed and logged so catalog generation can never disrupt
 * the caller. Writes only into the project's existing {@code docs/} folder and only touches this
 * one markdown file &mdash; never any {@code .mq5}/{@code .mqh} source.</p>
 */
public final class InspectionCatalogWriter {

    private static final Logger LOG = Logger.getInstance(InspectionCatalogWriter.class);
    private static final String REL_PATH = "docs/MQL_INSPECTION_CATALOG.md";
    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss z");

    private InspectionCatalogWriter() {
    }

    /**
     * Regenerates the catalog for {@code project} from the current contents of
     * {@link MqlProblemsLoggerService}. Safe to call from any background thread; performs no
     * read actions and touches no PSI or the EDT (the caller is responsible for having already
     * completed any scan it wants reflected in the catalog).
     */
    public static void write(@NotNull Project project, @NotNull MqlProblemsLoggerService loggerService) {
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

            List<MqlProblemsLoggerService.Problem> problems = loggerService.getCurrentProblems();

            String content = render(problems);

            Path target = docs.resolve("MQL_INSPECTION_CATALOG.md");
            Path tmp = docs.resolve(".MQL_INSPECTION_CATALOG.md.tmp");
            Files.writeString(tmp, content, StandardCharsets.UTF_8);
            Files.move(tmp, target, StandardCopyOption.REPLACE_EXISTING);
            LOG.info("Inspection catalog written: " + REL_PATH + " (" + problems.size() + " problems)");
        } catch (IOException | RuntimeException e) {
            LOG.warn("Failed to write inspection catalog (non-fatal)", e);
        }
    }

    @NotNull
    private static String render(@NotNull List<MqlProblemsLoggerService.Problem> problems) {
        // Group by file (sorted), each file's problems ordered by line.
        Map<String, List<MqlProblemsLoggerService.Problem>> byFile = new TreeMap<>();
        for (MqlProblemsLoggerService.Problem p : problems) {
            byFile.computeIfAbsent(p.filePath(), k -> new ArrayList<>()).add(p);
        }
        for (List<MqlProblemsLoggerService.Problem> list : byFile.values()) {
            list.sort(Comparator.comparingInt(MqlProblemsLoggerService.Problem::line));
        }

        StringBuilder sb = new StringBuilder(1 << 16);
        sb.append("# RIGGWIRE MQL — Inspection Catalog\n\n");
        sb.append("> **Generated:** ").append(ZonedDateTime.now().format(STAMP))
                .append("  ·  on-demand via the \"Generate MQL Inspection Catalog\" action.\n")
                .append("> **Snapshot:** ").append(problems.size()).append(" findings across ")
                .append(byFile.size()).append(" files.\n\n");
        sb.append("---\n\n");

        sb.append("## Read this before triaging\n\n");
        sb.append("1. **No AI, no database.** This catalog is a plain listing of the plugin's own inspection ")
                .append("findings for the current project state — nothing here is AI-generated, and there is ")
                .append("no suggested fix or diff to apply. It is a human triage document only.\n");
        sb.append("2. **Snapshot, not live.** Regenerate the catalog (re-run the action) after fixing issues ")
                .append("or editing files; it does not update automatically.\n");
        sb.append("3. **Overlaps.** A line may carry several inspections; reconcile per file when triaging.\n\n");
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
            for (MqlProblemsLoggerService.Problem p : byFile.get(fp)) {
                sb.append("### ").append(fp).append(':').append(p.line())
                        .append(" — `").append(p.inspectionName()).append("`\n\n");
                sb.append("- **Severity:** ").append(p.severity()).append('\n');
                sb.append("- **Message:** ").append(oneLine(p.message())).append('\n');
                if (p.fixHint() != null && !p.fixHint().isBlank()) {
                    sb.append("- **Fix hint:** ").append(oneLine(p.fixHint())).append('\n');
                }
                sb.append('\n');
            }
            sb.append("---\n\n");
        }

        // Appendix A — by inspection.
        Map<String, Integer> byInspection = new LinkedHashMap<>();
        for (MqlProblemsLoggerService.Problem p : problems) {
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
        sb.append("## Appendix B — problems by file\n\n| File | Problems |\n|---|---|\n");
        for (String fp : files) {
            sb.append("| ").append(fp).append(" | ").append(byFile.get(fp).size()).append(" |\n");
        }

        return sb.toString();
    }

    /** Collapses newlines so a message/hint stays on one markdown bullet line. */
    @NotNull
    private static String oneLine(@NotNull String s) {
        return s.replace('\r', ' ').replace('\n', ' ').trim();
    }
}
