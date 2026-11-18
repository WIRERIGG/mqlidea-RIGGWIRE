# Research: MetaEditor Comparison Harness

## R1. Giving MetaEditor a repository's headers without touching MetaTrader

- **Decision**: per repository, build `/tmp/mqlidea-harness/<repo>/MQL5/` with `Include/` holding symlinks to each Standard Library entry of MetaTrader's `MQL5/Include` plus the repository's own header folders, and the repository's programs copied under `MQL5/Experts/<repo>/`. Compile with `MetaEditor64.exe /compile:"Z:\tmp\...\X.mq5" /include:"Z:\tmp\mqlidea-harness\<repo>\MQL5" /log`.
- **Evidence**: MetaEditor64.exe's own usage string reads `/compile:"path" [/include:"path"]` with `/include:"path" - path to MQL4\MQL5 folder` (read from the binary's UTF-16 strings, 2026-11-17). `mt5 compile` already proved `Z:\` paths reach MetaEditor under Wine (2026-11-15).
- **Unknown (spike T001)**: whether Wine follows macOS symlinks inside the stand-in. **Fallback**: copy the Standard Library into the stand-in once (read from MetaTrader, written only under `/tmp`).
- **Rejected**: installing repo headers into MetaTrader's Include (Principle IV, ruin line).

## R2. Which header root each repository expects

- **Decision**: per repository, `corpus.json` lists `include_roots`: folders whose contents stand in for `MQL5/Include` (e.g. mql-zmq's `Include/`, LadinoBot's `Include/` for `<LadinoBot/...>`). Found once by reading each repo's `#include <...>` lines; a repo whose angle includes still miss after that is excluded with the reason "setup: missing include".
- **Rejected**: guessing roots at runtime (non-deterministic; violates FR-013).

## R3. Verdict key

- **Decision**: sha256 over the program's bytes plus the sorted bytes of every file in its repository's header roots, plus the MetaEditor build number. Any header edit or MetaEditor update invalidates exactly the affected verdicts (US4).
- **Rejected**: program bytes only (a changed header would reuse a stale verdict).

## R4. Busy check

- **Decision** (revised by lattice.md): port the plugin's *background-compile* rule to Python: busy = a command line running `metatester64.exe` (path ends `\name.exe` or `/name.exe`), an `mt5 backtest` driver, or `terminal64.exe` started with `/config:` (a tester run); table from `ps -axww -o command=`; unreadable table = busy. Checked at start and before every compile.
- **Why not "any terminal64"**: a plain terminal with charts open is not a backtest, compiles are safe beside it, and the owner's terminal is often open, so the stricter rule would starve the referee.

## R5. Plugin-side verdict

- **Decision**: `myFixture.configureFromExistingVirtualFile(f)` then `myFixture.doHighlighting(HighlightSeverity.ERROR)` with every default-on error-level inspection enabled (`UndefinedFunctionCall`, `UndeclaredIdentifier`), include roots set via `MqlIncludeRoots.setTestRoots` per repository. Headers are highlighted too; their errors attach to the header file, as MetaEditor's log names the header's path.
- **Mapping MetaEditor paths**: the log prints Windows paths of the staged copy; strip the stand-in prefix to get the repo-relative path (same idea as the plugin's `DiagnosticFileMatcher`).

## R6. Held-out repositories

- **Decision**: `EarnForex/Account-Protector`, `Roffild/RoffildLibrary`, `landim32/LadinoBot` (one small app, one library, one framework). Role `heldout` in `corpus.json`; scored only with `MQL_HARNESS_HELDOUT=1`.

## R7. Live cross-check (FR-015)

- **Decision**: `tools/clion-mcp-check.py` already returns CLion's live problems per file for a project. Quickstart step: open the EA and `geraked__metatrader5`, `sibvic__mq5-templates`, `xxvw__ICT_Library_MQ5` in CLion, run the check, and compare error counts per file with `build/harness-report.md`'s per-file section. Manual, once per plugin release.

## R8. Throughput

- **Estimate** (to be measured in T001): one Wine MetaEditor start per program, a few seconds each, so ~410 programs ≈ 30–60 minutes total, run in batches between backtests. Verdicts persist, so it is paid once per corpus or MetaEditor change.
