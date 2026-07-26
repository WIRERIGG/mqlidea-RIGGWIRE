# mqlidea-RIGGWIRE — Project Instructions

## What This Is

An IntelliJ Platform plugin (`io.riggwire.mql`, v2026.1.0) providing MQL4/MQL5 language support for MetaTrader trading development in IntelliJ IDEA and CLion. It focuses on being honest and genuinely helpful for real MQL projects: early, inline detection of syntactic/semantic errors, and full IDE assistance (navigation, refactoring, completion, docs, formatting) plus a compiler-backed error annotator.

> The former **AI Code Healing** subsystem (Grok analysis + Claude diff apply, SQLite DB, healing tool window, gutter markers, pre-commit prompts) was **removed in the 2026.1.0 revamp**. Only the AI-free "Generate MQL Inspection Catalog" action (`catalog/`) survives. Do not re-add healing.

## Build

```bash
# macOS: use the CLion (or IntelliJ) bundled JBR 21 as JAVA_HOME
export JAVA_HOME=/Applications/CLion.app/Contents/jbr/Contents/Home
./gradlew build          # compile + test + verify
./gradlew test           # tests only (246 pass)
./gradlew buildPlugin     # produces build/distributions/mqlidea-<version>.zip
```

- Java 21 (JetBrains Runtime), Gradle 9.3 via wrapper, IntelliJ Platform Gradle Plugin 2.11.0.
- Target IDE: IntelliJ IDEA / CLion **2025.3.2+** (since-build 253.30387).
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
- All existing tests must pass after changes (`./gradlew test` — 253). Delete only tests covering deliberately-removed features.
- Source is **Java 21** (not Kotlin). Both MQL4 and MQL5 use `language="MQL4"` in plugin.xml.
- Stub schema version is **22** — increment when changing stub structure.
- Respect the platform threading model: PSI/index access under read actions; long work off the EDT; actions override `getActionUpdateThread()`; index-backed extensions guard for dumb mode and call `ProgressManager.checkCanceled()`.
- Never swallow `ProcessCanceledException` (it extends `RuntimeException`) — always let it propagate.
- Run `./gradlew build` to verify after every change.

## Known Limitations / Roadmap

(from the 2026 architecture review — being worked through)
- Quick-fixes cover a growing subset; the Trading Safety group now has three (wrap unchecked `CopyRates`/`CopyBuffer`/`ArrayResize` in a `< 0` check via `WrapCallInFailureCheckFix`; `INVALID_HANDLE` guard via `CheckHandleAfterCreationFix`). More flagship checks (UncheckedOrderSend, MissingIndicatorRelease) still report-only.
- Inspection suppression is wired (comment + Suppress-for-function/file intentions via `MQL5SafetyInspectionBase` → `CustomSuppressableInspectionTool`) but editor-only: no batch **Inspect Code** suppression and no statement/line-level scope; built on pre-2016 deprecated API.
- Member-access (`obj.field`/`obj.Method()`) is not type-resolved, so rename silently misses those call sites and dot-completion only covers bundled StdLib types.
- Header (`.mqh`) compile errors from the ExternalAnnotator are not yet surfaced.
- Compile-checking is currently macOS/Wine via the `mt5` wrapper.
- A few deprecated platform APIs remain (`StartupActivity`→`ProjectActivity`, `SuppressIntentionAction`, `MQL5TemplateContextType` ctor).

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
