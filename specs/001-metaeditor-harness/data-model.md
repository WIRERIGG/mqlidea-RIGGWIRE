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
| `source`, `program` | corpus source name and repo-relative program path |
| `metaeditor_build` | from MetaEditor's log header |
| `status` | `ok` or `excluded` |
| `excluded_reason` | `missing-include`, `no-log`, `crash`, `timeout` |
| `diagnostics[]` | `{file, line, col, severity: error|warning, code, message}`, `file` repo-relative |
| `compiled_at` | timestamp (not part of the report, so reruns stay identical) |

## PluginVerdict (in memory, HarnessTest)

`{file, line, kind: parse|annotator|inspection, id, message}` for every ERROR-severity highlight.

## ComparisonResult (per program, with its headers)

| Field | Meaning |
|---|---|
| `outcome` | `agree-clean`, `agree-errors`, `disjoint-errors`, `false-error`, `missed-error`, `excluded` |
| `kinds[]` | disagreement kinds from the **first** error per file on each side: `plugin:<kind>:<id>` for false errors, `metaeditor:<code>` for missed errors |

State rules: `false-error` if the plugin reports any error in the program or its corpus headers and MetaEditor reports none; `missed-error` if the reverse; `agree-errors` if both report errors and at least one plugin error line matches a MetaEditor error line (same file, ±1 line); `disjoint-errors` if both report errors with no such match (a hidden false error, never counted as agreement). Warnings never decide the outcome; error counts never matter (MetaEditor cascades).

## Report (build/harness-report.md)

1. Headline: judged programs, agree-clean, agree-errors, false-error, missed-error, excluded (by reason), line mismatches.
2. Per source (open, heldout if requested, report).
3. Disagreement kinds ranked by programs affected, up to 5 `file:line` examples each.
4. MQL4 "no referee" section: plugin error counts only.
5. MetaTrader-untouched check result from the last referee run.

Ordering is fully sorted (source, path, line), so unchanged inputs give a byte-identical report (FR-013).

## Baseline (src/test/resources/gate/harness-baseline.properties)

`open.falseError`, `open.missedError`, `open.excluded`: counts only. The test fails when `falseError` or `missedError` rises; `MQL_HARNESS_UPDATE=1` rewrites it after a deliberate change.
