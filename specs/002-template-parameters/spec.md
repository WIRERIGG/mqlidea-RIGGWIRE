# Feature Specification: Template Type Parameters Resolve

**Feature Branch**: `002-template-parameters`

**Created**: 2026-11-17

**Status**: Draft

**Input**: User description: "Template type parameters (template<typename T>) resolve: uses of T inside the template's body go to the parameter's declaration, with highlighting, find usages and rename."

## Why

MQL5 templates (`template<typename T>`, `template<typename TKey,typename TValue>`) are core language syntax and MetaQuotes' own library uses them heavily: 317 template headers in `Generic/`, `Math/` and `Arrays/` alone. Today a template parameter is not a declaration the plugin knows: the plugin only avoids calling it undeclared by matching the name anywhere in the file. So go to declaration, find usages, rename and highlighting do nothing on `T`, and the corpus gate counts about 1,150 unresolved uses in the Standard Library (`T` 996, `TValue` 150, plus `TKey`, `TItem`). The name-anywhere workaround can also hide a real error: a stray `T` outside any template is never reported.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navigate a template parameter (Priority: P1)

Inside `template<typename TKey,typename TValue> class CHashMap { TValue Get(TKey key); }`, a developer Ctrl-clicks `TValue` in the method and lands on `TValue` in the template header; Find Usages on the header's `TKey` lists every use inside that class and nothing outside it.

**Why this priority**: navigation is the basic promise of the plugin and today it silently does nothing on the most common names in generic code.

**Independent Test**: open a file with a template class and a template function; go to declaration from each use reaches its own header; Find Usages on each parameter lists exactly its uses.

**Acceptance Scenarios**:

1. **Given** `template<typename T> class CList { T m_data[]; T At(int i); };`, **When** go to declaration on either `T`, **Then** the caret lands on `T` in `template<typename T>`.
2. **Given** two templates in one file, each with its own `T`, **When** Find Usages on the first header's `T`, **Then** only uses inside the first template are listed.
3. **Given** a template function `template<typename T> T Max(T a, T b) { T r = a; return r; }`, **When** go to declaration on any `T`, **Then** it reaches the function's own header.

---

### User Story 2 - Rename a template parameter (Priority: P1)

Renaming `T` to `TElement` in the header renames every use inside that template, and nothing outside it, including a different template's `T` in the same file.

**Why this priority**: rename is where a resolution gap does damage: today it can't be used on template parameters at all.

**Independent Test**: rename in a file holding two templates that both use `T`; only the chosen template changes and the file still compiles in MetaEditor.

**Acceptance Scenarios**:

1. **Given** two templates both using `T`, **When** the first template's `T` is renamed, **Then** the second template is unchanged.
2. **Given** an out-of-line member definition of a template class (`template<typename T> T CList::At(int i) { ... }`), **When** go to declaration on `T` inside it, **Then** it reaches that definition's own header.

---

### User Story 3 - Precise undeclared-name checks (Priority: P2)

A name like `T` used outside any template is reported as undeclared again (as MetaEditor does), because template parameters are now scoped to their template instead of matched anywhere in the file.

**Why this priority**: removes a known blind spot of the workaround, but real code rarely has this error.

**Independent Test**: a file with a template using `T` plus a plain function that uses an undeclared `T`: only the plain function's `T` is flagged; MetaEditor agrees.

**Acceptance Scenarios**:

1. **Given** a `T` outside any template, **When** inspections run, **Then** it is reported as undeclared.
2. **Given** MetaQuotes' Standard Library, **When** the corpus gate runs, **Then** undeclared-name errors stay at 0.

### Edge Cases

- `template <typename T>` with a space, and `class` instead of `typename` in the header.
- Several parameters (`TKey,typename TValue`), and parameters used as template arguments (`CKeyValuePair<TKey,TValue>`), arrays (`T &arr[]`), pointers (`T*`) and casts (`(T)x`).
- A member function template inside a class template, each with its own parameter names, including one that reuses an outer name.
- A template parameter named like a class elsewhere in the project (`T` vs a project class `T`): inside the template the parameter wins.
- A template parameter used inside a `#define` body or a macro argument: not resolved (macro bodies stay out of scope, as today).
- Code that is mid-edit (`template<typename` with nothing after it) must not break parsing of the rest of the file.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Each parameter in a template header MUST be a named declaration that go to declaration, Find Usages, rename and highlighting can target.
- **FR-002**: A use of a template parameter's name inside the declaration the header introduces (a class or struct and its members, a function, or an out-of-line member definition) MUST resolve to that header's parameter.
- **FR-003**: Inside a template, its parameter MUST take precedence over any same-named class, typedef, global or `#define` elsewhere.
- **FR-004**: Uses outside the template MUST NOT resolve to its parameters.
- **FR-005**: Renaming a template parameter MUST change exactly its uses inside its template.
- **FR-006**: The undeclared-name checks MUST rely on template scope instead of matching the name anywhere in the file, so a parameter's name outside any template is reported as undeclared, as MetaEditor does.
- **FR-007**: The corpus gate MUST show 0 parse errors and 0 false undeclared errors after the change, and resolved references MUST NOT drop for any name that resolves today.
- **FR-008**: Incomplete template headers while typing MUST NOT produce parse errors beyond the header itself.

### Key Entities

- **Template parameter**: a name introduced by a template header, scoped to the declaration that follows the header.
- **Template scope**: the class/struct (with its member bodies, in-class and out-of-line) or function that a header introduces.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the corpus gate, unresolved uses of template-parameter names in MetaQuotes' Standard Library drop by at least 1,000 (from about 1,150).
- **SC-002**: The corpus gate's resolved-reference count rises and no previously resolved reference is lost; parse errors and false undeclared errors stay at 0.
- **SC-003**: Go to declaration, Find Usages and rename work on template parameters in every acceptance scenario, verified by tests and once live in CLion.
- **SC-004**: All existing tests still pass.

## Assumptions

- Only template *parameters* are in scope. Members reached through a template-typed variable (`vertices[i].normal` where `vertices` is `TVertex&[]`) and members of an instantiated template (`CStack<double> s; s.Push(...)`) are later features; they depend on this one.
- `template<typename T>` and `template<class T>` are the forms MetaEditor accepts; non-type template parameters (`template<int N>`) are handled if MetaEditor accepts them, otherwise left as today.
- The stub schema version is bumped if the change adds stubbed elements (constitution).
- Measured by the existing corpus gate, so this feature doesn't wait on the 001 harness.
