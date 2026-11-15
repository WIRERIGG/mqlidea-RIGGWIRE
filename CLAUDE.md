# mqlidea-RIGGWIRE — Project Instructions

## What This Is

An IntelliJ Platform plugin (`io.riggwire.mql`, v2026.1.5) providing MQL4/MQL5 language support for MetaTrader trading development in IntelliJ IDEA and CLion. It focuses on being honest and genuinely helpful for real MQL projects: early, inline detection of syntactic/semantic errors, and full IDE assistance (navigation, refactoring, completion, docs, formatting) plus a compiler-backed error annotator.

> The former **AI Code Healing** subsystem (Grok analysis + Claude diff apply, SQLite DB, healing tool window, gutter markers, pre-commit prompts) was **removed in the 2026.1.0 revamp**. Only the AI-free "Generate MQL Inspection Catalog" action (`catalog/`) survives. Do not re-add healing.

## Build

```bash
# macOS: use the CLion (or IntelliJ) bundled JBR 21 as JAVA_HOME
export JAVA_HOME=/Applications/CLion.app/Contents/jbr/Contents/Home
./gradlew build          # compile (-Werror on deprecation) + test
./gradlew verifyPlugin verifyPluginStructure   # NOT part of build; run before a release
./gradlew test           # tests only (586 pass)
./gradlew buildPlugin     # produces build/distributions/mqlidea-<version>.zip
tools/publish-local-repo.sh   # copies that zip to ~/.mqlidea-repo + writes updatePlugins.xml
tools/corpus-gate.sh          # ratchet over real MQL corpora (needs a local MetaTrader install)
tools/clion-mcp-check.py ~/CLionProjects/RIGGWIRE-EA-TC RIGGWIRE-EA-LIVE --expect N   # live check after an install
python3 tools/verify-structs.py OUT.mq5   # compile OUT.mq5 in MetaEditor: exactly 1 error (the bogus member)
```

### Gates: every measured gap stays closed
- **Unit tests are hermetic.** In unit-test mode `MqlIncludeRoots` ignores this machine's MetaTrader install; tests that need an Include folder create one (`MqlIncludeLibraryTest`, `MqlIncludeRoots.setTestRoots`).
- **Corpus gate** (`gate/CorpusGateTest`, a no-op in `./gradlew build`): parse errors, bad characters, resolved references, references to declared names that don't resolve, and every MQL inspection's count, over the MetaQuotes Standard Library and examples. It may not get worse than `src/test/resources/gate/corpus-baseline.properties`. After a deliberate change, `MQL_GATE_UPDATE=1 tools/corpus-gate.sh` and commit the new baseline with the change. The EA is measured as `report:ea` (never gated: another session edits it). No MetaQuotes code is copied into this repo.
- **Live check** after every install: `tools/clion-mcp-check.py` with `--expect` set to the last known count.
- **Catalog names** (`mql5-structs.json`, `mql5-vector-matrix.json`) are API names only, each verified by compiling in MetaEditor.

- Java 21 (JetBrains Runtime), Gradle 9.3 via wrapper, IntelliJ Platform Gradle Plugin 2.11.0.
- Target IDE: IntelliJ IDEA / CLion **2025.3.2+** (since-build 253.30387).
- Updates reach CLion through a local plugin repository: `file:///Users/shemarrigg/.mqlidea-repo/updatePlugins.xml` (Settings → Plugins → ⚙ → Manage Plugin Repositories). Bump `version` in build.gradle.kts **and** `<version>` in plugin.xml, `buildPlugin`, then run the publish script; CLion offers the update.
- The plugin only depends on `com.intellij.modules.lang`, so it loads in CLion as well as IDEA.

## Dependencies

| Library | Purpose |
|---------|---------|
| `com.google.code.gson:gson` | JSON parsing for the bundled MQL doc catalogs |

(No SQLite / OkHttp / AI-client dependencies — those left with the healing system.)

## Project Structure

```
src/main/java/com/limemojito/oss/mql/
├── MQL4Language / MQL4FileType / MQL5FileType / MQL4Icons   # language + file types
├── MqlDialect.java                     # MQL4 vs MQL5 resolution (.mqh inherits project dialect)
├── psi/ , psi/impl/ , psi/stub/        # PSI, element factory, stub elements + indexes
├── parser/                             # JFlex lexer + parser (with error recovery)
├── editor/                             # syntax highlighter, semantic annotator, color settings,
│                                       #   commenter, brace matcher, folding, formatter, completion,
│                                       #   parameter info
├── inspection/                         # ~80 local inspections (MQL5SafetyInspectionBase + StatementAst)
├── compiler/                           # ExternalAnnotator: mt5/Wine/MetaEditor launchers +
│                                       #   MqlCompilerService (inline compile errors, memoised)
├── reference/ , refactoring/ , findusages/   # resolve, rename, find usages, #include navigation
├── index/                              # goto-symbol / goto-class contributors
├── structure/                          # structure view
├── doc/                                # quick documentation (bundled MQL HTML catalogs)
├── runconfig/                          # run configuration + program runner (compile via mt5)
├── settings/                           # settings panel + persistent state
└── catalog/                            # Generate MQL Inspection Catalog action (AI-free)

src/main/resources/
├── META-INF/plugin.xml                 # ALL extension points registered here
├── icons/ , inspectionDescriptions/ , liveTemplates/ , mql/ (doc HTML + JSON catalogs)

src/test/                               # parser + inspection tests (219)
```

## Rules

- Be honest and genuinely helpful for real MQL4/MQL5 projects; detect errors early and inline. Prefer add/enhance over remove.
- All new extensions MUST be registered in `plugin.xml`; removing an extension means removing its registration too.
- All existing tests must pass after changes (`./gradlew test` — 586). Delete only tests covering deliberately-removed features.
- Source is **Java 21** (not Kotlin). Both MQL4 and MQL5 use `language="MQL4"` in plugin.xml.
- Stub schema version is **27** — increment when changing stub structure.
- Respect the platform threading model: PSI/index access under read actions; long work off the EDT; actions override `getActionUpdateThread()`; index-backed extensions guard for dumb mode and call `ProgressManager.checkCanceled()`.
- Never swallow `ProcessCanceledException` (it extends `RuntimeException`) — always let it propagate.
- Run `./gradlew build` to verify after every change.
- Platform API must exist, un-deprecated, on **both** 2025.3.2 (since-build) and the newest verified IDE (CLion 2026.3). javac runs with `-Xlint:deprecation -Xlint:removal -Werror`, so a deprecated call fails the build. The only allowed exception is an override the oldest platform still declares abstract; it carries an explained `@SuppressWarnings("deprecation")`. Check the verifier reports under `build/reports/pluginVerifier/` for experimental and internal API too. The whole `com.intellij.codeInsight.hints` package is experimental, so use `hints.declarative`.

## Known Limitations / Roadmap

(from the 2026 architecture review — being worked through)
- Quick-fixes cover a growing subset; the Trading Safety group now has three (wrap unchecked `CopyRates`/`CopyBuffer`/`ArrayResize` in a `< 0` check via `WrapCallInFailureCheckFix`; `INVALID_HANDLE` guard via `CheckHandleAfterCreationFix`). More flagship checks (UncheckedOrderSend, MissingIndicatorRelease) still report-only.
- Inspection suppression uses the modern `SuppressQuickFix` API (`MQL5SafetyInspectionBase.getBatchSuppressActions` → `MqlSuppressFix`), which is also a `LocalQuickFix` and so works in **both** the editor and batch **Inspect Code** (Suppress-for-function / Suppress-for-file via `//noinspection <id>`). Remaining gap: no statement/line-level scope.
- Member-access (`obj.field`/`obj.Method()`) **is** type-resolved (`reference/MqlTypeResolver`: declared-type / param / `this` / base-class / bounded chain / array element `a[i].m` / call return type `Get().m`), so rename, find-usages, and dot-completion cover project-defined classes. `::name`, `Class::member`, `Namespace::name`, out-of-line `X::Method` bodies, `offsetof(S, m)`, `#define` names and typedefs resolve too. `x[i]` on an object with `operator[]` takes that operator's return type. Forward declarations (`class CFoo;`) never stand in for the definition. Out of scope: casts and template instantiation (template parameter names are known, not their bound types).
- Names resolve the way MetaEditor compiles: a file's own `#include` closure, then (for a header) the closures of the `.mq5`/`.mq4` files that include it (`MqlResolveUtil.includerScopeFor`). The MetaTrader `MQL5/Include` and `MQL4/Include` folders are indexed as a library (`MqlIncludeLibraryProvider`). They often hold stale copies of project headers, so every project-wide lookup goes through `MqlScopes.projectFirst` (project wins; a library declaration never stands in for a documented built-in), dialect inference and the undeclared-name fallback use project scope only, and Goto Class/Symbol honour "include non-project items". Macro parameters still resolve to nothing, by design.
- CLion's MCP `search_symbol` never sees MQL symbols: CLion routes it to its C++ engine (`RadSymbolSearchEngine`), and the only hook (`SymbolSearchEngine`) is `@ApiStatus.Internal`. Platform limitation, not fixable within the rules above; agents use `search_text`/`search_regex`. IntelliJ IDEA has no such engine, so it falls back to Goto Symbol.
- Built-in structure members (`MqlDateTime dt; dt.hour`) complete and are checked by name (`StructCatalog`); they have no PSI, so they don't navigate.
- MetaQuotes' Standard Library and examples have no false undeclared-name errors (corpus gate holds them at 0); parse errors there are 0 too.
- Header (`.mqh`) compile errors from the ExternalAnnotator are not yet surfaced.
- Compile-checking runs on macOS (`mt5`/Wine), Windows (native `metaeditor64.exe` via a registered MQL SDK), and Linux (explicit Wine) through the `MqlCompilerService` launcher strategy; macOS is the actively-exercised path.
- Plugin Verifier: Compatible on IU 2025.3.2 and CL 2026.3, with no experimental or internal API. One deprecated usage is unavoidable: `MQL4SdkType.suggestHomePath()`, which is still abstract on 2025.3. `suggestHomePaths(Project)` is overridden alongside it, so SDK suggestions keep working after the platform removes it. Drop the override once since-build passes 253.

## Available Agents

| Agent | Purpose |
|-------|---------|
| `orchestrator` | Coordinates multi-domain changes |
| `plugin-developer` | IntelliJ plugin architecture and extensions |
| `mql5-specialist` | MQL5 language expertise and parser guidance |
| `code-quality` | Code inspections and quality rules |
| `build-resolver` | Gradle build and CI issues |
| `code-optimizer` | Runtime-performance optimization of plugin code |
| `safety-analyzer` | MQL trading-safety inspection analysis |
