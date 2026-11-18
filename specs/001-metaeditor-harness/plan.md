# Implementation Plan: MetaEditor Comparison Harness

**Branch**: `001-metaeditor-harness` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-metaeditor-harness/spec.md` (with the pre-mortem's changes)

## Summary

Two halves joined by a verdict store outside the repository:

1. **Referee side** (`tools/harness/metaeditor_verdicts.py`, Python 3, no plugin code): for each MQL5 program in the corpus manifest, stage the program's repository in a throwaway MQL5 stand-in folder under `/tmp`, compile it with MetaTrader 5's MetaEditor under Wine using `/include:` pointed at that stand-in, parse the UTF-16 log, and store the verdict keyed by content. Refuses to run beside a backtest, rechecks before every compile, and proves MetaTrader's MQL5 folder is untouched.
2. **Plugin side** (`src/test/java/gate/HarnessTest.java`, JUnit on the IntelliJ test framework like `CorpusGateTest`): load each corpus repository as project files with its own include root, run the plugin's real highlighting (parse errors, annotators, error-level inspections that are on by default) on every judged file, compare with the stored verdicts, write `build/harness-report.md`, and ratchet the headline counts against `src/test/resources/gate/harness-baseline.properties`.

**Delivery order (from lattice.md):** spike `/include:` + symlinks → full pipeline on an MVP of 3 sources (`geraked__metatrader5`, `sibvic__mq5-templates`, MetaQuotes Examples) → onboard the remaining sources one at a time, each passing the 30%-excluded tripwire. Plugin-side tripwire: if the MVP's average highlight time × corpus size exceeds 10 minutes, highlight only programs and the headers MetaEditor named.

## Technical Context

**Language/Version**: Java 21 (plugin side, test source set only); Python 3 (referee side, matching `tools/*.py`)
**Primary Dependencies**: IntelliJ test framework already used by `CorpusGateTest` (`BasePlatformTestCase`, `CodeInsightTestFixture.doHighlighting`); MetaEditor64 under MetaTrader 5's bundled Wine
**Storage**: verdict store `~/.cache/mqlidea-harness/verdicts/<sha256>.json` (outside every repository); report `build/harness-report.md`; baseline `src/test/resources/gate/harness-baseline.properties` (counts only)
**Testing**: JUnit 5 for the Python-free parts (log parsing, classification, report determinism); a Python self-test for the referee's busy check and folder-snapshot check; one live spike
**Target Platform**: macOS with MetaTrader 5 under Wine (the referee); any OS for the plugin side once verdicts exist
**Project Type**: test and tooling addition to the existing plugin; no shipped plugin code changes
**Performance Goals**: plugin-side rescore of the full corpus under 10 minutes (SC-002); referee resumable in batches
**Constraints**: never write under MetaTrader's install (FR-009); never compile beside a backtest (FR-008); never copy corpus code into the repo (FR-010)
**Scale/Scope**: 219 corpus `.mq5` programs + MetaQuotes' Examples/Free programs (~190) and the ~1,150 headers they reach; 153 `.mq4` files plugin-side only

## Constitution Check

| Principle | Check | Status |
|---|---|---|
| I. Honest, early diagnostics | The harness is how honesty is proven: false errors become a gated number | PASS |
| II. Sturdy platform API | No shipped code changes. Test code uses only `BasePlatformTestCase`/`CodeInsightTestFixture`, already used by the corpus gate; no internal API | PASS |
| III. No MetaQuotes text or code | MetaQuotes and public code are read in place; staging copies live under `/tmp` only; the report quotes paths, lines, MetaEditor codes and messages (compiler output, not documentation) | PASS (note: MetaEditor's own error messages are quoted as data, as the plugin already does for compile diagnostics) |
| IV. Read-only toward MetaTrader | Programs are staged and compiled under `/tmp`; MetaQuotes' programs too (compiling in place would write `.ex5`/`.log` into the MetaTrader tree). `/include:` points at a `/tmp` stand-in whose Include holds symlinks to the Standard Library; MQL5 folder snapshot before/after; busy check before every compile | PASS |
| V. Every gate stays green | `HarnessTest` is a no-op without `MQL_HARNESS` (like `CorpusGateTest` without `MQL_CORPORA`), so `./gradlew build` is unaffected; its ratchet joins the gates once a baseline exists | PASS |

Re-checked after Phase 1 design: unchanged, PASS.

## Project Structure

### Documentation (this feature)

```text
specs/001-metaeditor-harness/
├── spec.md, premortem.md, plan.md, lattice.md
├── research.md          # decisions and the riskiest unknowns
├── data-model.md        # manifest, verdict, comparison, report
├── quickstart.md        # how to run it, and the live cross-check
├── contracts/
│   ├── verdict.schema.json
│   └── manifest.schema.json
└── tasks.md
```

### Source Code (repository root)

```text
tools/harness/
├── corpus.json              # manifest: sources, pinned commits, role (open | heldout | report)
├── metaeditor_verdicts.py   # referee: busy check, staging, /include:, compile, parse, store
└── harness.sh               # runs the plugin side (gradle) like tools/corpus-gate.sh

src/test/java/gate/
├── HarnessTest.java         # loads repos, highlights, compares, reports, ratchets
├── HarnessCompare.java      # pure classification + report text (unit-tested)
└── HarnessCompareTest.java

src/test/resources/gate/
└── harness-baseline.properties
```

**Structure Decision**: everything lives in `tools/` and the test source set, next to the corpus gate it extends. Nothing enters `src/main`, so the shipped plugin is untouched.

## Complexity Tracking

| Choice | Why needed | Simpler alternative rejected because |
|---|---|---|
| Python referee separate from the Java test | MetaEditor runs only under Wine on this Mac and takes hours; the plugin side must rerun in minutes on stored verdicts | One Java test that also compiles would block `./gradlew` for hours and need Wine wherever it runs |
| Staging every program under `/tmp` | MetaEditor writes `.ex5` and `.log` next to the source, which would write into the MetaTrader tree (MetaQuotes' programs) or dirty the corpus clones | Compiling in place breaks Principle IV |
| `doHighlighting` instead of walking PSI | Only real highlighting runs annotators and inspections the way CLion does, which FR-015's cross-check needs | Re-implementing the IDE's pass in the test would measure a setup no user has |
