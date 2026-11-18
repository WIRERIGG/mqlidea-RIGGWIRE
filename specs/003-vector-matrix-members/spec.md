# Feature Specification: Check Members of vector, matrix and complex

**Feature Branch**: `003-vector-matrix-members` (stacked on `002-template-parameters`)

**Created**: 2026-11-17

**Status**: Implemented (see tasks.md)

**Input**: "Make the plugin powerful for the syntax and logic": the biggest remaining class of uses the plugin understands but never checks.

## Why

`obj.NoSuchMember` is already reported for project classes and built-in structures (`MqlDateTime dt; dt.hours`), as MetaEditor's error 256. For MQL5's built-in `vector`, `matrix` and `complex` types nothing is checked: `v.Summ()` or `m.Rowz()` passes silently and only fails at compile time. MetaQuotes' own library leans on these types (about 300 member uses in Alglib alone), and so does public ML code. The plugin already ships a MetaEditor-verified catalog of their members (55 vector methods, 78 matrix methods, statics, `complex` fields); it is used for completion only.

## User Scenarios & Testing

### User Story 1 - A misspelt vector or matrix member is flagged (P1)

**Acceptance Scenarios**:

1. **Given** `vector v; v.Summ();`, **Then** `'Summ' - undeclared identifier` on `Summ`.
2. **Given** a `matrix<double>` field used in a method (`m_matrix.Rowz()`), a `vector<T> &x` parameter (`x.Resze(n)`), a `vectorf` local, or `complex z; z.rel`, **Then** each misspelt member is flagged.
3. **Given** every valid member (methods, fields, and the static constructors), **Then** nothing is flagged.

### User Story 2 - Never a false error (P1)

**Acceptance Scenarios**:

1. **Given** an `.mq4` file (MQL4 has no `vector`), **Then** no vector checks run.
2. **Given** a nearer declaration of the same name with another type (a local `CFoo v;` hiding a `vector v` parameter), **Then** no vector check runs on it.
3. **Given** a receiver whose type isn't proven from a declaration (a template parameter type `T v`, an indexed element `a[i].`, a call result `f().`, a cast), **Then** nothing is flagged.
4. **Given** MetaQuotes' Standard Library, examples, free code, and the 1,127-file public corpus, **Then** no member that MetaEditor accepts is flagged.

## Requirements

- **FR-001**: A member accessed with `.` on a plain name whose declaration (local, global, parameter or class field) has type `vector`, `matrix`, `complex` or a typed variant (`vectorf`, `vectorc`, `matrixf`, `matrixc`, `vector<T>`, `matrix<double>`) MUST be reported as undeclared when the catalog lists it under none of methods, statics or fields.
- **FR-002**: Only MQL5 files are checked.
- **FR-003**: The receiver type MUST come from the declaration the name resolves to, after the nearest lexical declaration is honoured; no text guessing.
- **FR-004**: The corpus gate keeps 0 false undeclared errors on the gated corpora; on the public corpus every new flag is reviewed and must be a real error.

## Success Criteria

- **SC-001**: Each acceptance scenario is a passing test.
- **SC-002**: 0 new flags on the gated corpora; every new public-corpus flag reviewed and confirmed (or the check narrowed).

## Assumptions

- The catalog lists only names verified in MetaEditor; a real member missing from it would show up as a corpus flag (SC-002) and be added only after compiling it in MetaEditor (catalog rule).
- Resolving `v.Sum` to a declaration (navigation) is out of scope: built-in members have no source to navigate to.
