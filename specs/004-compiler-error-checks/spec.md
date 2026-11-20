# 004: Compiler-error checks the plugin can make without MetaEditor

## Why

The MetaEditor harness (spec 001) seeds six kinds of mistake into real programs. The plugin caught
about 90% of misspelt names and members but about 0% of the other four: a missing `;`, a wrong
argument count, a type mismatch and an unbalanced brace. MetaEditor's inline compile reports these,
but the plugin skips that compile while a backtest runs (`compiler/StrategyTester`), and the owner's
sessions run backtests often. In those hours the plugin's own checks are the only ones.

## Goal

Raise each kind's catch rate as measured by `tools/harness/harness.sh`. False errors must not rise
above the baseline (7 open-source programs), and the corpus gate's compiling code
(Standard Library, examples, free robots, the EA) must get 0 new errors.

## Scope

1. Missing `;`: `MissingSemicolonInspection` (ERROR).
2. Wrong argument count on calls to functions the plugin can see (ERROR). Built-ins need an arity
   catalog verified in MetaEditor, so they come after.
3. Type mismatch: the two shapes the harness seeds, a scalar given a `{...}` initializer
   ("too many initializers") and an object pointer given a number.
4. Unbalanced brace: MetaEditor itself reports it far from the missing brace (150 of 152 mutants), so
   the near-the-line catch rule can't fairly score it. Out of scope unless the rule changes, which is
   its own commit (data-model.md markers).

## Premortem (inversion)

| Failure | Guardrail |
|---|---|
| Red errors on valid code (macros, labels, initializer lists, template calls) | 0 on the corpus gate's compiling code; harness false-error may not rise |
| A macro defined in a header the plugin can't read | skip files with unresolved includes; skip statements naming a `#define` |
| Overloads and default arguments make an argument count look wrong | report only when the count fits no visible function of that name |
| The check passes in tests and fails on real code | every change goes through the gate and the harness, not just unit tests |
| Tuning on the scored corpus | held-out sources (`MQL_HARNESS_HELDOUT=1`) checked before a release |

## Status

- Missing `;`: done. Catch 1% -> 85% (132/155). Fixing it uncovered a parser bug: explicit
  template arguments in an initializer (`new CPair<K,V>(...)`, `Array::Size<int, T *>(...)`) split
  the declaration at their comma and declared a variable named after a type argument.
- Type mismatch (value list given to a single value): done. `ScalarInitializerListInspection`
  (ERROR). Catch 0% -> 99% (143/144); false errors 7 (unchanged); 0 on the corpus gate.
- Wrong argument count, the program's own functions: done as a WARNING (`ArgumentCountInspection`);
  0 on the corpus gate. Harness catch stays 0%: the seeded calls are almost all built-ins
  (ArraySetAsSeries 22, SetIndexBuffer 12, ArrayResize 5 ...). Declaration initializers are flat
  tokens, so the argument counter reads them from the tokens.
- Next: built-in argument counts. The only catalog with parameter lists (`mql4-signatures.json`) comes
  from the MQL4 documentation, so it can't drive an error. Each count must be verified by compiling a
  probe in MetaEditor (D-1: no doc text), and only while no backtest runs.
