# Research: MetaEditor Comparison Harness

## R1. Giving MetaEditor a repository's headers without touching MetaTrader

- **Decision**: per repository, build `/tmp/mqlidea-harness/<repo>/MQL5/` with `Include/` holding symlinks to each Standard Library entry of MetaTrader's `MQL5/Include` plus the repository's own header folders, and the repository's programs copied under `MQL5/Experts/<repo>/`. Compile with `MetaEditor64.exe /compile:"Z:\tmp\...\X.mq5" /include:"Z:\tmp\mqlidea-harness\<repo>\MQL5" /log`.
- **Evidence**: MetaEditor64.exe's own usage string reads `/compile:"path" [/include:"path"]` with `/include:"path" - path to MQL4\MQL5 folder` (read from the binary's UTF-16 strings, 2026-11-17). `mt5 compile` already proved `Z:\` paths reach MetaEditor under Wine (2026-11-15).
- **Settled by T001 (2026-11-18, MetaEditor build 6230, MetaTrader idle)**: `/include:` takes effect (2MAAOS.mq5 read `EAUtils.mqh` and `errordescription.mqh` from the staged Include) and Wine follows the macOS symlinks (MACD Sample read `Include\Trade\Trade.mqh`, `Object.mqh`, `StdLibErr.mqh` through them). No copy needed. The `.log` lands beside the staged program; MetaTrader's MQL5 folder was identical before and after four compiles; only `logs/metaeditor.log` (outside MQL5) grew.
- **Found by T001**: `#resource "\\Indicators\\X.ex5"` resolves from the MQL5 root, so a repo laid out like an MQL5 folder needs its `Experts/`, `Indicators/`, `Scripts/`, `Libraries/`, `Files/`, `Images/`, `Sounds/` (top level or under `MQL5/`) mirrored at the stage root too; without it 2MAAOS failed with errors 310/313 (a false "missed error" against the plugin). With the mirror it compiles clean.
- **Found by T010 (2026-11-18)**: MetaEditor builds a missing `#resource` from its `.mq5` itself, but not when that source has `#resource`s of its own (CEZLSMA -> ChandelierExit: "compiling ... failed", errors 310/313, although ChandelierExit compiles clean on its own). The referee now builds each missing resource's staged source first and retries the program once. DarvasBoxes: MetaEditor 5 rejects an initialised `extern` (error 303), so the plugin's annotator error there is right.
- **Rejected**: installing repo headers into MetaTrader's Include (Principle IV, ruin line).

## R2. Which header root each repository expects

- **Decision**: per repository, `corpus.json` lists `include_roots`: folders whose contents stand in for `MQL5/Include` (e.g. mql-zmq's `Include/`, LadinoBot's `Include/` for `<LadinoBot/...>`). Found once by reading each repo's `#include <...>` lines; a repo whose angle includes still miss after that is excluded with the reason "setup: missing include".
- **Rejected**: guessing roots at runtime (non-deterministic; violates FR-013).

## R3. Verdict key

- **Decision**: sha256 over the source name and program path (quoted includes resolve beside the program), the program's bytes, plus the sorted bytes of every file in its repository's header roots, plus the MetaEditor build number. Any header edit or MetaEditor update invalidates exactly the affected verdicts (US4).
- **Rejected**: program bytes only (a changed header would reuse a stale verdict).

## R4. Busy check

- **Added 2026-11-18**: the referee re-checks after each compile too; a compile that overlapped the start of a backtest (whose driver may kill MetaEditor) is discarded, not stored as a crash.


- **Decision** (revised by lattice.md): port the plugin's *background-compile* rule to Python: busy = a command line running `metatester64.exe` (path ends `\name.exe` or `/name.exe`), an `mt5 backtest` driver, or `terminal64.exe` started with `/config:` (a tester run); table from `ps -axww -o command=`; unreadable table = busy. Checked at start and before every compile.
- **Seen in T001 (2026-11-18)**: with MetaTrader closed there are no `metatester64` processes at all (no Wine process either), so the conservative rule never starved the referee there. Whether an open terminal keeps `/run` agents up when no test runs is still unobserved; the rule stays conservative (any `metatester64` is busy) until it is.
- **Open question (seen 2026-11-17)**: during a backtest, `ps` shows eight `metatester64.exe /run /address:0.0.0.0:200N` agents plus one `metatester64.exe /local ...` agent. If the `/run` agents stay up when no test runs, "any metatester64" would starve the referee too; the rule would then be `/local` agent, `mt5 backtest` driver, or `terminal64 /config:`. Observe `ps` after the backtests end before writing `is_busy()`.
- **Why not "any terminal64"**: a plain terminal with charts open is not a backtest, compiles are safe beside it, and the owner's terminal is often open, so the stricter rule would starve the referee.

- **Seen while building the referee (2026-11-17)**: every compile appends a summary line to `<MetaTrader>/logs/metaeditor.log` (the bridge relies on it), outside `MQL5/`. Unavoidable for any compile, `mt5 compile` included; the untouched check covers `MQL5/` as specified, and the report says so.

## R5. Plugin-side verdict

- **Decision**: `myFixture.configureFromExistingVirtualFile(f)` then `myFixture.doHighlighting(HighlightSeverity.ERROR)` with every default-on error-level inspection enabled (`UndefinedFunctionCall`, `UndeclaredIdentifier`), include roots set via `MqlIncludeRoots.setTestRoots` per repository. Headers are highlighted too; their errors attach to the header file, as MetaEditor's log names the header's path.
- **Mapping MetaEditor paths**: the log prints Windows paths of the staged copy; strip the stand-in prefix to get the repo-relative path (same idea as the plugin's `DiagnosticFileMatcher`).

## R6. Held-out repositories

- **Decision**: `EarnForex/Account-Protector`, `Roffild/RoffildLibrary`, `landim32/LadinoBot` (one small app, one library, one framework). Role `heldout` in `corpus.json`; scored only with `MQL_HARNESS_HELDOUT=1`.

## R7. Live cross-check (FR-015)

- **Decision**: `tools/clion-mcp-check.py` already returns CLion's live problems per file for a project. Quickstart step: open the EA and `geraked__metatrader5`, `sibvic__mq5-templates`, `xxvw__ICT_Library_MQ5` in CLion, run the check, and compare error counts per file with `build/harness-report.md`'s per-file section. Manual, once per plugin release.

## R8. Throughput

- **Measured in T001 (2026-11-18)**: 3.3 s (MACD Sample, ChartInChart), 4.9 s (2MAAOS), 10.1 s on the first, cold Wine start. All 16 sources: 587 programs and header stubs plus about 2,200 mutants, so roughly 3–4 hours of compiles in total, run in batches between backtests (the referee stops cleanly when one starts and reuses every verdict on the next run). Paid once per corpus or MetaEditor change.
