# Feature Specification: MetaEditor Comparison Harness

**Feature Branch**: `001-metaeditor-harness`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "A MetaEditor comparison harness: compile a fixed, broad MQL corpus (MetaQuotes' code plus public MQL5 projects, read in place) with MetaEditor and the plugin, and report per file where the plugin raises an error MetaEditor doesn't, misses one it does, or differs in severity; refuses to run beside a backtest; output is a ranked gap list and a single score. Make the plugin powerful for MQL syntax and logic, judged by the language, not by one repository."

## Why

The plugin is currently judged on two things: MetaQuotes' Standard Library and examples (corpus gate) and the owner's own EA. The EA uses almost none of the language's harder features (no templates at all), so judging by it hid real gaps, and nothing compares the plugin's verdict with MetaEditor's file by file. Without that comparison, "the plugin is accurate" is unproven and every syntax or logic improvement is a guess. This feature builds the referee every later improvement is scored by.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One score for language accuracy (Priority: P1)

The plugin maintainer runs the harness and gets one headline result over a broad, fixed body of real MQL code: how many files the plugin wrongly flags with an error (false errors), how many real compile errors it misses (missed errors), and how many files both agree on.

**Why this priority**: Without a single, repeatable number, no syntax or logic change can be shown to help or hurt. This is the minimum that makes every later feature measurable.

**Independent Test**: Run the harness on the full corpus; it prints the three counts and the corpus size, and a second run with nothing changed prints identical numbers.

**Acceptance Scenarios**:

1. **Given** the corpus and MetaEditor's recorded verdicts, **When** the maintainer runs the harness, **Then** it reports false errors, missed errors, agreements and the number of files judged.
2. **Given** no change to the plugin or the corpus, **When** the harness runs twice, **Then** both reports are identical.
3. **Given** a deliberately injected parse error in one corpus file's in-memory copy, **When** the harness runs, **Then** that file is counted as a false error and named.

---

### User Story 2 - A ranked list of what to fix (Priority: P1)

Alongside the score, the maintainer gets the disagreements grouped by kind (for example: "plugin reports a parse error MetaEditor accepts", "MetaEditor reports 'undeclared identifier' the plugin misses"), ranked by how many files each kind affects, with a few concrete file:line examples per kind.

**Why this priority**: The score says how good the plugin is; the ranked list says what to build next. It replaces guesses (templates, vector/matrix) with measured gaps.

**Independent Test**: The report lists each disagreement kind with a file count and up to 5 file:line examples; following any example to its file shows the disagreement.

**Acceptance Scenarios**:

1. **Given** a completed run, **When** the maintainer opens the report, **Then** disagreement kinds are listed from most to fewest affected files, each with examples.
2. **Given** MetaEditor's error code for a missed error, **When** the report lists it, **Then** the kind is named by MetaEditor's code and message, not paraphrased.

---

### User Story 3 - Never disturb MetaTrader (Priority: P1)

The harness never writes into MetaTrader's folders and never compiles while the Strategy Tester runs. If a backtest starts mid-run, the harness stops cleanly and can resume later.

**Why this priority**: Other sessions run backtests on this machine often; corrupting one, or polluting MetaTrader's Include folder with third-party headers, is the one outcome that cannot be undone. This is a hard rule of the project (constitution Principle IV).

**Independent Test**: Start the harness while a backtest runs: it refuses and says why. Start a backtest during a harness run: the harness stops before its next compile. After any run, MetaTrader's MQL5 folder listing is unchanged.

**Acceptance Scenarios**:

1. **Given** a Strategy Tester agent or an `mt5 backtest` driver is running, **When** the harness is asked to compile, **Then** it refuses and names what is running.
2. **Given** a harness run in progress, **When** a backtest starts, **Then** the harness stops before the next compile and keeps the verdicts gathered so far.
3. **Given** any run, **When** it ends, **Then** nothing under MetaTrader's MQL5 folder was created, changed or deleted.

---

### User Story 4 - Fast reruns (Priority: P2)

MetaEditor's verdicts are recorded per file content, so after the first full run the plugin side can be re-scored in minutes without recompiling anything, and only files whose content changed are recompiled.

**Why this priority**: The harness is useful only if it runs after every plugin change. Recompiling ~1,550 files each time would make it too slow to use.

**Independent Test**: After a full run, a rerun with no corpus change makes zero MetaEditor calls and still produces the full report.

**Acceptance Scenarios**:

1. **Given** recorded verdicts for every file, **When** the harness reruns with an unchanged corpus, **Then** MetaEditor is not started.
2. **Given** one corpus file edited, **When** the harness reruns, **Then** only that file is recompiled.

---

### User Story 5 - The corpus covers the language, not one repository (Priority: P2)

The corpus is a fixed, documented list: MetaQuotes' Standard Library, examples and free code, plus public, licensed MQL repositories chosen for language variety (templates, large class hierarchies, vector/matrix maths, MQL4 and MQL5). The owner's EA can be measured but is reported separately and never decides the score.

**Why this priority**: Judging by one repository hid template gaps; the score must reflect the language.

**Independent Test**: The report shows the score per corpus source and a total that excludes the owner's EA.

**Acceptance Scenarios**:

1. **Given** the corpus manifest, **When** the harness runs, **Then** every listed source is read in place at its pinned version and none of its files are copied into the plugin repository.
2. **Given** the owner's EA is included, **When** the report is produced, **Then** it appears as report-only and is excluded from the headline score.

### Edge Cases

- A repository's file includes a header MetaEditor can't find (the repo expected to live inside MetaTrader's Include folder): the file is excluded from the score and counted under "setup: missing include", never as a plugin miss.
- A repository has more than 30% of its files excluded for setup reasons: the report flags that repository's setup as untrustworthy.
- MetaEditor crashes, hangs or produces no log for a file: the file is recorded as "no verdict" with the reason and excluded from the score; the run continues.
- A file is a header (`.mqh`) MetaEditor can't compile on its own: it is judged through a program that includes it, or excluded with the reason "header without a program".
- MetaEditor and the plugin agree that a file has errors but report them on different lines: counted as agreement on the file, with a separate "line mismatch" count.
- Warnings: reported separately from errors and never part of the headline score.
- The same file content appears in two repositories: verdicts are shared, the file is scored once per source.
- The process table can't be read: treated as "a backtest may be running", so the harness refuses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST read every corpus source in place, from a manifest that names each source, its location and its pinned version.
- **FR-002**: The harness MUST obtain MetaEditor's verdict (errors and warnings with code, message, file and line) for each corpus program, with each repository's own headers available to MetaEditor without writing into MetaTrader's folders.
- **FR-003**: The harness MUST record MetaEditor's verdicts keyed by file content, and reuse them while the content is unchanged.
- **FR-004**: The harness MUST obtain the plugin's verdict for the same files: parse errors, annotator errors and every error-level inspection that is on by default.
- **FR-005**: The harness MUST classify each judged file as agreement, false error (plugin error, MetaEditor clean), missed error (MetaEditor error, plugin clean), or both-flag (both report errors), with line mismatches counted separately.
- **FR-006**: The harness MUST exclude, and count separately, files without a usable MetaEditor verdict (missing include, no log, crash, header without a program).
- **FR-007**: The harness MUST produce a report with the headline counts, the score per corpus source, and disagreement kinds ranked by affected files with up to 5 file:line examples each.
- **FR-008**: The harness MUST refuse to start compiling, and MUST stop before the next compile, whenever a Strategy Tester agent, a terminal running a test, or an `mt5 backtest` driver is running, or when the process table can't be read.
- **FR-009**: The harness MUST NOT create, change or delete anything under MetaTrader's installation, and MUST verify this at the end of each run.
- **FR-010**: The harness MUST NOT copy corpus files into the plugin repository; reports may quote file paths and line numbers, not code.
- **FR-011**: The plugin-side scoring MUST run as part of the plugin's test tooling, without MetaEditor, using the recorded verdicts.
- **FR-012**: The harness MUST be able to fail the plugin's gate when the false-error count rises above a recorded baseline, the same way the corpus gate ratchets.
- **FR-013**: Two runs with no plugin or corpus change MUST produce identical reports.
- **FR-014**: The unit of judgement MUST be the MQL5 program (`.mq5`) together with the headers it includes; a header's diagnostics are judged through the programs that include it. MQL4 files (`.mq4`), which MetaTrader 5's MetaEditor cannot compile, MUST be reported as "no referee" with plugin-side counts only, and MUST NOT enter the headline score.
- **FR-015**: The harness MUST cross-check its plugin-side setup against the real IDE: on the owner's EA and three corpus repositories, its error counts per file MUST equal those the installed plugin reports live in CLion; a mismatch marks the run untrustworthy.
- **FR-016**: Three named corpus repositories MUST be held out: scored only on request (at release time) and reported separately, so the plugin can't be tuned to the open set.
- **FR-017**: The harness MUST include a mutation set: for a fixed, seeded sample of corpus programs, copies (outside every repository) with one known error injected per kind (missing `;`, misspelt identifier, wrong argument count, type mismatch, unbalanced brace, undeclared member). A mutant counts only if MetaEditor rejects it; the report gives, per kind, the share of counted mutants the plugin flags. Released corpus code compiles cleanly, so without mutants "missed errors" cannot measure detection.
- **FR-018**: Every corpus header not included by any corpus program MUST be judged through a generated stub program (the header's include plus an empty entry point), created outside every repository and never committed.
- **FR-019**: The harness MUST hold its own lock and MUST NOT compile while any other MetaEditor process is running.
- **FR-020**: A report MUST NOT mix verdicts from different MetaEditor builds; after a build change, affected verdicts are recompiled before the next score.
- **FR-021**: The mutation generator MUST choose mutation sites from the raw text and tokens alone, never from the plugin's parser or resolver, so the sample is not biased toward code the plugin already understands. A mutant is "caught" only when the plugin reports an error on the mutated line (±1); a warning there is reported separately as "caught as warning".
- **FR-022**: The classification rules (line tolerance, exclusion reasons, which diagnostics count) are fixed in data-model.md. Changing them MUST be its own commit that shows the headline numbers before and after, and MUST NOT share a commit with a plugin change.

### Key Entities

- **Corpus source**: a named body of MQL code (MetaQuotes Standard Library, examples, free code, or a public repository), its location, pinned version, licence and role (scored or report-only).
- **MetaEditor verdict**: for one file content: errors and warnings (code, message, file, line), or a reason there is no verdict.
- **Plugin verdict**: for the same file: the plugin's error-level diagnostics (kind, message, line).
- **Comparison result**: per file: agreement, false error, missed error, both-flag, excluded (with reason), plus line mismatches.
- **Report**: headline counts, per-source scores, ranked disagreement kinds with examples, excluded-file counts, and the MetaTrader-untouched check.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A full run gets a usable MetaEditor verdict for at least 85% of the corpus's MQL5 programs (the rest excluded with a stated reason); MQL4 files are counted separately as "no referee".
- **SC-002**: After the first full run, re-scoring the plugin side takes under 10 minutes with zero MetaEditor calls.
- **SC-003**: Two consecutive unchanged runs produce byte-identical reports.
- **SC-004**: Zero files under MetaTrader's MQL5 folder are created, changed or deleted across every run, verified by the run itself.
- **SC-005**: The harness never compiles while a backtest runs: a test that starts a fake tester process mid-run sees the harness stop before its next compile.
- **SC-006**: The first report names the top 5 disagreement kinds with file counts, giving the next syntax or logic features a measured order.
- **SC-007**: The first report gives a catch rate per mutation kind over at least 50 counted mutants per kind.

## Assumptions

- MetaEditor 64 accepts `/include:"path"` (a folder standing in for the MQL5 folder) under Wine, so each repository can get its own include folder in a temporary location. If it doesn't, headers are staged in a temporary folder by another route, still never inside MetaTrader's folders. This is the riskiest assumption and is tested first.
- The corpus is the 15 public repositories in `~/mql-corpus` (1,127 files: 219 `.mq5`, 153 `.mq4`, 755 `.mqh`; pinned in its MANIFEST) plus MetaQuotes' code from the local MetaTrader install (~432 files). Changing the list is a deliberate, recorded change.
- No MetaTrader 4 is installed, so MQL4 code has no referee in this feature.
- Compiling the full corpus once takes hours under Wine; that is acceptable because verdicts are recorded and reused.
- Only errors decide the headline score; warnings and the plugin's opt-in style checks are out of scope for the score.
- Logic checks beyond MetaEditor (the plugin's safety inspections) are not judged by this harness; MetaEditor accepting code sets the floor, not the ceiling.
- Fixing any gap the harness finds is out of scope: each becomes its own feature.
- The harness MVP (through the live cross-check) is time-boxed to two working sessions; feature 002 (template type parameters) proceeds alongside it under the existing corpus gate, so the plugin improves while the referee is built.
- 5 of the 15 public repositories have no MQL5 programs (headers only), which is why FR-018 exists.
