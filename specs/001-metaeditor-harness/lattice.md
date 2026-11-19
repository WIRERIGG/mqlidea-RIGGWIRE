# Lattice: 001 MetaEditor Comparison Harness plan

**Verdict:** the plan is sound but has three defects that would make its numbers misleading or unusable; all three are fixed in plan.md / research.md / data-model.md before tasks.

**Models used:** First principles, Bottleneck, Margin of safety (plus inversion from premortem.md).

## First principles: what is actually true?

- **The busy rule is too broad.** R4 counted any running `terminal64` as busy. A plain terminal with charts open is not a backtest, and MetaEditor compiles are safe beside it (established for the bridge). The owner's terminal is often open, so the referee would starve. **Fix:** use the plugin's *background-compile* rule (`StrategyTester.isRunning`): busy = a `metatester64` agent, an `mt5 backtest` driver, or a `terminal64` started with a `/config:` (a tester run); unreadable table = busy. The backtest run config keeps its stricter rule; this harness doesn't launch backtests.
- **"Both report errors" is not agreement.** If the plugin flags a false parse error on line 40 and MetaEditor reports a real error on line 900, calling that "agree-errors" hides a false error. **Fix:** a program where both flag errors but no plugin error line matches a MetaEditor error line (same file, ±1 line) is its own outcome, `disjoint-errors`, shown in the headline and listed with both sides.
- **Cascades are real.** One MetaEditor syntax error often produces dozens of follow-on errors; the plugin's error recovery produces fewer. Counting errors would punish the plugin for recovering well. **Confirmed in plan:** outcomes are per program; kinds use the *first* error per file on each side.

## Bottleneck: what limits the whole thing?

- **Per-repository header setup, not code.** Each of 15 repos expects its own layout under `MQL5/Include` (EA31337 alone has 403 files). Until a repo's `include_roots` are right, every one of its programs is "missing include" and the score is noise. **Fix:** build the whole pipeline end to end on **3 repos first** (MVP: `geraked__metatrader5`, `sibvic__mq5-templates` for templates, MetaQuotes' Examples), then onboard the rest one by one, each gated by the premortem's 30%-excluded tripwire.
- **The `/include:` + symlink spike** stays task 1; nothing else is built until it passes.

## Margin of safety: what if estimates are off by 30-50%?

- **Referee time:** even at 3× the estimate (~15 s per program), ~410 programs is under 2 hours, run once and resumable: survivable.
- **Plugin side:** `doHighlighting` over ~1,500 files might take 3× the 10-minute target. **Tripwire:** if the MVP's per-file average × corpus size exceeds 10 minutes, highlight only programs and the headers MetaEditor named (the rest can't disagree), before any deeper optimisation.
- **Determinism:** highlighting order can vary; the report sorts everything (source, path, line) and excludes timestamps, so SC-003 holds by construction.

## Where the models agree / conflict

All three say: shrink the first build to 3 repos and make the classification strict. The one tension is scope versus speed: onboarding all 15 repos is what makes the score "the language", but doing it before the pipeline works wastes the setup effort. MVP first resolves it.

## Plan changes applied

1. research.md R4: tester-only busy rule (above).
2. data-model.md: new outcome `disjoint-errors`; kinds use first error per file.
3. plan.md: MVP of 3 repos before onboarding the rest; plugin-side time tripwire.
