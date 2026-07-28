<img src="src/main/resources/META-INF/pluginIcon.svg" width="96" alt="RIGGWIRE MQL" />

# RIGGWIRE MQL

MQL4/MQL5 language support for IntelliJ IDEA and CLion, with inline MetaEditor compiler diagnostics.

![Version](https://img.shields.io/badge/version-2026.1.0-2381C4?style=flat-square)
![IntelliJ Platform](https://img.shields.io/badge/IntelliJ%20Platform-2025.3.2%2B-000000?style=flat-square&logo=intellijidea&logoColor=white)
![Java](https://img.shields.io/badge/Java-21-E5393B?style=flat-square&logo=openjdk&logoColor=white)
![License](https://img.shields.io/badge/license-GPL--3.0-777777?style=flat-square)

Plugin id: `io.riggwire.mql`. The plugin is focused on one thing: catching MQL mistakes early — from the lexer, from static inspections, and from the real MetaEditor compiler — directly in the editor.

---

## Features

### Language support

- **Three file types** — `MQL4 File` (`.mq4`, `.mql4`), `MQL5 File` (`.mq5`, `.mql5`), and `MQL Header` (`.mqh`) — each with its own icon, resolved from the view provider so the icon never flickers before settling
- JFlex lexer and hand-written parser with error recovery — a syntax error does not break highlighting or navigation for the rest of the file
- Dialect awareness (`MqlDialect`): files are classified as MQL4 or MQL5 (a `.mqh` header inherits its project's dialect), and dialect-specific features — completion, inspections — only apply where they belong
- Syntax highlighting with a configurable **Color Settings** page, plus a semantic annotator that recognizes event handlers (`OnInit`, `OnTick`, …) and `input` parameters
- Read-vs-write identifier highlighting (`ReadWriteAccessDetector`) and a bundled MQL/MetaTrader spellchecking dictionary
- Structure view and breadcrumbs (`CClass ▸ Method`) for classes, functions, and enums
- `#region`/`#endregion` and consecutive-`#include` folding; native TODO recognition (`IndexPatternBuilder`)
- Gutter icons marking MT5 entry points (`OnInit`/`OnTick`/…) and a ▶ run marker (one-click compile)
- **New → MQL5 Expert Advisor / Indicator / Script** and **MQL4 Expert** from templates pre-filled with `#property` blocks and event-handler skeletons

### Error detection

- **80 local inspections** across 13 categories — Trading Safety, Advanced Patterns, Performance, Memory & Allocation, Function Signature, Control Flow, Class Structure, Security & Data, Code Complexity, Trading-Specific, Naming & Style, Type Safety, and Preprocessor
- The **Trading Safety** group (13 checks) covers unchecked `OrderSend()` results, unchecked / double-released indicator handles, missing `IndicatorRelease()`, MQL4 order-close loop direction, trade-context checks, unchecked `CopyRates`/`CopyBuffer`, `delete` without a null guard, and more
- A cross-file **global inspection**: unused global function across the entire `#include` closure
- Dialect-filtered: MQL5-only checks (indicator handles, `OnCalculate()`) stay off `.mq4` files and vice versa
- Safety-focused checks are enabled by default; style, naming, and complexity checks are opt-in (`enabledByDefault="false"`)
- **Trading Safety quick-fixes**: wrap an unchecked `CopyRates`/`CopyBuffer`/`ArrayResize` in a `< 0` failure check, add an `INVALID_HANDLE` guard after handle creation, and nullify a pointer after `delete` — all pure document-text rewrites that always emit compilable code
- Suppression that works both in the editor and in batch **Inspect Code** — modern `SuppressQuickFix` API adds *Suppress for function* / *Suppress for file* (`//noinspection <id>` comment markers), plus Alt-Enter previews so you see the exact edit before applying it
- A background problems logger (`MqlProblemsLoggerService`) that writes a structured Markdown/log report of the current, *profile-enabled* findings for the open project, refreshed on file events
- **Tools → Generate MQL Inspection Catalog** — an AI-free triage document (`docs/MQL_INSPECTION_CATALOG.md`) enumerating every inspection

### Navigation and refactoring

- Real reference resolution: go-to-declaration (Ctrl-click) and Find Usages for functions, classes/structs, enums, enum constants, parameters, and variables — local, global, and member (`obj.field` / `obj.Method()`, including through base classes) — across files reached via `#include`
- Rename refactoring (Shift-F6, in-place) for the same symbol kinds, updating call sites project-wide **including member accesses**
- **Go to Super**, **Go to Type Declaration**, **Extract Variable**, and **Safe Delete** (blocked when the symbol is still used, via the member-aware usage search)
- `#include "X.mqh"` and `#include <Trade/Trade.mqh>` are navigable links; the include closure is computed with cycle protection and cached per file so it isn't rebuilt on every keystroke
- **Four stub indexes** — classes, functions, enum types, and top-level global variables — powering Go to Class, Go to Symbol, and fast cross-file resolution without re-parsing every included file

### Editing and formatting

- Code completion: tiered, dialect-filtered, with insert handlers for parentheses and arguments — including members of project-defined classes after `.`
- Parameter info (Ctrl-P) with real signatures for built-in and project functions, and inline **parameter-name hints** on positional calls (`OrderSend(sym, /*cmd:*/ OP_BUY, /*volume:*/ 0.1, …)`)
- Quick documentation (hover / Ctrl-Q) in English and Russian, including your own doc comments
- Code formatter with a configurable, MetaEditor-compatible default style (**Settings → Code Style → MQL4**)
- Brace matching, quote handling, code folding, and line/block commenting
- 9 live templates for common trading patterns (`oninit`, `ontick`, `ondeinit`, `ordersend`, `input`, `indicator`, `fileop`, `class`, `pool`)

### Compiler integration

- An **ExternalAnnotator** runs the real MetaEditor compiler and shows genuine compile errors and warnings as inline editor squiggles
- **Cross-platform launcher strategy** (`MqlCompilerService` tries each in order and uses the first available):
  - **macOS** — the `mt5` CLI wrapper driving MetaEditor through MetaTrader 5's bundled Wine
  - **Windows** — native `metaeditor64.exe` (falling back to `metaeditor.exe`), no Wine, located via a registered MQL SDK
  - **Linux / other** — an explicit Wine binary + MetaEditor exe (`MQL_WINE_PATH` / `mql.wine.path`)
- A **Compile Check Now** action (Tools menu and editor popup) forces a fresh compile on demand
- A status-bar widget shows the current compile state of the open file
- Results are memoized by document modification stamp, so unchanged files are not recompiled; the stale log from a previous compile is cleared before each run so a no-op compile can never report a stale result
- Compile logs are decoded as UTF-16 (little-endian, BOM-aware) exactly as MetaEditor emits them
- An **MQL SDK type** (Project Structure → SDKs) points the Windows/Linux launchers at your MetaEditor install
- A **run configuration** and **program runner** for invoking the MQL compiler as a build step, with clickable `file(line,col)` hyperlinks in the run console
- When no compiler is available, the plugin degrades honestly: the widget reports "compiler N/A" rather than pretending the file is clean

---

## Requirements

| | Requirement |
| :-- | :-- |
| **IDE** | IntelliJ IDEA or CLion 2025.3.2+ (build 253.30387+) |
| **Java** | 21 (JetBrains Runtime) — for running the IDE; the build auto-detects a JDK (see below) |
| **Compile checking** | MetaEditor, reached per-platform: macOS via the `mt5` wrapper + Wine · Windows via native `metaeditor64.exe` (registered MQL SDK) · Linux via an explicit Wine binary + exe |
| **File types** | `.mq4` `.mql4` `.mq5` `.mql5` `.mqh` |

Everything except compile checking works with no external tools installed. **Compile checking is supported on macOS, Windows, and Linux.** Windows and Linux support is inherited from the upstream plugin (which shipped native `metaeditor64.exe` / Wine compilation via the Run configuration) and extended here — refactored into the launcher strategy, wired into the inline annotator, and fixed for MQL5 (`.mq5`) sources.

---

## Installation

### From disk

1. Build the plugin (below) or download a release `.zip`
2. **Settings → Plugins → ⚙ → Install Plugin from Disk…**
3. Select the `.zip` and restart the IDE
4. If another MQL plugin (investflow.ru MQL Idea, Lime MQL Editing) is installed, uninstall it first

### Building from source

```bash
./gradlew buildPlugin            # produces build/distributions/*.zip
./gradlew test                   # run the test suite (421 tests)
./gradlew runIde                 # launch a sandbox IDE with the plugin installed
```

The build daemon's JDK is chosen by auto-detection via `gradle/gradle-daemon-jvm.properties` (no hardcoded absolute path), so `gradlew`/`gradlew.bat` work on macOS, Windows, and Linux as long as a JDK of that major version is installed and discoverable (a CLion/IDEA bundled JBR or any Temurin/JDK counts). If detection misses your JDK, set `JAVA_HOME` or add `org.gradle.java.home=<path>` to your user-level `~/.gradle/gradle.properties`. Compilation targets Java 21 bytecode via `javac --release 21`.

Gradle 9 wrapper included; built with the IntelliJ Platform Gradle Plugin 2.11.0 against `intellijIdea("2025.3.2")`.

### Enabling compile checking

- **macOS** — install the `mt5` bridge (a CLI wrapper that drives MetaEditor through Wine) and make sure `mt5` is on your `PATH`. The plugin shells out to it automatically; no further configuration is needed.
- **Windows** — register an **MQL SDK** (Project Structure → SDKs → **+** → *MQL4 SDK*) pointing at the folder that contains `metaeditor64.exe`. The plugin discovers the exe from any configured MQL SDK.
- **Linux** — register the MQL SDK as above and make a Wine binary discoverable (`MQL_WINE_PATH`, `mql.wine.path`, or a standard install location).

Without any of these, all editor features still work — only inline compiler diagnostics are unavailable.

---

## How the compiler integration works

When you stop typing (or trigger **Compile Check Now**), the ExternalAnnotator hands the current file to `MqlCompilerService`, which asks each launcher — `Mt5CliLauncher` (macOS/Wine), `MetaEditorLauncher` (native Windows), then `WineLauncher` (Linux) — for a command and uses the first that reports itself available. MetaEditor writes a `<basename>.log` next to the source; the service deletes any prior log before launching (so a no-op compile can't feed back a stale result), reads the fresh one as BOM-aware UTF-16, and parses each `file(line,col) : error|warning code : message` line into a line-accurate diagnostic rendered as a standard editor annotation. Results are cached per document modification stamp, so the compiler only runs when the file has actually changed. If no launcher succeeds, the status-bar widget reports "compiler N/A" instead of showing a false green state.

---

## Roadmap

Known limitations, tracked as upcoming work:

- **Inline (ExternalAnnotator) compile diagnostics on Windows/Linux are freshly extended and not yet field-validated** — Windows/Linux compilation via the **Run configuration** is inherited from upstream (native `metaeditor64.exe` / Wine) and now also corrected for MQL5 (`.mq5`) sources; wiring those same launchers into the *inline* annotator is the new part, and macOS (`mt5`/Wine) remains the path exercised day-to-day, so a Windows/Linux inline smoke test is pending. Debugging is unsupported everywhere (no public MetaTrader debug protocol).
- **Header (`.mqh`) compile errors are not yet surfaced** — the compiler integration currently reports diagnostics for the compiled `.mq4`/`.mq5` file only
- **Trading Safety quick-fixes cover a subset** — more mechanical remediations planned for the flagship group
- **Member-access resolution is declared-type + bounded inheritance/chain**, not full expression type inference — function-return types, casts, templates and array-element types are out of scope, so member navigation/rename on those forms is not yet resolved

Note: earlier versions shipped an experimental AI "code healing" pipeline. It was removed in the 2026.1.0 revamp and is not part of this plugin. The AI-free **Generate MQL Inspection Catalog** action is its only surviving artifact.

---

## Project structure

```
src/main/java/com/limemojito/oss/mql/
├── action/           New-file actions (Expert / Indicator / Script)
├── parser/           Lexer (JFlex) + parser with error recovery
├── psi/              PSI elements + stubs (indexes for classes, functions, enums, globals)
├── editor/           Highlighting, completion, parameter info, formatter, folding, templates
├── inspection/       80 local inspections + 1 global inspection + problems logger
├── compiler/         ExternalAnnotator, MetaEditor/mt5/Wine launchers, status-bar widget
├── reference/        Reference resolution + member/type resolution + #include navigation
├── findusages/       Find Usages provider
├── refactoring/      Rename, Extract Variable, Safe Delete (refactoring support)
├── index/            Goto Class / Goto Symbol contributors + stub index keys
├── structure/        Structure view, breadcrumbs, Go to Super
├── runconfig/        Run configuration + compiler runner
├── sdk/              MQL SDK type (locates metaeditor64.exe)
├── settings/         Plugin settings + configurable panel
├── doc/              Quick documentation (EN + RU)
└── catalog/          AI-free inspection catalog generator

src/main/resources/
├── META-INF/plugin.xml          All extension registrations
├── inspectionDescriptions/      HTML descriptions per inspection
├── liveTemplates/               9 MQL live templates
└── mql/doc/                     Bundled MQL documentation + JSON catalogs
```

~261 Java source files; the test suite (**421 tests**) covers the parser, resolution (incl. member access), inspections, refactoring, editor extensions, compiler-output parsing, and log decoding.

---

## License

GPL-3.0 — see [LICENSE.txt](LICENSE.txt).

**RIGGWIRE MQL** is maintained by [RIGGWIRE Trading Systems](https://github.com/WIRERIGG). It is a fork of the [Lime MQL Editing](https://github.com/LimeMojito/mqlidea) plugin by [Lime Mojito Pty Ltd](https://limemojito.com/), itself forked from the [InvestFlow MQL Idea](https://github.com/investflow/mqlidea) plugin. All original copyright notices are retained per GPL-3.0; the original authors do not endorse this fork.

**Found a bug or have a feature request?** [Open an issue](https://github.com/WIRERIGG/mqlidea/issues)
