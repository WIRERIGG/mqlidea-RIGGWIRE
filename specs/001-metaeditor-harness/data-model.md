# Data Model: MetaEditor Comparison Harness

## CorpusSource (tools/harness/corpus.json)

| Field | Meaning |
|---|---|
| `name` | e.g. `geraked__metatrader5`, `metaquotes-examples` |
| `path` | absolute or `~`-relative location, read in place |
| `commit` | pinned version (git short sha), or `metatrader-build-<n>` for MetaQuotes code |
| `licence` | SPDX id; sources without one are not admitted |
| `role` | `open` (scored), `heldout` (scored on request), `report` (measured, never in the headline, e.g. the owner's EA) |
| `include_roots` | folders standing in for `MQL5/Include` |
| `programs` | glob for programs, default `**/*.mq5` |

## MetaEditorVerdict (~/.cache/mqlidea-harness/verdicts/<key>.json)

| Field | Meaning |
|---|---|
| `key` | sha256 per research R3 |
| `source`, `program` | corpus source name and repo-relative program path; for a header stub (FR-018), the header's path |
| `metaeditor_build` | from MetaEditor's log header |
| `status` | `ok` or `excluded` |
| `excluded_reason` | `missing-include`, `no-log`, `crash`, `timeout`, `unsupported-path` |
| `diagnostics[]` | `{file, line, col, severity: error|warning, code, message}`, `file` repo-relative |
| `mutant` | mutants only (FR-017): `{kind, index, line, text}`, the injected error's 1-based line and the whole mutated program |

The index of one referee run (`current.json` beside the store) lists `programs[]` and `mutants[]` as `{source, program, key}` (mutants add `kind`, `index`), plus `metaeditor_build`, `complete` and `metatrader_untouched`.

## PluginVerdict (in memory, HarnessTest)

`{file, line, kind: parse|annotator|inspection, id, message}` for every ERROR-severity highlight.

## ComparisonResult (per program, with its headers)

| Field | Meaning |
|---|---|
| `outcome` | `agree-clean`, `agree-errors`, `disjoint-errors`, `false-error`, `missed-error`, `excluded` |
| `kinds[]` | disagreement kinds from the **first** error per file on each side: `plugin:<kind>:<id>` for false errors, `metaeditor:<code>` for missed errors |

<!-- scoring-rules:begin (FR-022: change only in its own commit, with before/after numbers; HarnessTest checks this block's hash against the baseline) -->

State rules: `false-error` if the plugin reports any error in the program or its corpus headers and MetaEditor reports none; `missed-error` if the reverse; `agree-errors` if both report errors and at least one plugin error line matches a MetaEditor error line (same file, ±1 line); `disjoint-errors` if both report errors with no such match (a hidden false error, never counted as agreement). Warnings never decide the outcome; error counts never matter (MetaEditor cascades).

Mutant rules (FR-017, FR-021): mutants are made only from programs MetaEditor compiles with no error, at most 2 per kind per program (seeded). A mutant is `counted` when MetaEditor reports an error for it; `caught` when the plugin reports an error on the program within ±1 line of the injected line that it did not report on the unmutated program; `caught as warning` when, not caught, a plugin warning lands within ±1 line. Catch rate = caught / counted, per kind, open sources; a kind with fewer than 50 counted mutants is marked below SC-007.

<!-- scoring-rules:end -->

## Report (build/harness-report.md)

1. Headline: judged programs, agree-clean, agree-errors, false-error, missed-error, excluded (by reason), line mismatches.
2. Per source (open, heldout if requested, report).
3. Disagreement kinds ranked by programs affected, up to 5 `file:line` examples each.
4. MQL4 "no referee" section: plugin error counts only.
5. MetaTrader-untouched check result from the last referee run.
6. Mutation set: per kind, generated, counted, caught, caught as warning and catch rate; first 5 missed mutants per kind.

Ordering is fully sorted (source, path, line), so unchanged inputs give a byte-identical report (FR-013).

## Baseline (src/test/resources/gate/harness-baseline.properties)

Counts only: `open.<outcome>` per outcome, `mutants.caught.<kind>` per kind, and `rules.sha256` (the hash of the scoring-rules block above). The test fails when `open.false-error`, `open.missed-error` or `open.disjoint-errors` rises, when a `mutants.caught.<kind>` falls, or when the rules block no longer matches `rules.sha256`; `MQL_HARNESS_UPDATE=1` rewrites it after a deliberate change.
