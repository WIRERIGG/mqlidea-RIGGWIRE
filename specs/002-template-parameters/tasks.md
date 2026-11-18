# Tasks: Template Type Parameters Resolve

- [X] T001 Dump today's PSI for class, function and out-of-line templates (header tokens are loose; uses are unresolved references)
- [X] T002 [US1] `TEMPLATE_HEADER` / `TEMPLATE_PARAMETER` element types and `parseTemplateHeader` (top level and class bodies), rolling back on any other shape
- [X] T003 [US1] `MQL4TemplateParameterElement` (no stub) + factory + declaration-name check
- [X] T004 [US1] `resolveTemplateParameter`: innermost enclosing header, before locals and globals, not after `.`
- [X] T005 [US2] Find usages type and in-place rename
- [X] T006 [US1/US2] `MqlTemplateParameterTest`: 11 tests (class, several parameters, function, out-of-line, `class` form, member template hiding, precedence over a class `T`, no leak, find usages, rename, incomplete header)
- [X] T007 ⛔ Corpus gate: Standard Library unresolved 6,112 → 4,879 (SC-001 ≥1,000 met), resolved +1,048, every inspection and parse count unchanged, EA unchanged
- [X] T008 [US3] Remove the name-anywhere fallback; test that a stray `T` is flagged
- [ ] T009 ⛔ Corpus gate after US3 at 0 false undeclared errors, plus the 1,127-file public corpus (`MQL_EXTRA_CORPORA=report:public=~/mql-corpus`) with no new parse errors vs master
- [ ] T010 Rebaseline (`MQL_GATE_UPDATE=1`), README/CLAUDE.md notes, test count
- [ ] T011 Live check in CLion after the next install (owner)
