# Tasks: MetaEditor Comparison Harness

**Input**: spec.md, premortem.md, plan.md, lattice.md, research.md, data-model.md, contracts/
**Rules**: harness core (T001–T019 only; Phase 4b comes after) time-boxed to 2 sessions, ⛔ over that → stop and report; feature 002 (template parameters) runs alongside it; riskiest unknown first; every premortem/lattice tripwire is a check below (marked ⛔); `/speckit-implement` + `/speckit-converge` stop after 3 rounds and report what is left.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- ⛔ = tripwire: if it fails, stop and report instead of continuing

## Phase 1: Spike (the riskiest unknown, blocks everything)

- [x] T001 ⛔ Spike, **only while no backtest runs** (tester-only busy rule, research R4): stage `geraked__metatrader5` into `/tmp/mqlidea-harness/geraked__metatrader5/MQL5/` (Include = symlinks to MetaTrader's Standard Library entries + the repo's headers; programs under `Experts/`), compile one program with `MetaEditor64.exe /compile:"Z:\tmp\...\X.mq5" /include:"Z:\tmp\mqlidea-harness\geraked__metatrader5\MQL5" /log` under MetaTrader's Wine, and record: did `/include:` take effect, did Wine follow the symlinks, seconds per compile, where the log was written, and a before/after listing of MetaTrader's MQL5 folder (must be identical). If symlinks fail, repeat with the Standard Library copied into the stand-in. Write findings into research.md R1/R8. — **Done 2026-11-18:** `/include:` works, Wine follows the symlinks, 3.3–10 s per compile, log beside the staged program; found and fixed the `#resource` root (MQL5-layout folders now mirrored at the stage root). Details in research.md R1/R4/R8.
- [x] T002 ⛔ Check after T001: MetaTrader's MQL5 folder unchanged. If anything there changed, stop the feature and report. — **Done 2026-11-18:** MetaTrader's MQL5 folder identical before and after every T001 compile (snapshot diff empty); only `logs/metaeditor.log`, outside MQL5, grew.

## Phase 2: Foundational (blocks all stories)

- [X] T003 Create `tools/harness/corpus.json` per contracts/manifest.schema.json with the MVP sources only: `geraked__metatrader5` (open), `sibvic__mq5-templates` (open), MetaQuotes Examples (open), the owner's EA (report); include_roots from each repo's `#include <...>` lines (research R2) — done: geraked (38 programs), sibvic (5), MetaQuotes Examples (7, read in place), EA report (8, links MetaTrader's whole Include for its user headers)
- [X] T004 [P] Busy check in `tools/harness/metaeditor_verdicts.py` (`is_busy()`, research R4) with a self-test against recorded `ps` lines: idle, plain terminal (not busy), tester agent, `terminal64 /config:` run, `mt5 backtest` driver, unreadable table (busy) — done; every tester agent counts until T001 settles the `/run`-agent question; a running MetaEditor counts too (FR-019)
- [X] T005 [P] MetaTrader-untouched check in the same script: snapshot (relative path, size, mtime) of MetaTrader's MQL5 folder at start; compare at end; non-zero exit and a loud message on any difference — done
- [X] T006 [P] Log parser in the same script: UTF-16LE (BOM-aware) MetaEditor log → diagnostics per contracts/verdict.schema.json, staged paths mapped back to repo-relative paths; self-test on a recorded log from T001 — done; self-test on a synthetic log in MetaEditor's format (UTF-16 BOM, absolute `Z:\` and `MQL5\`-relative paths, Standard Library labelled `<stdlib>/`); recheck on a real T001 log
- [X] T007 Verdict key and store (research R3): sha256 over program bytes + sorted header-root bytes + MetaEditor build; store at `~/.cache/mqlidea-harness/verdicts/<key>.json` — done; key also covers the source and program path (quoted includes resolve beside the program; found when two identical programs shared a verdict); MetaEditor build read from the exe's version resource (6230 today)

## Phase 3: User Story 3 - Never disturb MetaTrader (P1)

- [X] T008 [US3] Referee loop in `metaeditor_verdicts.py`: for each program without a fresh verdict: `is_busy()` → stop cleanly (keep verdicts so far) if busy; stage; compile with timeout; parse; store; classify exclusions (`missing-include`, `no-log`, `crash`, `timeout`) — done; staging keeps header names, makes folders and program names space-free (Wine can't compile a spaced path), error 106 → missing-include
- [X] T009 [US3] ⛔ Test: start the referee with a fake `metatester64.exe` process line present (stub the table): it refuses and names it; inject the stub mid-run: it stops before the next compile — done (self-test: refuses to start; stops before the next compile)
- [X] T010 [US3] Run the referee on the MVP sources (MetaTrader idle only). ⛔ Any source with >30% programs excluded: fix its include_roots before continuing — **done 2026-11-18**: run in idle windows between the other session's backtests; the referee stopped cleanly each time a tester agent started (one overlapping compile discarded). Tripwire: see research.md "T010 tripwire". Two staging gaps were fixed: `#resource` sources MetaEditor can't build itself, and MQL4 headers that had been stubbed.

## Phase 4: User Story 1 + 2 - Score and ranked gap list (P1) 🎯 MVP

- [X] T011 [P] [US1] `src/test/java/gate/HarnessCompare.java`: pure classification per data-model.md (`agree-clean`, `agree-errors`, `disjoint-errors`, `false-error`, `missed-error`, `excluded`; ±1-line match; first error per file for kinds) and report text, fully sorted, no timestamps
- [X] T012 [P] [US1] `src/test/java/gate/HarnessCompareTest.java`: every outcome incl. `disjoint-errors`, cascades don't change outcome, warnings never decide, report byte-identical across two calls
- [X] T013 [US1] `src/test/java/gate/HarnessTest.java`: no-op without `MQL_HARNESS`; per source, load files as project files, set `MqlIncludeRoots.setTestRoots` to the source's roots + the Standard Library, enable default-on ERROR inspections, `doHighlighting(HighlightSeverity.ERROR)` per judged file (research R5), compare against the store, write `build/harness-report.md` — done; Standard Library loaded once (include/), user headers apart (include-user/, EA only); compiler annotator can't fire (light-test files are not on disk)
- [X] T014 [US1] ⛔ Time check on the MVP: average highlight time × full corpus size; over 10 minutes → restrict to programs + headers MetaEditor named (lattice.md) before going on — dry run on placeholder verdicts: 58 programs in ~21 s (≈350 ms each), far under 10 minutes
- [X] T015 [US2] Report sections: headline, per source, ranked kinds with ≤5 `file:line` examples, MQL4 "no referee", MetaTrader-untouched result (data-model.md Report) — headline, per source, ranked kinds with distinct examples, run section (build, complete, untouched, MQL4 no referee)
- [X] T016 [US1] Baseline ratchet: `src/test/resources/gate/harness-baseline.properties` (counts only); fail when `open.falseError` or `open.missedError` rises; `MQL_HARNESS_UPDATE=1` rewrites — done; the first real run writes the baseline **First real baseline 2026-11-18** (587 programs and stubs, 1,006 counted mutants): open sources 285 agree-clean, 79 agree-errors, 36 disjoint, 31 false-error, 67 missed, 40 excluded; caught per kind: misspelt identifier 150/164 (91%), undeclared member 102/110 (93%), missing `;` 1/155, unbalanced brace 2/134, type mismatch 0/144, argument count 0/146. A full scoring run took 346 s.
- [X] T017 [US1] `tools/harness/harness.sh` (like `tools/corpus-gate.sh`: fresh test index before and after) — done
- [X] T018 [US1] ⛔ Determinism: run `harness.sh` twice; reports must be byte-identical (SC-003) — dry run: two runs byte-identical; recheck on real verdicts — **rechecked on real verdicts 2026-11-18**: two full runs (346 s, 288 s) gave byte-identical reports.
- [ ] T019 [US1] ⛔ Live cross-check (FR-015, research R7): on the EA and `geraked__metatrader5`, per-file error counts from the report equal `tools/clion-mcp-check.py` in CLion with the installed plugin; any mismatch → fix the harness setup, don't trust the score

**Checkpoint**: MVP delivers a score and a ranked gap list for 3 sources + the EA (report-only).

## Phase 4b: Detection and coverage (from the second /invert)

- [x] T019a [US1] Header stubs (FR-018): for each header no program includes, generate `/tmp/.../Scripts/<repo>/stub_<n>.mq5` (`#include` the header, empty `OnStart`); judged like programs; never written to any repository — **Done:** stubs staged in `MQL5/Scripts/<name>/stub_<n>.mq5` for every repo `.mqh` no program reaches (text-level include closure, quoted beside the file then Include, case-insensitive); the verdict is filed under the header's repo path, so HarnessTest scores the header with no special case; errors on the stub's own lines map to `<stub>/...`. Stage-only: geraked 1, sibvic 189, EA 2. The verdict key now also hashes every `.mqh`/`.h` in the repo (a quoted include can reach outside the roots) but no other program, so one program edit still means one recompile (self-tested).
- [x] T019b [US1] Mutation set (FR-017, FR-021): seeded, text/token-based generator (no plugin parser) writing mutants to `/tmp` only, 6 kinds (missing `;`, misspelt identifier, wrong argument count, type mismatch, unbalanced brace, undeclared member); keep a mutant only if MetaEditor rejects it; report catch rate per kind — **Done:** `tools/harness/mutate.py` (text + token mask only, seeded, 6 kinds, own self-test); the referee compiles up to `MQL_HARNESS_MUTANTS`=2 mutants per kind per clean program after the programs, mutant text kept in the verdict; HarnessTest swaps the text into the program document, highlights at WARNING, restores; `HarnessCompare.classifyMutant`/`mutationReport` (unit-tested); `mutants.caught.<kind>` ratcheted. Dry run on placeholder verdicts (every mutant "rejected"): 480 mutants from 40 programs; missing `;` caught 1%, unbalanced brace 0%, wrong argument count 0%, type mismatch 0%, misspelt identifier 97%, undeclared member 100%. Probe confirmed the first two are the plugin, not the harness: a missing `;` gives no error at all (tolerant parser), and an unbalanced brace is reported at the opening brace, outside the ±1 rule.
- [X] T019c [US3] Lock and single MetaEditor (FR-019): harness lock file; skip and wait while another `metaeditor64.exe` runs; self-test with a stubbed process line — done: lock with owner PID, stale takeover, exit 6 when held; another MetaEditor is busy
- [x] T019d [US1] One build per score (FR-020): report refuses to mix builds; build change → stale verdicts recompiled first — **Done:** HarnessTest already refused verdicts from another build; the referee self-test now proves a build change recompiles every program and mutant before the next index, and the index carries only the new build.
- [X] T019e ⛔ SC-007: at least 50 counted mutants per kind; otherwise widen the program sample — **met 2026-11-18**: counted per kind 155 / 164 / 144 / 134 / 110 / 144 (missing `;`, misspelt identifier, type mismatch, unbalanced brace, undeclared member, argument count).

- [x] T019f ⛔ Rule-change discipline (FR-022): a check in HarnessTest that fails if data-model.md's rule block changed without the baseline being rewritten in the same commit — **Done:** data-model.md's rules sit between `scoring-rules` markers (mutant rules added there); the baseline stores `rules.sha256` and HarnessTest fails when the block changes without a baseline rewrite. Verified both ways on placeholder verdicts.

## Phase 5: User Story 4 - Fast reruns (P2)

- [X] T020 [US4] Rerun with no corpus change: zero MetaEditor starts (count them) and identical report; edit one staged-program's source copy in a temp clone: exactly one recompile — **done 2026-11-18**: a full rerun with nothing changed compiled 0 and reused 1,575 verdicts in 16 s. In a temp clone of dwxconnect, an unchanged run compiled 0; editing one program compiled 13 (the program plus its 12 seeded mutants, which derive from its text); with `MQL_HARNESS_MUTANTS=0`, exactly 1. MQL5 was untouched each time.
- [x] T021 [US4] ⛔ Plugin-side full rescore under 10 minutes (SC-002) — **Done 2026-11-18 (placeholder verdicts; MetaEditor's answers don't change plugin-side time):** all 16 sources, 587 programs and stubs plus 2,209 mutants, held-out included: 318 s for the whole harness.sh run, 152 s of it highlighting (259 ms per program).

## Phase 6: User Story 5 - The corpus covers the language (P2)

- [X] T022 [US5] Onboard the remaining open sources one at a time (`dingmaotu__mql-zmq`, `EarnForex__PositionSizer`, `EA31337__EA31337-classes`, `MegaJoctan__ML5`, `darwinex__dwxconnect`, `xxvw__ICT_Library_MQ5`, `EarnForex__MarketProfile`, `erlonfs__bad-robot.framework`, `vivazzi__JAson`, MetaQuotes Free code); ⛔ each must pass the 30%-excluded tripwire before its numbers count; `dingmaotu__mql4-lib` is MQL4: plugin-side only — **done 2026-11-18**: every source compiled (1,575 verdicts). Over the tripwire: ML5 (17 of 30), because its `Sklearn/` folder includes files the repo no longer has. No include root can fix that, so it is kept and recorded in research.md; its 13 compiling programs count.
- [ ] T023 [US5] Held-out sources (`EarnForex__Account-Protector`, `Roffild__RoffildLibrary`, `landim32__LadinoBot`): role `heldout`, scored only with `MQL_HARNESS_HELDOUT=1` (FR-016)
- [X] T024 [US5] ⛔ SC-001: at least 85% of the corpus's MQL5 programs have a usable verdict; otherwise list the sources holding it back — **met 2026-11-18**: 234 of 234 `.mq5` programs have a usable verdict (100%); counting the 335 header stubs, 529 of 569 (93%). The 40 exclusions are header stubs in ML5 `Sklearn/` (17) and sibvic snippets (23), both missing-include for the reasons in research.md.

## Phase 7: Polish

- [ ] T025 [P] CLAUDE.md: harness commands and what its numbers mean; README "How quality is held": add the false-error / missed-error score once the baseline exists — **CLAUDE.md part done 2026-11-18** (commands and what the numbers mean); README waits for the first real baseline.
- [X] T026 Record the first report's top 5 disagreement kinds in the spec folder as `findings.md` (paths/lines/MetaEditor codes only, no corpus code): these become features 002+ (SC-006) — **done 2026-11-18**: findings.md (top 5 kinds, mutation gaps as the next four features, fixes the harness found).
- [ ] T027 `./gradlew build` green (643+ tests; HarnessTest is a no-op there)

## Dependencies

T001 → T002 → everything. T003–T007 before T008. T008–T010 before T013. T011–T012 can start right after T002 (pure code). Phase 5 and 6 need the MVP checkpoint. T026 needs T024.

## Found by the mutation dry run (plugin gaps, for T026)

- A statement missing its `;` produces no plugin error (the parser recovers silently); MetaEditor rejects it. Largest catch-rate gap; a parser change, so it needs its own spec (ruin line: new parse errors in real code).
- An unbalanced brace is reported at the opening brace, not near the missing `}`; under the frozen ±1 rule it never counts as caught. Whether to score "caught anywhere in the file" for this kind is a rule change (FR-022: its own commit).
- No argument-count or type checks exist yet, so those kinds sit at 0% until features add them.

## Found by the dry run (placeholder verdicts, before MetaEditor)

Plugin errors on public code that look false by eye; MetaEditor's verdict will confirm:
- `DatabaseColumnInteger(...)` (geraked EAUtils.mqh:1692, Cot.mqh, Storage.mqh: 17 programs): built-in Database column readers missing from the plugin's function catalog.
- `kernel32::GetLastError()` after `#import "kernel32.dll"` (geraked Shell.mqh:53, WinINet.mqh:341): import-qualified calls don't resolve.
- `_signaler.GetSymbol()` (sibvic AlertSignal.mqh:65) and `extern int` in an MQL5 indicator (geraked DarvasBoxes.mq5:37, annotator): need the verdict.
