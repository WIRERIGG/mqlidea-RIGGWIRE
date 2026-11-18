# Pre-mortem: 002 Template Type Parameters Resolve

**Verdict: GO.** Small, self-contained, measured by the existing corpus gate, and it unblocks the two larger template features. Scope stays at parameters only.

**Win:** every use of a template parameter in MetaQuotes' Standard Library resolves to its own header (≥1,000 fewer unresolved uses), with go-to, Find Usages and rename working, and nothing that resolves today lost.

**Ruin line:** a parser change that creates parse errors in real code: a parse error switches off the MetaEditor annotator for the whole file (constitution I).

## How this fails (sorted, ruin first)

| Failure | Likelihood | Recoverable? | Guardrail or tripwire |
|---|---|---|---|
| Turning the template header into PSI changes how the following class or function parses, creating parse errors in real code | med | painful (annotator off for those files) | Corpus gate must stay at 0 parse errors over Standard Library, examples, free code **and** the 1,127-file public corpus in `~/mql-corpus` (run it as an extra `report:` corpus); ⛔ any new parse error stops the change |
| Out-of-line definitions miss: 282 in the Standard Library are `template<typename T>` on the line before `CStack::CStack(...)`, and the parameter must scope over that definition, not the class's in-class one | high (it's the common form) | recoverable | Acceptance scenario US2-2; the gate's per-name count for `T`/`TValue`/`TKey` must fall, which it won't if out-of-line bodies miss |
| Scope leaks: two templates in one file both use `T` and resolve to each other's header, so rename edits the wrong template | med | painful (rename corrupts code) | Scope = the one declaration the header introduces; tests for two templates per file (US1-2, US2-1) and a member template inside a class template that reuses `T` |
| Stub schema change forgotten: stale indexes after upgrade, odd resolve results until a re-index | low | recoverable | If parameters become stubbed elements, bump the stub version (27 → 28); simpler: keep them as plain PSI (no stubs), since they are file-local by definition |
| Removing the name-anywhere workaround (US3) brings back false "undeclared" errors where scope detection misses | med | painful | Do US3 last; ⛔ corpus gate undeclared errors must stay 0 on every corpus, else keep the workaround as a fallback for names inside any template header in the file |
| Precedence bug: inside the template, a project class named `T` wins over the parameter | low | recoverable | FR-003 test with a project class and a typedef both named like the parameter |

## Inverted assumption

"Resolving `T` is valuable on its own." Partly: navigation and rename on `T` are modest wins. The bigger value is that template parameters become real declarations, which the next features (members through template-typed variables, members of `CStack<double>`) need. That holds; it is the right first slice, and it doesn't wait on the 001 harness.

## Changes to the spec

None required. Two decisions for the plan: template parameters as plain (non-stubbed) PSI, and the public corpus as an extra `report:` corpus in the gate run for this change.
