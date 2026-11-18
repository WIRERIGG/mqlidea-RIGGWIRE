# Tasks: MetaEditor Comparison Harness

**Input**: spec.md, premortem.md, plan.md, lattice.md, research.md, data-model.md, contracts/
**Rules**: riskiest unknown first; every premortem/lattice tripwire is a check below (marked ⛔); `/speckit-implement` + `/speckit-converge` stop after 3 rounds and report what is left.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- ⛔ = tripwire: if it fails, stop and report instead of continuing

## Phase 1: Spike (the riskiest unknown, blocks everything)

- [ ] T001 ⛔ Spike, **only while no backtest runs** (tester-only busy rule, research R4): stage `geraked__metatrader5` into `/tmp/mqlidea-harness/geraked__metatrader5/MQL5/` (Include = symlinks to MetaTrader's Standard Library entries + the repo's headers; programs under `Experts/`), compile one program with `MetaEditor64.exe /compile:"Z:\tmp\...\X.mq5" /include:"Z:\tmp\mqlidea-harness\geraked__metatrader5\MQL5" /log` under MetaTrader's Wine, and record: did `/include:` take effect, did Wine follow the symlinks, seconds per compile, where the log was written, and a before/after listing of MetaTrader's MQL5 folder (must be identical). If symlinks fail, repeat with the Standard Library copied into the stand-in. Write findings into research.md R1/R8.
- [ ] T002 ⛔ Check after T001: MetaTrader's MQL5 folder unchanged. If anything there changed, stop the feature and report.

## Phase 2: Foundational (blocks all stories)

- [ ] T003 Create `tools/harness/corpus.json` per contracts/manifest.schema.json with the MVP sources only: `geraked__metatrader5` (open), `sibvic__mq5-templates` (open), MetaQuotes Examples (open), the owner's EA (report); include_roots from each repo's `#include <...>` lines (research R2)
- [ ] T004 [P] Busy check in `tools/harness/metaeditor_verdicts.py` (`is_busy()`, research R4) with a self-test against recorded `ps` lines: idle, plain terminal (not busy), tester agent, `terminal64 /config:` run, `mt5 backtest` driver, unreadable table (busy)
- [ ] T005 [P] MetaTrader-untouched check in the same script: snapshot (relative path, size, mtime) of MetaTrader's MQL5 folder at start; compare at end; non-zero exit and a loud message on any difference
- [ ] T006 [P] Log parser in the same script: UTF-16LE (BOM-aware) MetaEditor log → diagnostics per contracts/verdict.schema.json, staged paths mapped back to repo-relative paths; self-test on a recorded log from T001
- [ ] T007 Verdict key and store (research R3): sha256 over program bytes + sorted header-root bytes + MetaEditor build; store at `~/.cache/mqlidea-harness/verdicts/<key>.json`

## Phase 3: User Story 3 - Never disturb MetaTrader (P1)

- [ ] T008 [US3] Referee loop in `metaeditor_verdicts.py`: for each program without a fresh verdict: `is_busy()` → stop cleanly (keep verdicts so far) if busy; stage; compile with timeout; parse; store; classify exclusions (`missing-include`, `no-log`, `crash`, `timeout`)
- [ ] T009 [US3] ⛔ Test: start the referee with a fake `metatester64.exe` process line present (stub the table): it refuses and names it; inject the stub mid-run: it stops before the next compile
- [ ] T010 [US3] Run the referee on the MVP sources (MetaTrader idle only). ⛔ Any source with >30% programs excluded: fix its include_roots before continuing

## Phase 4: User Story 1 + 2 - Score and ranked gap list (P1) 🎯 MVP

- [ ] T011 [P] [US1] `src/test/java/gate/HarnessCompare.java`: pure classification per data-model.md (`agree-clean`, `agree-errors`, `disjoint-errors`, `false-error`, `missed-error`, `excluded`; ±1-line match; first error per file for kinds) and report text, fully sorted, no timestamps
- [ ] T012 [P] [US1] `src/test/java/gate/HarnessCompareTest.java`: every outcome incl. `disjoint-errors`, cascades don't change outcome, warnings never decide, report byte-identical across two calls
- [ ] T013 [US1] `src/test/java/gate/HarnessTest.java`: no-op without `MQL_HARNESS`; per source, load files as project files, set `MqlIncludeRoots.setTestRoots` to the source's roots + the Standard Library, enable default-on ERROR inspections, `doHighlighting(HighlightSeverity.ERROR)` per judged file (research R5), compare against the store, write `build/harness-report.md`
- [ ] T014 [US1] ⛔ Time check on the MVP: average highlight time × full corpus size; over 10 minutes → restrict to programs + headers MetaEditor named (lattice.md) before going on
- [ ] T015 [US2] Report sections: headline, per source, ranked kinds with ≤5 `file:line` examples, MQL4 "no referee", MetaTrader-untouched result (data-model.md Report)
- [ ] T016 [US1] Baseline ratchet: `src/test/resources/gate/harness-baseline.properties` (counts only); fail when `open.falseError` or `open.missedError` rises; `MQL_HARNESS_UPDATE=1` rewrites
- [ ] T017 [US1] `tools/harness/harness.sh` (like `tools/corpus-gate.sh`: fresh test index before and after)
- [ ] T018 [US1] ⛔ Determinism: run `harness.sh` twice; reports must be byte-identical (SC-003)
- [ ] T019 [US1] ⛔ Live cross-check (FR-015, research R7): on the EA and `geraked__metatrader5`, per-file error counts from the report equal `tools/clion-mcp-check.py` in CLion with the installed plugin; any mismatch → fix the harness setup, don't trust the score

**Checkpoint**: MVP delivers a score and a ranked gap list for 3 sources + the EA (report-only).

## Phase 5: User Story 4 - Fast reruns (P2)

- [ ] T020 [US4] Rerun with no corpus change: zero MetaEditor starts (count them) and identical report; edit one staged-program's source copy in a temp clone: exactly one recompile
- [ ] T021 [US4] ⛔ Plugin-side full rescore under 10 minutes (SC-002)

## Phase 6: User Story 5 - The corpus covers the language (P2)

- [ ] T022 [US5] Onboard the remaining open sources one at a time (`dingmaotu__mql-zmq`, `EarnForex__PositionSizer`, `EA31337__EA31337-classes`, `MegaJoctan__ML5`, `darwinex__dwxconnect`, `xxvw__ICT_Library_MQ5`, `EarnForex__MarketProfile`, `erlonfs__bad-robot.framework`, `vivazzi__JAson`, MetaQuotes Free code); ⛔ each must pass the 30%-excluded tripwire before its numbers count; `dingmaotu__mql4-lib` is MQL4: plugin-side only
- [ ] T023 [US5] Held-out sources (`EarnForex__Account-Protector`, `Roffild__RoffildLibrary`, `landim32__LadinoBot`): role `heldout`, scored only with `MQL_HARNESS_HELDOUT=1` (FR-016)
- [ ] T024 [US5] ⛔ SC-001: at least 85% of the corpus's MQL5 programs have a usable verdict; otherwise list the sources holding it back

## Phase 7: Polish

- [ ] T025 [P] CLAUDE.md: harness commands and what its numbers mean; README "How quality is held": add the false-error / missed-error score once the baseline exists
- [ ] T026 Record the first report's top 5 disagreement kinds in the spec folder as `findings.md` (paths/lines/MetaEditor codes only, no corpus code): these become features 002+ (SC-006)
- [ ] T027 `./gradlew build` green (643+ tests; HarnessTest is a no-op there)

## Dependencies

T001 → T002 → everything. T003–T007 before T008. T008–T010 before T013. T011–T012 can start right after T002 (pure code). Phase 5 and 6 need the MVP checkpoint. T026 needs T024.
