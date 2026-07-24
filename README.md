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

- Dedicated file types for `.mq4`, `.mql4`, `.mq5`, `.mql5`, and `.mqh`, each with its own icon
- JFlex lexer and hand-written parser with error recovery — a syntax error does not break highlighting or navigation for the rest of the file
- Dialect awareness (`MqlDialect`): files are classified as MQL4 or MQL5, and dialect-specific features (completion, inspections) only apply where they belong
- Syntax highlighting plus a semantic annotator that recognizes event handlers (`OnInit`, `OnTick`, …) and `input` parameters
- Structure view for classes, functions, and enums
- New File actions for MQL4 and MQL5 sources

### Error detection

- **80 local inspections** across 13 categories, including a **Trading Safety** group (unchecked `OrderSend()` results, unchecked indicator handles, missing `IndicatorRelease()`, MQL4 order-close loop direction, trade-context checks, and more)
- Dialect-filtered: MQL5-only checks (indicator handles, `OnCalculate()`) stay off `.mq4` files and vice versa
- Safety-focused checks are enabled by default; style and complexity checks are opt-in
- A background problems logger that writes a structured report of current findings, plus a **Tools → Generate MQL Inspection Catalog** action that produces an AI-free triage document (`docs/MQL_INSPECTION_CATALOG.md`)

### Navigation and refactoring

- Real reference resolution: go-to-declaration (Ctrl-click) and Find Usages for functions, classes/structs, enums, enum constants, parameters, and variables — local, global, and member — including across files reached via `#include`
- Rename refactoring (Shift-F6, in-place) for the same symbol kinds, updating call sites project-wide
- `#include "X.mqh"` and `#include <Trade/Trade.mqh>` are navigable links; the include closure is computed with cycle protection
- Stub indexes for classes and functions powering Go to Class and Go to Symbol

### Editing and formatting

- Code completion: tiered, dialect-filtered, with insert handlers for parentheses and arguments
- Parameter info (Ctrl-P) with real signatures for built-in and project functions
- Quick documentation (hover / Ctrl-Q) in English and Russian, including your own doc comments
- Code formatter with a configurable, MetaEditor-compatible default style (**Settings → Code Style → MQL4**)
- Brace matching, code folding, and line/block commenting
- 9 live templates for common trading patterns (`oninit`, `ontick`, `ordersend`, `indicator`, `pool`, …)

### Compiler integration

- An **ExternalAnnotator** runs the real MetaEditor compiler and shows genuine compile errors and warnings as inline editor squiggles
- A **Compile Check Now** action (Tools menu and editor popup) forces a fresh compile on demand
- A status-bar widget shows the current compile state of the open file
- Results are memoized by document modification stamp, so unchanged files are not recompiled
- When no compiler is available, the plugin degrades honestly: the widget reports "compiler N/A" rather than pretending the file is clean
- A run configuration and program runner for invoking the MQL compiler as a build step

---

## Requirements

| | Requirement |
| :-- | :-- |
| **IDE** | IntelliJ IDEA or CLion 2025.3.2+ (build 253.30387+) |
| **Java** | 21 (JetBrains Runtime) |
| **Compile checking** | MetaEditor — on macOS via the `mt5` wrapper script and Wine; other platforms need a reachable `metaeditor64.exe` |
| **File types** | `.mq4` `.mql4` `.mq5` `.mql5` `.mqh` |

Everything except compile checking works with no external tools installed. Inline compiler diagnostics currently target macOS (MetaTrader under Wine, driven by the `mt5` CLI wrapper); Windows/Linux support is planned.

---

## Installation

### From disk

1. Build the plugin (below) or download a release `.zip`
2. **Settings → Plugins → ⚙ → Install Plugin from Disk…**
3. Select the `.zip` and restart the IDE
4. If another MQL plugin (investflow.ru MQL Idea, Lime MQL Editing) is installed, uninstall it first

### Building from source

```bash
# Requires JAVA_HOME pointing at a JDK/JBR 21+ (bytecode targets release 21)
./gradlew buildPlugin            # produces build/distributions/*.zip
./gradlew test                   # run the test suite
./gradlew runIde                 # launch a sandbox IDE with the plugin installed
```

Gradle 9 wrapper included; built with the IntelliJ Platform Gradle Plugin 2.11.0 against `intellijIdea("2025.3.2")`.

### Enabling compile checking (macOS)

Install the `mt5` bridge (a CLI wrapper that drives MetaEditor through Wine) and make sure `mt5` is on your `PATH`. The plugin shells out to it automatically; no further configuration is needed. Without it, all editor features still work — only inline compiler diagnostics are unavailable.

---

## How the compiler integration works

When you stop typing (or trigger **Compile Check Now**), the ExternalAnnotator hands the current file to `MqlCompilerService`, which picks a launcher: the `mt5` CLI wrapper (macOS/Wine) or a direct MetaEditor invocation. The compiler's log output is parsed into line-accurate diagnostics and rendered as standard editor annotations. Results are cached per document modification stamp, so the compiler only runs when the file has actually changed. If no launcher succeeds, the status-bar widget reports "compiler N/A" instead of showing a false green state.

---

## Roadmap

Known limitations, tracked as upcoming work:

- **Quick-fixes cover ~10 of 80 inspections** — property/doc-comment/empty-body/delete-nullify fixes ship today; the **Trading Safety** group reports problems without automated remediation yet (planned: wrap-in-check and insert-release fixes)
- **Inspection suppression is editor-only** — `// noinspection`-style comments plus Suppress-for-function / Suppress-for-file intentions work in the editor, but batch **Inspect Code** results and statement/line-level scope are not yet supported
- **Member-access rename/completion gap** — because `obj.field` / `obj.Method()` are not type-resolved, renaming a member does not rewrite its call sites and dot-completion only knows bundled StdLib types (project-defined types need type inference, planned)
- **Header (`.mqh`) compile errors are not yet surfaced** — the compiler integration currently reports diagnostics for the compiled `.mq4`/`.mq5` file only
- **Inline compiler diagnostics on Windows/Linux**, plus debugging support
- **Member access resolution** (`obj.field` / `obj.Method()`) requires type inference and is planned for a later phase
- Safe-delete refactoring

Note: earlier versions shipped an experimental AI "code healing" pipeline. It was removed in the 2026.1.0 revamp and is not part of this plugin. The AI-free **Generate MQL Inspection Catalog** action is its only surviving artifact.

---

## Project structure

```
src/main/java/com/limemojito/oss/mql/
├── parser/           Lexer (JFlex) + parser with error recovery
├── psi/              PSI elements + stubs (stub indexes for classes/functions)
├── editor/           Highlighting, completion, parameter info, formatter, folding, templates
├── inspection/       80 local inspections + problems logger
├── compiler/         ExternalAnnotator, MetaEditor/mt5/Wine launchers, status-bar widget
├── reference/        Reference resolution + #include navigation
├── findusages/       Find Usages provider
├── refactoring/      Rename support
├── index/            Goto Class / Goto Symbol contributors
├── structure/        Structure view
├── runconfig/        Run configuration + compiler runner
├── settings/         Plugin settings + configurable panel
├── doc/              Quick documentation (EN + RU)
└── catalog/          AI-free inspection catalog generator

src/main/resources/
├── META-INF/plugin.xml          All extension registrations
├── inspectionDescriptions/      HTML descriptions per inspection
├── liveTemplates/               9 MQL live templates
└── mql/doc/                     Bundled MQL documentation + JSON catalogs
```

~231 Java source files; the test suite (246 tests) covers the parser, resolution, inspections, and compiler-output parsing.

---

## License

GPL-3.0 — see [LICENSE.txt](LICENSE.txt).

**RIGGWIRE MQL** is maintained by [RIGGWIRE Trading Systems](https://github.com/WIRERIGG). It is a fork of the [Lime MQL Editing](https://github.com/LimeMojito/mqlidea) plugin by [Lime Mojito Pty Ltd](https://limemojito.com/), itself forked from the [InvestFlow MQL Idea](https://github.com/investflow/mqlidea) plugin. All original copyright notices are retained per GPL-3.0; the original authors do not endorse this fork.

**Found a bug or have a feature request?** [Open an issue](https://github.com/WIRERIGG/mqlidea/issues)
