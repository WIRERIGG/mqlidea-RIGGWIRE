/*
 * Copyright (c) 2026.  Lime Mojito Pty Ltd, Investflow.ru.
 * Modified 2026 by RIGGWIRE Trading Systems (fork; see git history for changes).
 * This code is copyright under GPL3.  Please refer to the LICENSE.txt file in the base of this code repository.
 */

package gate;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.TreeMap;
import java.util.stream.Collectors;

/**
 * Compares MetaEditor's verdict on a program with the plugin's (specs/001-metaeditor-harness,
 * data-model.md). Pure: no IDE, no MetaEditor, so the scoring rules are unit-tested on their own.
 * The rules are frozen there; changing one is its own commit with before/after numbers (FR-022).
 */
final class HarnessCompare {

    /** A plugin error within this many lines of a MetaEditor error, in the same file, matches it. */
    static final int LINE_TOLERANCE = 1;

    enum Outcome { AGREE_CLEAN, AGREE_ERRORS, DISJOINT_ERRORS, FALSE_ERROR, MISSED_ERROR, EXCLUDED }

    /** One MetaEditor diagnostic; {@code file} is relative to the program's source. */
    record MetaEditorDiag(String file, int line, boolean error, int code, String message) {
    }

    /** One plugin error: {@code kind} is parse, annotator or inspection; {@code id} names the check. */
    record PluginDiag(String file, int line, String kind, String id, String message) {
    }

    /** MetaEditor's verdict on one program (with its headers), or why there is none. */
    record Verdict(String source, String program, String excludedReason, List<MetaEditorDiag> diagnostics) {
        boolean excluded() {
            return excludedReason != null;
        }
    }

    /** One program's comparison: the outcome and the disagreement kinds it contributes. */
    record Result(String source, String program, Outcome outcome, String excludedReason, List<Example> kinds) {
    }

    /** A disagreement kind with the place it was seen first. */
    record Example(String kind, String file, int line) {
    }

    private HarnessCompare() {
    }

    static Result classify(Verdict verdict, List<PluginDiag> plugin) {
        if (verdict.excluded()) {
            return new Result(verdict.source(), verdict.program(), Outcome.EXCLUDED, verdict.excludedReason(), List.of());
        }
        List<MetaEditorDiag> me = verdict.diagnostics().stream().filter(MetaEditorDiag::error).toList();
        if (me.isEmpty() && plugin.isEmpty()) {
            return new Result(verdict.source(), verdict.program(), Outcome.AGREE_CLEAN, null, List.of());
        }
        List<Example> kinds = new ArrayList<>();
        Outcome outcome;
        if (me.isEmpty()) {
            outcome = Outcome.FALSE_ERROR;
            kinds.addAll(firstPluginErrorPerFile(plugin));
        } else if (plugin.isEmpty()) {
            outcome = Outcome.MISSED_ERROR;
            kinds.addAll(firstMetaEditorErrorPerFile(me));
        } else if (plugin.stream().anyMatch(p -> me.stream().anyMatch(m -> matches(p, m)))) {
            outcome = Outcome.AGREE_ERRORS;
        } else {
            outcome = Outcome.DISJOINT_ERRORS;
            kinds.addAll(firstPluginErrorPerFile(plugin));
            kinds.addAll(firstMetaEditorErrorPerFile(me));
        }
        return new Result(verdict.source(), verdict.program(), outcome, null, List.copyOf(kinds));
    }

    static boolean matches(PluginDiag p, MetaEditorDiag m) {
        return p.file().equals(m.file()) && Math.abs(p.line() - m.line()) <= LINE_TOLERANCE;
    }

    /** First error per file only: MetaEditor cascades after one syntax error, the plugin recovers. */
    private static List<Example> firstPluginErrorPerFile(List<PluginDiag> plugin) {
        Map<String, PluginDiag> first = new TreeMap<>();
        plugin.stream().sorted(Comparator.comparing(PluginDiag::file).thenComparingInt(PluginDiag::line))
                .forEach(p -> first.putIfAbsent(p.file(), p));
        return first.values().stream()
                .map(p -> new Example("plugin:" + p.kind() + ":" + p.id(), p.file(), p.line())).toList();
    }

    private static List<Example> firstMetaEditorErrorPerFile(List<MetaEditorDiag> me) {
        Map<String, MetaEditorDiag> first = new TreeMap<>();
        me.stream().sorted(Comparator.comparing(MetaEditorDiag::file).thenComparingInt(MetaEditorDiag::line))
                .forEach(m -> first.putIfAbsent(m.file(), m));
        return first.values().stream()
                .map(m -> new Example("metaeditor:" + m.code() + " " + m.message(), m.file(), m.line())).toList();
    }

    /** Headline counts for the results of one role (or all), every outcome present even at zero. */
    static Map<Outcome, Long> counts(List<Result> results) {
        Map<Outcome, Long> counts = new LinkedHashMap<>();
        for (Outcome o : Outcome.values()) {
            counts.put(o, 0L);
        }
        results.forEach(r -> counts.merge(r.outcome(), 1L, Long::sum));
        return counts;
    }

    /**
     * The report text: headline over scored sources, a table per source, disagreement kinds ranked by
     * programs affected (up to 5 examples each), exclusions by reason. Everything is sorted and nothing
     * time-dependent is printed, so unchanged inputs give the same bytes (FR-013).
     */
    static String report(List<Result> results, Map<String, String> roleBySource) {
        List<Result> sorted = results.stream()
                .sorted(Comparator.comparing(Result::source).thenComparing(Result::program)).toList();
        List<Result> scored = sorted.stream().filter(r -> "open".equals(roleBySource.get(r.source()))).toList();
        StringBuilder out = new StringBuilder("# MetaEditor comparison\n\n## Headline (open sources)\n\n");
        appendCounts(out, counts(scored));
        out.append("\n## Per source\n\n| Source | Role |");
        for (Outcome o : Outcome.values()) {
            out.append(' ').append(label(o)).append(" |");
        }
        out.append("\n|---|---|").append("---|".repeat(Outcome.values().length)).append('\n');
        Map<String, List<Result>> bySource = sorted.stream()
                .collect(Collectors.groupingBy(Result::source, TreeMap::new, Collectors.toList()));
        bySource.forEach((source, rs) -> {
            out.append("| ").append(source).append(" | ").append(roleBySource.getOrDefault(source, "?")).append(" |");
            counts(rs).values().forEach(n -> out.append(' ').append(n).append(" |"));
            out.append('\n');
        });
        out.append("\n## Disagreement kinds (open sources)\n\n");
        Map<String, List<Result>> byKind = new TreeMap<>();
        for (Result r : scored) {
            r.kinds().stream().map(Example::kind).distinct().forEach(k -> byKind.computeIfAbsent(k, x -> new ArrayList<>()).add(r));
        }
        if (byKind.isEmpty()) {
            out.append("None.\n");
        }
        byKind.entrySet().stream()
                .sorted(Comparator.<Map.Entry<String, List<Result>>>comparingInt(e -> -e.getValue().size()).thenComparing(Map.Entry::getKey))
                .forEach(e -> {
                    out.append("- **").append(e.getKey()).append("**: ").append(e.getValue().size()).append(" programs\n");
                    e.getValue().stream().map(r -> exampleOf(r, e.getKey()).map(x -> r.source() + "/" + x.file() + ":" + x.line()))
                            .flatMap(Optional::stream).distinct().limit(5)
                            .forEach(where -> out.append("  - ").append(where).append('\n'));
                });
        out.append("\n## Excluded (all sources)\n\n");
        Map<String, Long> reasons = sorted.stream().filter(r -> r.outcome() == Outcome.EXCLUDED)
                .collect(Collectors.groupingBy(Result::excludedReason, TreeMap::new, Collectors.counting()));
        if (reasons.isEmpty()) {
            out.append("None.\n");
        }
        reasons.forEach((reason, n) -> out.append("- ").append(reason).append(": ").append(n).append('\n'));
        return out.toString();
    }

    /** At least this many counted mutants per kind before a catch rate means anything (SC-007). */
    static final int MIN_COUNTED_PER_KIND = 50;

    /**
     * One mutant (FR-017): {@code counted} when MetaEditor rejects it; {@code caught} when the plugin
     * reports an error within {@link #LINE_TOLERANCE} lines of the injected one that it didn't report
     * on the original program; {@code caughtAsWarning} when only a warning lands there (FR-021).
     */
    record MutantResult(String source, String program, String kind, int line, boolean counted, boolean caught,
                        boolean caughtAsWarning) {
    }

    static MutantResult classifyMutant(String source, String program, String kind, int line, boolean rejected,
                                       java.util.Collection<Integer> errorLines, java.util.Collection<Integer> warningLines,
                                       java.util.Collection<Integer> originalErrorLines) {
        boolean caught = rejected && errorLines.stream()
                .anyMatch(l -> Math.abs(l - line) <= LINE_TOLERANCE && !originalErrorLines.contains(l));
        boolean warned = rejected && !caught && warningLines.stream().anyMatch(l -> Math.abs(l - line) <= LINE_TOLERANCE);
        return new MutantResult(source, program, kind, line, rejected, caught, warned);
    }

    /** Counted mutants caught per kind, open sources only: the ratchet's numbers. */
    static Map<String, Long> caughtPerKind(List<MutantResult> mutants, Map<String, String> roleBySource) {
        return mutants.stream().filter(m -> "open".equals(roleBySource.get(m.source())) && m.caught())
                .collect(Collectors.groupingBy(MutantResult::kind, TreeMap::new, Collectors.counting()));
    }

    static String mutationReport(List<MutantResult> mutants, Map<String, String> roleBySource) {
        StringBuilder out = new StringBuilder("\n## Mutation set (open sources)\n\n");
        List<MutantResult> open = mutants.stream().filter(m -> "open".equals(roleBySource.get(m.source()))).toList();
        if (open.isEmpty()) {
            return out.append("No mutants.\n").toString();
        }
        out.append("| Kind | Generated | Counted (MetaEditor rejects) | Caught | Caught as warning | Catch rate |\n|---|---|---|---|---|---|\n");
        Map<String, List<MutantResult>> byKind = open.stream()
                .collect(Collectors.groupingBy(MutantResult::kind, TreeMap::new, Collectors.toList()));
        byKind.forEach((kind, ms) -> {
            long counted = ms.stream().filter(MutantResult::counted).count();
            long caught = ms.stream().filter(MutantResult::caught).count();
            long warned = ms.stream().filter(MutantResult::caughtAsWarning).count();
            out.append("| ").append(kind).append(" | ").append(ms.size()).append(" | ").append(counted)
                    .append(counted < MIN_COUNTED_PER_KIND ? " (below " + MIN_COUNTED_PER_KIND + ", SC-007)" : "")
                    .append(" | ").append(caught).append(" | ").append(warned).append(" | ")
                    .append(counted == 0 ? "-" : Math.round(100.0 * caught / counted) + "%").append(" |\n");
        });
        out.append("\nMissed mutants (first 5 per kind):\n\n");
        byKind.forEach((kind, ms) -> ms.stream().filter(m -> m.counted() && !m.caught()).limit(5)
                .forEach(m -> out.append("- ").append(kind).append(": ").append(m.source()).append('/')
                        .append(m.program()).append(':').append(m.line()).append('\n')));
        return out.toString();
    }

    private static Optional<Example> exampleOf(Result r, String kind) {
        return r.kinds().stream().filter(x -> x.kind().equals(kind)).findFirst();
    }

    private static void appendCounts(StringBuilder out, Map<Outcome, Long> counts) {
        long judged = counts.entrySet().stream().filter(e -> e.getKey() != Outcome.EXCLUDED).mapToLong(Map.Entry::getValue).sum();
        out.append("- judged programs: ").append(judged).append('\n');
        counts.forEach((o, n) -> out.append("- ").append(label(o)).append(": ").append(n).append('\n'));
    }

    static String label(Outcome o) {
        return o.name().toLowerCase(java.util.Locale.ROOT).replace('_', '-');
    }
}
