# Pre-mortem: 001 MetaEditor Comparison Harness

**Verdict: SHRINK, then go.** The idea holds, but the spec counted files MetaEditor can never judge. Scope is cut to what MetaEditor 5 can referee; the spec is corrected (see "Spec changes" below) before planning.

**Win:** one repeatable score (false errors, missed errors) over every MQL5 program in a broad corpus, plus the headers those programs include, that every later syntax or logic change must move the right way.

**Ruin line:** anything written into MetaTrader's folders, a backtest disturbed by a compile, or third-party code copied into the plugin repository.

## How this fails (sorted, ruin first)

| Failure | Likelihood | Recoverable? | Guardrail or tripwire |
|---|---|---|---|
| Third-party headers land in MetaTrader's Include folder to make a repo compile | low | ruin | Only a temporary MQL5 stand-in folder under /tmp via `/include:`; the run snapshots MetaTrader's MQL5 listing before and after and fails loudly on any difference (FR-009) |
| A compile runs beside a backtest and disturbs it | med (backtests run most days) | painful | Refuse to start, and recheck before every single compile, using the plugin's own `StrategyTester` table; unreadable table counts as busy (FR-008) |
| **The target can't be met: 153 of 1,127 corpus files are MQL4 and this machine has no MetaTrader 4, and 755 are headers MetaEditor judges only through a program** | certain (measured) | recoverable | Score programs (`.mq5`) and the headers reached from them; MQL4 files are reported as "no referee" (plugin-side counts only) until an MT4 MetaEditor exists. SC-001 restated in programs, not files |
| The plugin is measured in a test fixture that differs from real CLion (include roots, dialect, light project), so the score describes a setup no user has | med | painful (false confidence) | Cross-check: on the owner's EA and 3 corpus repos, the harness's plugin-side error counts must equal what `tools/clion-mcp-check.py` reports live in CLion; mismatch stops the run from being trusted |
| Every disagreement is really a repo-setup problem (missing headers, wrong folder layout), not a plugin gap | high | recoverable | MetaEditor "can't open include" files are excluded and counted; a repo over 30% excluded is flagged and its setup fixed before its numbers count |
| Overfitting: later features tune the plugin to these exact repos, and the score stops meaning "the language" | med (over months) | painful | Hold out 3 repositories as a sealed check, scored only at release time; a feature that improves the open set but worsens the held-out set is rejected |
| `/include:` doesn't work under Wine, or symlinks don't resolve through Wine | med | recoverable | First task is a one-repo spike; fallback is copying headers into the /tmp stand-in folder (still never into MetaTrader) |
| Full compile takes many hours and blocks MetaTrader for other sessions | med | recoverable | Compile in small batches between backtests, resumable, verdicts recorded per file content (US4) |

## Inverted assumption

"MetaEditor agreeing with the plugin means the plugin is right." For errors, yes. But a clean MetaEditor compile says nothing about logic (an unchecked `OrderSend` compiles fine). The harness is the floor: it proves the plugin never cries wolf and never misses a compile error. The plugin's logic checks beyond the compiler stay judged by their own tests, and stay off by default until the harness shows they raise zero false errors. This holds; the spec already says it.

## Spec changes required before planning

1. Unit of judgement: MQL5 **programs** (`.mq5`) and the headers they include, not every file. MQL4 files: plugin-side numbers only, labelled "no referee".
2. SC-001 restated: at least 85% of corpus `.mq5` programs get a usable MetaEditor verdict.
3. Add the live cross-check (fixture vs CLion) as a requirement.
4. Add the held-out repositories as a requirement.

## Next action

Apply the four spec changes, then `/speckit-plan`, whose first task is the one-repo `/include:` spike (once no backtest is running).

## Second pass (/invert on the spec, 2026-11-17)

New failures found and folded into the spec as FR-017..FR-020 and SC-007:
- Released corpus code compiles cleanly, so missed errors stay near 0 regardless of the plugin: detection needs a mutation set (FR-017).
- 5 of 15 repositories have no MQL5 programs and sibvic has 5 programs for 278 headers: headers need stub programs (FR-018).
- Concurrent MetaEditor runs (another session's `mt5 compile`, the plugin's background compile) can clash: own lock, no compile beside another MetaEditor (FR-019).
- MetaEditor self-updates: never mix builds in a score (FR-020).
- Process: building the referee could crowd out improving the plugin: MVP time-boxed to 2 sessions, feature 002 (template parameters) runs alongside.

## Third pass (/latticework + /invert, 2026-11-17)

- Incentives: the same agent writes plugin fixes and the scorer, so rules could drift toward better numbers: rules frozen, rule changes isolated with before/after numbers (FR-022, T019f).
- Second-order: a mutation generator using the plugin's parser picks only sites the plugin understands: text/token-based generator; "caught" means an error on the mutated line ±1, warnings reported apart (FR-021).
- Base rates: the 2-session time-box covers the core T001–T019 only.
- Diminishing returns: this pass found smaller issues than the second; stop analysing, implement.
