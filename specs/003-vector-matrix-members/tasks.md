# Tasks: Check Members of vector, matrix and complex

- [X] T001 Rank the Standard Library's unresolved uses by name (full gate samples): vector/matrix members ~300, template-typed members ~130 (need instantiation: out of scope), built-in functions/struct fields (noise or by design)
- [X] T002 Probe the type resolver: it returns nothing for every built-in receiver (classes only)
- [X] T003 `VectorMatrixCatalog.Members.has` (method, static or field) and `MqlTypeResolver.resolveBuiltinValueTypeName` (declaration-proven, nearest lexical declaration honoured, single resolve target, no arrays)
- [X] T004 `UndeclaredIdentifierInspection`: vector/matrix/complex members in MQL5 files
- [X] T005 Tests (6): misspelt members flagged (field `matrix<double>`, `vector<T>&` parameter, `vectorf`, `complex`), valid members incl. statics clean, unproven receivers clean (template `T`, call result, indexed element, array `.Size()`), shadowing, MQL4
- [X] T006 ⛔ Corpus gate: one false error found (`complex &x[]; x.Size()` in Alglib, an array receiver) → arrays skipped, test added → gate identical to baseline
- [X] T007 ⛔ Public corpus (1,127 files incl. ML5): undeclared flags identical to 002 (0 new); other counts within the known run-to-run noise
- [X] T008 Catch rate measured by the 001 harness mutation set (undeclared-member kind) once MetaEditor is free — **measured 2026-11-18; the random sample can't answer it.** None of the 128 counted undeclared-member mutants (seed 20261117, 2 per program) lands on a vector, matrix or complex receiver, so the harness says nothing about 003 specifically. Overall undeclared-member catch rate with 003 included: 102/110 open (93%). 003's coverage rests on its MetaEditor-verified catalogue and unit tests. A site filter on mutate.py could seed members on vector/matrix receivers if a number is wanted.
