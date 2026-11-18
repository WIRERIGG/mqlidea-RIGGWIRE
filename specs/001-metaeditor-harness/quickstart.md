# Quickstart: MetaEditor Comparison Harness

1. **Referee (MetaTrader idle only).** `python3 tools/harness/metaeditor_verdicts.py` compiles every program whose verdict is missing or stale and stops before the next compile if a backtest starts. Rerun to resume. It ends by printing `MetaTrader MQL5 folder: unchanged` or failing.
2. **Plugin side (any time).** `zsh tools/harness/harness.sh` runs `gate.HarnessTest` against the stored verdicts and writes `build/harness-report.md`. Add `MQL_HARNESS_HELDOUT=1` at release time; `MQL_HARNESS_UPDATE=1` after a deliberate change rewrites the baseline.
3. **Live cross-check (once per release).** Open the EA and the three cross-check repos in CLion with the installed plugin, run `python3 tools/clion-mcp-check.py <project> <subdir>`, and compare error counts per file with the report's per-file section. Any difference means the harness's setup doesn't match the IDE: fix that before trusting the score.
