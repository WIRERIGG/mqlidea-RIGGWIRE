<div align="center">

<img src="src/main/resources/META-INF/pluginIcon.svg" width="104" alt="RIGGWIRE MQL" />

# RIGGWIRE MQL

**MQL4/MQL5 language support for IntelliJ IDEA & CLion — with inline MetaEditor compiler diagnostics.**

![Version](https://img.shields.io/badge/version-2026.1.10-2381C4?style=flat-square)
![IntelliJ Platform](https://img.shields.io/badge/IntelliJ%20Platform-2025.3.2%2B-000000?style=flat-square&logo=intellijidea&logoColor=white)
![Java](https://img.shields.io/badge/Java-21-E5393B?style=flat-square&logo=openjdk&logoColor=white)
![Inspections](https://img.shields.io/badge/inspections-84-3ddc84?style=flat-square)
![Tests](https://img.shields.io/badge/tests-663%20passing-3ddc84?style=flat-square)
![License](https://img.shields.io/badge/license-GPL--3.0-777777?style=flat-square)

</div>

> Focused on one thing: **catching MQL mistakes early** — from the lexer, from static inspections, and from the real MetaEditor compiler — directly in the editor. A check that can't be sure stays quiet rather than guessing.

Plugin id: `io.riggwire.mql`

|  |  |
| :-- | :-- |
| 🛡️ **84 inspections** (83 per-file + 1 cross-file) — 57 on by default, 4 quick-fixes | ✍️ **Member-aware rename** & Find Usages across the `#include` closure |
| 🔎 **Real resolution** — members, base classes, namespaces, macros, typedefs, 7 stub indexes | ⚙️ **MetaEditor compile** inline, headers included — macOS · Windows · Linux |
| 📈 **MetaTrader workflow** — backtest run configs, `.set` checks, drift warnings | 🎨 **Completion · formatter · folding · templates · structure view** |

---

## ✨ Features

### 🧩 Language support

- **Three file types** — `MQL4 File` (`.mq4`, `.mql4`), `MQL5 File` (`.mq5`, `.mql5`), and `MQL Header` (`.mqh`) — each with its own icon
- JFlex lexer and hand-written parser with error recovery — a syntax error does not break highlighting or navigation for the rest of the file
- The MQL5 language as MetaEditor accepts it: classes, structs and **unions**, `pack(n)`, interfaces, operator methods, **namespaces**, `typedef` function pointers, templates, `input group`, `export`, `#`/`##` in macros, `unsigned int` (and `unsigned char/short/long`), `D'…'` datetime and `C'…'` color literals, `\x` escapes, and the `vector`/`matrix`/`complex` types
- Dialect awareness (`MqlDialect`): files are classified as MQL4 or MQL5 (a `.mqh` header inherits its project's dialect), and dialect-specific completion and inspections only apply where they belong
- Syntax highlighting with a configurable **Color Settings** page, plus a semantic annotator for event handlers (`OnInit`, `OnTick`, …), `input` parameters and MetaEditor's own literal errors (out-of-range character codes, MQL5 `extern` initializers)
- Read-vs-write identifier highlighting and a bundled MQL/MetaTrader spellchecking dictionary
- Structure view and breadcrumbs for classes, functions, enums, namespaces and input groups
- `#region`/`#endregion` and consecutive-`#include` folding; native TODO recognition
- Gutter icons marking MT5 entry points and a ▶ run marker (one-click compile)
- **New → MQL5 Expert Advisor / Indicator / Script** and **MQL4 Expert** from templates pre-filled with `#property` blocks and event-handler skeletons

### 🛡️ Error detection

- **83 local inspections** in 13 groups — Trading Safety (14), Advanced Patterns, Performance, Control Flow, Memory & Allocation, Function Signature, Class Structure, Security & Data, Code Complexity, Trading-Specific, Naming & Style, Type Safety, and Preprocessor
- **Trading Safety** covers unchecked `OrderSend()` results, unchecked or double-released indicator handles, missing `IndicatorRelease()`, MQL4 order-close loop direction, trade-context checks, unchecked `CopyRates`/`CopyBuffer`, `delete` without a null guard, and more
- **Indicator buffer contract**: `SetIndexBuffer`, `CopyBuffer` and `iCustom` buffer indexes checked against the indicator's declared buffers and plots (literal values)
- **Call to an undefined function**: MetaEditor's "undeclared identifier" (error 256), reported as you type; skipped when anything the file's `#include`s reach (or the programs that include it read) doesn't resolve or isn't MQL, such as a C++ `.h` header, so it never guesses. Calls through an `#import` module (`kernel32::GetLastError()`), names a `##` macro pastes together, and MQL4 functions inside `#ifdef __MQL4__` branches are understood
- **Undeclared names and members**: a variable or type nothing declares, and a member a type doesn't have, for your classes, built-in structures (`dt.hours` on `MqlDateTime`) and `vector`/`matrix`/`complex` (`v.Summ()`); a stray template parameter name outside its template is reported too
- A cross-file **global inspection**: unused global function across the entire `#include` closure
- Safety checks are on by default (57); style, naming and complexity checks are opt-in (26)
- **Quick-fixes** that always emit compilable code: wrap an unchecked `CopyRates`/`CopyBuffer`/`ArrayResize`/`OrderSend` in a failure check, add an `INVALID_HANDLE` guard after handle creation, release global indicator handles in `OnDeinit`, and nullify a pointer after `delete`
- **Suppression** in the editor and in batch **Inspect Code**: *Suppress for function* / *Suppress for file*, and per statement with `//noinspection <id>` on the line above or at the end of the line
- A background problems logger that writes a Markdown report of the current, profile-enabled findings for the open project (`mql-tasks.md`)
- **Tools → Generate MQL Inspection Catalog** — a triage document enumerating every inspection

### 🔎 Navigation and refactoring

- Go to declaration and Find Usages for functions, classes/structs/unions, enums and their constants, parameters, variables, `#define` macros and typedefs — across files reached via `#include`
- Member access is typed: `obj.field`, `obj.Method()`, base classes, `this`, chains, array elements (`rates[i].close`), call results (`Get().m`), casts (`((CFoo*)p).m`, `dynamic_cast`), and `operator[]`
- Scoped names: `::global`, `Class::member`, `Namespace::name`, and out-of-line `CFoo::Method` bodies that see the class's members
- Names resolve the way MetaEditor compiles: a file's own `#include` closure, then (for a header) the closures of the programs that include it. MetaTrader's `MQL5/Include` folder is indexed as a library, and your project's copy of a header always wins over a stale one there
- **Rename** (Shift-F6, in-place) updates call sites project-wide, including member accesses; **Go to Super**, **Go to Type Declaration**, **Extract Variable**, and **Safe Delete**
- `#include "X.mqh"` and `#include <Trade/Trade.mqh>` are navigable links
- **Seven stub indexes** — classes, functions, enums, enum constants, globals, typedefs and macros — for Go to Class, Go to Symbol and fast cross-file resolution

### ✍️ Editing and formatting

- Completion: dialect-filtered, with insert handlers for parentheses and arguments; members of your classes after `.`, `vector`/`matrix` methods, built-in structure fields (`MqlDateTime dt; dt.hour`), macros and typedefs
- Parameter info (Ctrl-P) with real signatures and inline **parameter-name hints** on positional calls
- Quick documentation (hover / Ctrl-Q) in English and Russian, including your own doc comments
- Code formatter with a MetaEditor-compatible default style (**Settings → Code Style → MQL4**)
- Brace matching, quote handling, folding, and line/block commenting
- 9 live templates (`oninit`, `ontick`, `ondeinit`, `ordersend`, `input`, `indicator`, `fileop`, `class`, `pool`)

### ⚙️ Compiler integration

- The real MetaEditor compiler runs in the background and its errors and warnings appear as inline squiggles
- **Headers too**: a `.mqh` is checked by compiling the nearest program that includes it. Its errors land on the header; the program gets a file-level warning naming any included file that fails; the status bar reads `MQL: N errors, M warnings (via X.mq5)`
- Each diagnostic goes to the file at the exact path MetaEditor printed, so same-named headers in another checkout or worktree never swap errors
- Results are cached by a stamp over the whole `#include` closure: editing any included file triggers a fresh compile, nothing else does
- **Compile Check Now** (Tools menu and editor popup) forces a compile, from a program or a header
- Background compiles pause while a Strategy Tester run is in progress
- **Cross-platform launchers** (`MqlCompilerService` uses the first available):
  - **macOS** — the `mt5` command at `~/.local/bin/mt5`, driving MetaEditor through MetaTrader 5's bundled Wine
  - **Windows** — native `metaeditor64.exe` (falling back to `metaeditor.exe`) from a registered MQL SDK
  - **Linux** — an explicit Wine binary + MetaEditor exe (`MQL_WINE_PATH` / `mql.wine.path`)
- A compile run configuration with clickable `file(line,col)` links in the console
- When no compiler is available the status bar says "compiler N/A" rather than showing a false clean state

### 📈 MetaTrader workflow

None of these ever stop MetaTrader or write into its folders.

- **Backtest run configuration** (Run → Edit Configurations → MQL Backtest): Expert, symbol, period, dates, tick model, deposit and an optional `.set` file, run through `mt5 backtest --no-kill`. It refuses to start while MetaTrader, a tester agent or another backtest is running, or when it can't tell; when it finishes, the notification offers to open the report
- **`.set` file check**: a `.set` file that names inputs the Expert doesn't declare gets an editor banner listing them; with several copies of the EA, the one matching MetaTrader's deployed tree is used
- **Drift warning**: when MetaTrader's deployed copy of an open source file differs from the repository's, a banner says so (paths mapped from `.claude/mt5-bridge.json`, the same mapping `mt5 sync` uses)

---

## 📋 Requirements

| | Requirement |
| :-- | :-- |
| **IDE** | IntelliJ IDEA or CLion 2025.3.2+ (build 253.30387+) |
| **Java** | 21 (JetBrains Runtime) — for running the IDE; the build auto-detects a JDK |
| **Compile checking** | MetaEditor — macOS via the `mt5` command + Wine · Windows via `metaeditor64.exe` (registered MQL SDK) · Linux via Wine |
| **Backtests, drift and `.set` checks** | The `mt5` command (macOS) |
| **File types** | `.mq4` `.mql4` `.mq5` `.mql5` `.mqh` |

Everything in the editor works with no external tools installed; only compile checking and the MetaTrader workflow need them.

---

## 📦 Installation

### From disk

1. Build the plugin (below) or download a release `.zip`
2. **Settings → Plugins → ⚙ → Install Plugin from Disk…**
3. Select the `.zip` and restart the IDE
4. If another MQL plugin (investflow.ru MQL Idea, Lime MQL Editing) is installed, uninstall it first

### Building from source

```bash
./gradlew build                  # compile (deprecations are errors) + all 663 tests
./gradlew buildPlugin            # produces build/distributions/*.zip
./gradlew verifyPlugin           # Plugin Verifier against 2025.3.2 and CLion 2026.3
./gradlew runIde                 # launch a sandbox IDE with the plugin installed
```

The Gradle daemon's JDK is auto-detected (`gradle/gradle-daemon-jvm.properties`); a CLion/IDEA bundled JBR or any JDK 21 works. If detection misses yours, set `JAVA_HOME` or `org.gradle.java.home` in `~/.gradle/gradle.properties`. Gradle 9 wrapper included; built with the IntelliJ Platform Gradle Plugin 2.11.0 against `intellijIdea("2025.3.2")`.

### Enabling compile checking

- **macOS** — the plugin runs `~/.local/bin/mt5` (it does not search `PATH`). `mt5` is a separate command-line bridge to MetaTrader 5's bundled Wine and is **not distributed with this plugin**. The plugin needs:
  - `mt5 compile <file>`: compiles a file anywhere on disk (a path outside the MetaTrader folder must reach MetaEditor as a `Z:\…` path, or MetaEditor silently compiles nothing); MetaEditor's log next to the source carries the diagnostics
  - `mt5 backtest …` (backtest run configuration only): runs the Strategy Tester and prints `Report: <path>`; exit codes 0 finished · 1 no report · 2 setup error · 3 timeout · 4 bad arguments · 5 MetaTrader already open · 6 gave up waiting for another backtest
- **Windows** — register an **MQL SDK** (Project Structure → SDKs → **+** → *MQL4 SDK*) pointing at the folder that contains `metaeditor64.exe`
- **Linux** — register the MQL SDK as above and make a Wine binary discoverable (`MQL_WINE_PATH`, `mql.wine.path`, or a standard install location)

Without any of these, every editor feature still works; only inline compiler diagnostics are unavailable.

---

## ✅ How quality is held

- **Corpus gate**: over MetaQuotes' Standard Library and examples (read from your local MetaTrader install, never copied into this repo), the plugin must report **0 parse errors and 0 false "undeclared" errors**, and no inspection's count may grow without a deliberate, committed baseline change
- **Plugin Verifier**: compatible with IntelliJ IDEA 2025.3.2 and CLion 2026.3, using no internal or experimental platform API
- **Hermetic tests**: the 693 unit tests never depend on the machine's MetaTrader install
- **MetaEditor is the referee**: language support and built-in name lists are checked by compiling probes in the real MetaEditor; no mql5.com documentation text is bundled
- **MetaEditor harness**: 234 MQL5 programs (14 open-source repositories, plus MetaQuotes' examples and one private EA read from the local install and never copied), their 335 otherwise-unreached headers, and 1,006 seeded mistakes are compiled in MetaEditor, and the plugin is scored against those verdicts. Its false errors, missed errors and caught mistakes per kind may not get worse. Today: 309 programs where both are clean, 7 where only the plugin reports an error, 86 where only MetaEditor does (mostly code that MetaEditor's newer compiler rejects for argument and struct-copy types). The plugin catches 90% of misspelt names and 93% of misspelt members; it does not yet catch a missing `;`, a wrong argument count or a type mismatch (see `specs/001-metaeditor-harness/findings.md`)

---

## 🔧 How the compiler integration works

When you stop typing (or run **Compile Check Now**), the annotator picks the file to compile: the file itself for a program, or the nearest including program for a header. `MqlCompilerService` asks each launcher — `Mt5CliLauncher` (macOS), `MetaEditorLauncher` (Windows), then `WineLauncher` (Linux) — for a command and uses the first available. MetaEditor writes a `<basename>.log` next to the source; the service deletes any old log first (so a compile that did nothing can't report a stale result), reads the new one as BOM-aware UTF-16, and parses each `file(line,col) : error|warning code : message` line. Each diagnostic is placed on the file at the path MetaEditor printed. Results are cached by a stamp over the whole include closure. If no launcher works, the status bar shows "compiler N/A".

---

## 🗺️ Known limitations

- **Inline compile checking on Windows and Linux is untested on real machines.** The launchers are wired in, but macOS is the only platform exercised day to day. Debugging is unsupported everywhere (MetaTrader has no public debug protocol).
- **Templates**: template parameters (`template<typename T>`) are declarations scoped to their template, with go to declaration, find usages and rename; members of an instantiated template type (`CStack<double> s; s.Push(…)`) and members reached through a template-typed variable don't resolve yet.
- **Built-in structure fields** (`dt.hour`) complete and are checked by name, but have no declaration to navigate to.
- **Quick documentation in MQL5 files** shows nothing for language keywords and preprocessor directives: the bundled language reference is the MQL4 one, and showing nothing beats showing MQL4 behaviour. Function and constant docs work in both dialects.
- **CLion's MCP `search_symbol`** never finds MQL symbols: CLion sends it to its C++ engine, and the only hook is internal API this plugin won't use. Goto Symbol in the IDE works.
- **Quick-fixes** cover the four Trading Safety remediations above; more are planned.

> **Note** — earlier versions shipped an experimental AI "code healing" pipeline. It was removed in the 2026.1.0 revamp and is not part of this plugin. The AI-free **Generate MQL Inspection Catalog** action is its only surviving artifact.

---

## 🗂️ Project structure

```
src/main/java/com/limemojito/oss/mql/
├── action/           New-file actions (Expert / Indicator / Script)
├── parser/           Lexer (JFlex) + parser with error recovery
├── psi/              PSI elements + stubs (7 indexes)
├── editor/           Highlighting, completion, parameter info, formatter, folding, templates
├── inspection/       83 local inspections + 1 global inspection + quick-fixes + problems logger
├── compiler/         Annotator, MetaEditor/mt5/Wine launchers, status bar, Strategy Tester detection
├── reference/        Reference resolution, member/type resolution, #include navigation
├── findusages/       Find Usages provider
├── refactoring/      Rename, Extract Variable, Safe Delete
├── index/            Goto Class / Goto Symbol contributors
├── structure/        Structure view, breadcrumbs, Go to Super
├── runconfig/        Compile and backtest run configurations
├── tester/           .set file reading and input checks
├── deploy/           MetaTrader drift detection (read-only)
├── sdk/              MQL SDK type (locates metaeditor64.exe)
├── settings/         Plugin settings + configurable panel
├── doc/              Quick documentation (EN + RU)
└── catalog/          Inspection catalog generator

src/main/resources/
├── META-INF/plugin.xml          All extension registrations
├── inspectionDescriptions/      HTML descriptions per inspection
├── liveTemplates/               9 MQL live templates
└── mql/                         Bundled MQL documentation + JSON catalogs (API names only)
```

~300 Java source files; the **663 tests** cover the parser, resolution, inspections, quick-fixes, refactoring, editor extensions, compiler-output parsing, the MetaTrader workflow and log decoding.

---

## 📄 License

GPL-3.0 — see [LICENSE.txt](LICENSE.txt).

**RIGGWIRE MQL** is maintained by [RIGGWIRE Trading Systems](https://github.com/WIRERIGG). It is a fork of the [Lime MQL Editing](https://github.com/LimeMojito/mqlidea) plugin by [Lime Mojito Pty Ltd](https://limemojito.com/), itself forked from the [InvestFlow MQL Idea](https://github.com/investflow/mqlidea) plugin. All original copyright notices are retained per GPL-3.0; the original authors do not endorse this fork.

**Found a bug or have a feature request?** [Open an issue](https://github.com/WIRERIGG/mqlidea-RIGGWIRE/issues)
