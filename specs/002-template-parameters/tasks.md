# Tasks: Template Type Parameters Resolve

- [X] T001 Dump today's PSI for class, function and out-of-line templates (header tokens are loose; uses are unresolved references)
- [X] T002 [US1] `TEMPLATE_HEADER` / `TEMPLATE_PARAMETER` element types and `parseTemplateHeader` (top level and class bodies), rolling back on any other shape
- [X] T003 [US1] `MQL4TemplateParameterElement` (no stub) + factory + declaration-name check
- [X] T004 [US1] `resolveTemplateParameter`: innermost enclosing header, before locals and globals, not after `.`
- [X] T005 [US2] Find usages type and in-place rename
- [X] T006 [US1/US2] `MqlTemplateParameterTest`: 11 tests (class, several parameters, function, out-of-line, `class` form, member template hiding, precedence over a class `T`, no leak, find usages, rename, incomplete header)
- [X] T007 ⛔ Corpus gate: Standard Library unresolved 6,112 → 4,879 (SC-001 ≥1,000 met), resolved +1,048, every inspection and parse count unchanged, EA unchanged
- [X] T008 [US3] Remove the name-anywhere fallback; test that a stray `T` is flagged
- [X] T009 ⛔ Public corpus (1,127 files) alone, master vs branch: parse errors 371 = 371; first pass +33 undeclared (modifier between header and function, body parsed apart from its signature) → tolerant `templateHeaderBefore` + 3 tests → undeclared flags identical to master (2,198, none new); one false undefined-function call gone (`T(x)` cast); a +1 MissingDestructor did not reproduce on the file alone and master itself varies run to run (resolved ±97): public-corpus gate runs are not fully deterministic (note for 001 SC-003)
- [X] T009b Found in passing: `unsigned int` in a parameter list is a plugin parse error (EA31337 SerializerDict.mqh); whether MetaEditor accepts it is for the 001 harness / one compile once backtests stop
- [X] T010 Rebaseline: Standard Library unresolved 6,112 → 4,853 (−1,259), resolved 394,613 → 395,687; README/CLAUDE.md; 658 tests
- [X] T011 Live check in CLion after the next install (owner): 2026-11-19, 2026.1.10 in CLion 2026.3; geraked's templated `Storage.mqh`, `EAUtils.mqh` and `WinINet.mqh` show no errors
