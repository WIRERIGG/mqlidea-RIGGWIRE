# Pre-mortem: 003 Check Members of vector, matrix and complex

**Verdict: GO, narrow.** A real detection gain (error 256 on built-in value types) using an existing verified catalog; small code.

**Win:** misspelt `vector`/`matrix`/`complex` members flagged as MetaEditor does, with 0 false errors on every corpus.
**Ruin line:** false errors on valid code (constitution I), which teach users to ignore the check.

| Failure | Likelihood | Recoverable? | Guardrail or tripwire |
|---|---|---|---|
| The catalog misses a real member, so valid code is flagged | med | painful | Accept a name listed anywhere (methods, statics, fields); ⛔ every corpus flag reviewed; a missing name is added only after a MetaEditor compile, else the check stays off for that name |
| Wrong receiver type: an inner `CFoo v` hides an outer `vector v`, or `vector arr[]` indexed | med | painful | Type only from the resolved declaration after the nearest-lexical scan agrees (FR-003); no `[]`, call or cast receivers |
| MQL4 code using a class named `vector` | low | recoverable | MQL5 files only |
| Instance use of a static (`v.Zeros(3)`) is actually legal or illegal | med | recoverable | Accept statics on instances (can only miss an error, never invent one) |

**Inverted assumption:** "this improves error detection measurably." It does only if people misspell these members; the gain is the same class of check MetaEditor does at compile time, now inline, and the mutation set (001 FR-017, undeclared-member kind) will measure it.
