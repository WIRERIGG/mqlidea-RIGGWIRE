# Findings: first MetaEditor harness report (2026-11-18)

MetaEditor build 6230; 569 verdicts (234 programs, 335 header stubs) and 1,006 counted mutants; MetaTrader's MQL5 folder untouched. Paths, lines and MetaEditor codes only: no corpus code is copied here (D-1).

## Top 5 disagreement kinds (open sources, baseline report on this branch)

| # | Kind | Programs | Where | What it means | Feature |
|---|---|---|---|---|---|
| 1 | MetaEditor 246 "cannot convert parameter 'MqlDateTime&' to 'const DateTimeEntry&'" | 54 | EA31337 `DateTime.mqh:66` | A struct passed where a derived struct reference is expected. MetaEditor 5 rejects it; the plugin has no argument type checks | Argument type checks (with #4 below) |
| 2 | MetaEditor 200 "parameter passed as reference, variable expected" | 45 | EA31337 `DictStruct.mqh:170`, `Dict.mqh:124` | A temporary passed to a `T&` parameter. The plugin doesn't check reference arguments | Reference-argument check |
| 3 | Plugin UndeclaredIdentifier | 38 | EA31337 `Indicators/**/tests/*.test.mq5:48-53` | The plugin flags names its include resolution can't see. Most of these disappear on the fix branch (unseen-include guard, `struct {…} v;`, qualified types) | Fixed on `fix/builtins-and-import-calls`: 31 → 7 false errors when combined |
| 4 | Plugin parse error (PsiErrorElement) | 35 | EA31337 `Indicators/Indi_*.mqh:38-51`, `DictBase.mqh:109` | Forms the parser rejected. One was `unsigned int` after another parameter (`unsigned` was lexed as a type name), now fixed on the fix branch. The rest are still open | Parser: remaining EA31337 forms |
| 5 | MetaEditor 216 "'r' - structure have objects and cannot be copied" | 34 | EA31337 `Order.struct.h:1001` | A struct holding objects or strings assigned by value. MetaEditor 5 rejects the copy | Struct-copy check |

EA31337 dominates because build 6230 is stricter than the compiler the library was written for: 129 of its 136 programs fail in MetaEditor. Those are genuine verdicts. The plugin should report them, and today it doesn't.

## Mutation set: what the plugin catches

| Kind | Counted | Caught (baseline) | Caught (fix branch, combined) |
|---|---|---|---|
| misspelt identifier | 164 | 150 (91%) | 148 (90%) |
| undeclared member | 110 | 102 (93%) | 102 (93%) |
| missing `;` | 155 | 1 | 1 |
| unbalanced brace | 134 | 2 | 2 |
| type mismatch | 144 | 0 | 0 |
| wrong argument count | 144 | 0 | 0 |

The four near-zero kinds are the next features. Each needs its own spec with the parse-error ruin line from 002's pre-mortem:
1. **Missing `;`**: the parser recovers silently. Report the recovery point as an error, matching MetaEditor's line.
2. **Argument count** (MetaEditor 199): built-ins (the catalogue has signatures) and user functions (PSI has parameters, defaults and overloads).
3. **Type mismatch** (MetaEditor 246/219): assigning a number to a pointer or object, and an initialiser list to a scalar.
4. **Unbalanced brace**: reported at the opening brace, not where MetaEditor reports it (the end of file or the next function). This is a rule question for the FR-022 scoring rules: change it in its own commit if line agreement should allow it.

## Found while building the harness (fixed)

- **Fix branch:** a quoted `#include` from a file sitting directly in an include root didn't resolve when that root was also project content (Object.mqh → "StdLibErr.mqh"). The unseen-include guard then silenced checks for every Standard Library user in the gate and harness setups. The mutation set caught it; the corpus gate couldn't. Fixed with a regression test.
- **Fix branch:** in MQL5, a for-loop variable used after its loop is now reported, matching MetaEditor's error 256.
- **Referee:** it now builds `#resource` sources MetaEditor can't build itself, and no longer stubs headers in MQL4 folders.
