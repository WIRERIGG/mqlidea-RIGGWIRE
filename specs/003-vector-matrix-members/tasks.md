# Tasks: Check Members of vector, matrix and complex

- [X] T001 Rank the Standard Library's unresolved uses by name (full gate samples): vector/matrix members ~300, template-typed members ~130 (need instantiation: out of scope), built-in functions/struct fields (noise or by design)
- [X] T002 Probe the type resolver: it returns nothing for every built-in receiver (classes only)
- [X] T003 `VectorMatrixCatalog.Members.has` (method, static or field) and `MqlTypeResolver.resolveBuiltinValueTypeName` (declaration-proven, nearest lexical declaration honoured, single resolve target, no arrays)
- [X] T004 `UndeclaredIdentifierInspection`: vector/matrix/complex members in MQL5 files
- [X] T005 Tests (6): misspelt members flagged (field `matrix<double>`, `vector<T>&` parameter, `vectorf`, `complex`), valid members incl. statics clean, unproven receivers clean (template `T`, call result, indexed element, array `.Size()`), shadowing, MQL4
- [X] T006 ⛔ Corpus gate: one false error found (`complex &x[]; x.Size()` in Alglib, an array receiver) → arrays skipped, test added → gate identical to baseline
- [X] T007 ⛔ Public corpus (1,127 files incl. ML5): undeclared flags identical to 002 (0 new); other counts within the known run-to-run noise
- [ ] T008 Catch rate measured by the 001 harness mutation set (undeclared-member kind) once MetaEditor is free
