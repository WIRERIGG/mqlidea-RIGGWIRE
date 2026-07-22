<div align="center">

<br/>

<img src="src/main/resources/META-INF/pluginIcon.svg" alt="RIGGWIRE MQL" width="96" />

<br/><br/>

# RIGGWIRE MQL

### Professional MQL4 &amp; MQL5 Language Support for IntelliJ IDEA — with AI Code Healing

*The most comprehensive MetaTrader development environment available inside a JetBrains IDE.*

<br/>

<img src="src/main/resources/icons/mql4.svg" alt="MQL4" width="40" />&nbsp;&nbsp;<img src="src/main/resources/icons/mql5.svg" alt="MQL5" width="40" />&nbsp;&nbsp;<img src="src/main/resources/icons/mqh.svg" alt="MQH" width="40" />&nbsp;&nbsp;<img src="src/main/resources/icons/mql_healing.svg" alt="AI Healing" width="40" />

<br/>

[**Features**](#features) &#8226; [**AI Healing**](#-ai-code-healing) &#8226; [**Inspections**](#-75-code-inspections) &#8226; [**Live Templates**](#-live-templates) &#8226; [**Install**](#-installation) &#8226; [**Build**](#-building-from-source) &#8226; [**License**](#-license)

<br/>

---

<br/>

<table>
<tr>
<td align="center"><h3>75</h3>Code Inspections</td>
<td align="center"><h3>1,300+</h3>Documented APIs</td>
<td align="center"><h3>9</h3>Live Templates</td>
<td align="center"><h3>12</h3>Safety Categories</td>
</tr>
</table>

<br/>

</div>

## Features

<table>
<tr>
<td width="50%" valign="top">

### Language Intelligence
- Syntax highlighting for `.mq4`, `.mq5`, `.mqh` files
- Inline documentation (Ctrl+Q) in English & Russian
- Code completion and navigation
- Structure view for classes, methods, enums
- Bracket matching and code folding
- Semantic error highlighting via annotator

</td>
<td width="50%" valign="top">

### File-Level Awareness
- Distinct icons per file type (MQL4, MQL5, MQH)
- **Gray icons** for files with problems -- instantly see which files need attention
- Icons restore to full color when all issues are resolved
- New File actions for MQL4 and MQL5

</td>
</tr>
<tr>
<td width="50%" valign="top">

### Background Analysis Engine
- Continuous scanning against all 75 inspections
- Incremental -- only re-scans modified files
- Batched read actions (5 files/lock) for zero UI lag
- Structured `mql-problems.log` report at project root
- Actionable fix hints for every finding

</td>
<td width="50%" valign="top">

### Optimized for Scale
- Regex pattern caching across 40+ inspections
- Zero `Pattern.compile()` on hot paths
- ConcurrentHashMap caches with lazy cleanup
- Low-priority daemon thread that never blocks the IDE

</td>
</tr>
</table>

<br/>

---

<br/>

## <img src="src/main/resources/icons/mql_healing.svg" width="22" height="22" align="top" alt="healing" /> AI Code Healing

Beyond *finding* problems, the plugin can *fix* them. An optional two-stage AI pipeline turns inspection findings into reviewable, one-click patches — entirely under your control.

<table>
<tr>
<td width="50%" valign="top">

### How it works
1. **Scan** — the background engine records every inspection finding in a local SQLite database (`.idea/mql-healing.db`)
2. **Analyze** — [**Grok**](https://x.ai) reviews each problem with MQL5 context and produces an insight
3. **Refactor** — [**Claude**](https://www.anthropic.com/claude) turns each insight into a unified-diff fix
4. **Apply** — you approve it; the diff is applied in a single undoable `WriteCommandAction`

</td>
<td width="50%" valign="top">

### Where fixes surface
- **Alt+Enter** intentions — *"Apply AI fix"* right at the problem
- **Gutter icons** on any file that has a pending fix
- **AI Healing tool window** — review and apply the full queue
- **Pre-commit prompt** — get reminded of pending fixes before you commit
- Every patch is **reviewable and undoable** — nothing changes without your say-so

</td>
</tr>
</table>

<br/>

| Setting | Default | Purpose |
|:--|:--|:--|
| **Auto-heal** | `off` | Master switch for automatic healing cycles |
| **Healing interval** | `5 min` | Time between background analysis cycles |
| **Grok model** | `grok-2` | Model used for problem analysis |
| **Claude model** | `claude-sonnet-4-5` | Model used to generate diffs |
| **API keys** | — | Stored in IntelliJ **PasswordSafe**, never on disk or in settings |

> Healing is **opt-in and off by default**. Bring your own Grok and Claude API keys; all analysis data stays in your project's local database.

<br/>

---

<br/>

## <img src="https://img.shields.io/badge/75-inspections-blue?style=flat-square" alt="75 inspections" /> 75 Code Inspections

Real-time analysis across 12 categories, catching bugs before they cost you money.

<br/>

<details>
<summary><b>Trading Safety</b> &mdash; 9 inspections &nbsp;&nbsp;<code>Catch order failures before they go live</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Unchecked OrderSend() result** | `OrderSend()` without checking return value |
| **Unchecked indicator handle** | Handle creation without `INVALID_HANDLE` check |
| **Missing IndicatorRelease()** | Forgetting `IndicatorRelease(handle)` in `OnDeinit()` |
| **Array access without size check** | Array indexing without `ArraySize()` guard |
| **Missing input parameter validation** | `OnInit()` without parameter range checks |
| **FileOpen() without FileClose()** | File handles left open |
| **Unchecked CopyRates/CopyBuffer** | Copy functions without return value check |
| **Double IndicatorRelease()** | Releasing the same handle twice |
| **Delete without NULL check** | `delete ptr` without prior null guard |

</details>

<details>
<summary><b>Memory & Allocation</b> &mdash; 7 inspections &nbsp;&nbsp;<code>Stop leaks and per-tick allocations</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Object allocation in OnTick()** | Creating objects on every tick |
| **Unchecked ArrayResize() return** | Ignoring `ArrayResize()` failure |
| **Missing NULL after delete** | Dangling pointer after `delete` |
| **Indicator handle in OnTick()** | Creating indicator handles per tick |
| **Heap allocation in loop** | `new` inside loops without object pooling |
| **Missing new bar check** | `OnTick()` without bar-change guard |
| **Unconditional order loop** | Sending orders without conditions in a loop |

</details>

<details>
<summary><b>Performance</b> &mdash; 8 inspections &nbsp;&nbsp;<code>Keep your EA fast on every tick</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **ArrayResize() in loop** | Resizing arrays inside loops instead of pre-allocating |
| **Print/Comment in OnTick()** | Logging on every tick (kills performance) |
| **Sleep() in event handler** | Blocking calls in event handlers |
| **Redundant calculations in OnTick()** | Recomputing values that only change per bar |
| **String concatenation in loop** | Using `+` for strings in loops |
| **Suboptimal container usage** | Inefficient data structure patterns |
| **Missing array pre-allocation** | Arrays that grow without reserve parameter |
| **Lazy evaluation missed** | Expensive conditions checked before cheap ones |

</details>

<details>
<summary><b>Advanced Patterns</b> &mdash; 12 inspections &nbsp;&nbsp;<code>Deep analysis for production-grade code</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Stack overflow risk** | Unbounded recursion without depth limits |
| **Dangling object reference** | Pointers to deleted or out-of-scope objects |
| **Stale handle usage** | Using handles after `IndicatorRelease()` |
| **Incomplete class (Rule of Three)** | Missing copy constructor or assignment operator |
| **GlobalVariableSet() conflicts** | Multiple functions writing the same global variable |
| **Missing error recovery** | `OrderSend()` failures without retry logic |
| **Over-complex error handling** | Deeply nested error-checking blocks |
| **Unsafe ArrayCopy()** | `ArrayCopy()` without size validation |
| **Deprecated MQL4 in MQL5** | Using deprecated MQL4 functions in MQL5 context |
| **Price comparison sans NormalizeDouble()** | Floating-point price comparisons |
| **Missing ArraySetAsSeries()** | Timeseries data without direction set |
| **Secure coding patterns** | General secure coding pattern violations |

</details>

<details>
<summary><b>Security & Data</b> &mdash; 5 inspections &nbsp;&nbsp;<code>Protect credentials and account data</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Account info exposure** | Logging sensitive account details |
| **Hardcoded credentials** | Passwords/keys embedded in source code |
| **OrderSend() without volume validation** | Trading without `SymbolInfoDouble()` checks |
| **File read without error check** | File I/O without return value validation |
| **Deterministic random seed** | Using `MathSrand()` with predictable seeds |

</details>

<details>
<summary><b>Function Signature</b> &mdash; 5 inspections &nbsp;&nbsp;<code>Get function signatures right</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **OnInit() returns void** | `void OnInit()` instead of `int OnInit()` with return code |
| **Empty event handler** | Event handlers with empty bodies |
| **Missing const on reference param** | Reference parameters that should be `const` |
| **Large struct by value** | Passing `MqlTradeRequest` etc. by copy instead of reference |
| **Missing destructor** | Classes that allocate resources but have no destructor |

</details>

<details>
<summary><b>Class Structure</b> &mdash; 6 inspections &nbsp;&nbsp;<code>Clean OOP for MQL5</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Virtual methods without virtual destructor** | Polymorphic class missing `virtual ~Destructor()` |
| **Public data members** | Public fields that should be private with accessors |
| **Missing #property description** | Scripts/indicators without `#property description` |
| **Missing #property version** | Missing `#property version` directive |
| **Excessive global variables** | Too many globals -- should be encapsulated |
| **Input parameter reassignment** | Modifying `input` parameters directly |

</details>

<details>
<summary><b>Type Safety</b> &mdash; 3 inspections &nbsp;&nbsp;<code>Prevent silent precision loss</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Narrowing return type** | Returning `double` from an `int` function |
| **Uninitialized variable** | Variables declared without initial values |
| **Implicit type cast** | Implicit narrowing conversions |

</details>

<details>
<summary><b>Naming & Style</b> &mdash; 4 inspections &nbsp;&nbsp;<code>Consistent, readable code</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Function naming convention** | Functions not in PascalCase |
| **Variable naming convention** | Variables not following naming conventions |
| **Class naming convention** | Classes without `C` prefix (`CMyClass`) |
| **Missing function doc comment** | Public functions without `//---` documentation |

</details>

<details>
<summary><b>Control Flow</b> &mdash; 6 inspections &nbsp;&nbsp;<code>Catch structural bugs</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Use of `goto`** | `goto` statements (always flagged) |
| **Suspicious semicolon** | `;` immediately after `if`/`for`/`while` |
| **Empty loop body** | Loops with no body |
| **Switch without default** | `switch` missing `default:` case |
| **Switch fall-through** | Missing `break` in `case` blocks |
| **Infinite loop risk** | Loops without clear termination |

</details>

<details>
<summary><b>Code Complexity</b> &mdash; 5 inspections &nbsp;&nbsp;<code>Keep code maintainable</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Excessive nesting depth** | Code nested too deeply (>4 levels) |
| **Function too long** | Functions exceeding 200 lines |
| **Too many parameters** | Functions with >7 parameters |
| **Unused parameter** | Parameters declared but never used |
| **TODO/FIXME markers** | Unresolved work items in code |

</details>

<details>
<summary><b>Trading-Specific</b> &mdash; 4 inspections &nbsp;&nbsp;<code>MetaTrader best practices</code></summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **Hardcoded magic numbers** | Literal values in trading operations |
| **Return value ignored** | Ignoring return values of important functions |
| **Virtual call in constructor** | Calling virtual methods from constructors |
| **Repeated API calls in OnTick()** | Calling `SymbolInfoDouble()` etc. multiple times per tick |

</details>

<details>
<summary><b>Preprocessor</b> &mdash; 1 inspection</summary>
<br/>

| Inspection | What it catches |
|:--|:--|
| **#property directive issues** | Invalid or malformed `#property` directives |

</details>

<br/>

---

<br/>

## <img src="https://img.shields.io/badge/9-templates-green?style=flat-square" alt="9 templates" /> Live Templates

Type the abbreviation, press **Tab**, and get production-ready code with proper error handling.

```
oninit     -->  OnInit() with INIT_SUCCEEDED return
ontick     -->  OnTick() with new bar check pattern
ondeinit   -->  OnDeinit() cleanup handler
ordersend  -->  Full OrderSend() with MqlTradeRequest/Result + error handling
input      -->  input parameter declaration with inline comment
indicator  -->  Indicator creation with INVALID_HANDLE check
fileop     -->  FileOpen()/FileClose() with error handling
class      -->  Class with constructor and destructor
pool       -->  Object pool pattern for reusable objects
```

> Every template follows the patterns enforced by the inspections above -- so generated code passes all 75 checks out of the box.

<br/>

---

<br/>

## <img src="https://img.shields.io/badge/quick-start-orange?style=flat-square" alt="quick start" /> Installation

<table>
<tr>
<td width="50%" valign="top">

### From JetBrains Marketplace

1. Uninstall any previous MQL plugins
2. Restart IntelliJ IDEA
3. **Settings > Plugins > Marketplace**
4. Search **"RIGGWIRE MQL"**
5. Install and restart

</td>
<td width="50%" valign="top">

### From Disk

1. Download the latest `.zip` from [Releases](https://github.com/WIRERIGG/mqlidea/releases)
2. **Settings > Plugins > Install Plugin from Disk**
3. Select the `.zip` file
4. Restart IntelliJ IDEA

</td>
</tr>
</table>

<br/>

---

<br/>

## <img src="https://img.shields.io/badge/dev-build-purple?style=flat-square" alt="build" /> Building from Source

```bash
# Requirements: Java 21 (JetBrains Runtime), Gradle 9.3 (wrapper included)

# Set JAVA_HOME
export JAVA_HOME="/c/Program Files/JetBrains/IntelliJ IDEA 2025.3.2/jbr"

# Build and run all tests
./gradlew.bat --no-daemon --console=plain build

# Launch IDE sandbox with plugin installed
./gradlew.bat --no-daemon --console=plain runIde
```

<br/>

<details>
<summary><b>Project Structure</b></summary>
<br/>

```
src/main/java/                       100+ Java source files
src/main/resources/
    META-INF/plugin.xml              Plugin manifest (75 inspections + healing registered)
    icons/                           SVG file-type badges (4, 5, h, struct) + AI healing icon
    inspectionDescriptions/          52 HTML inspection descriptions
    liveTemplates/                   MQL5 live template definitions
    mql/doc/                         1,314 HTML docs + JSON catalogs (en + ru)
src/test/                            Parser tests + MQL sample files
cpp_tests/                           134 GoogleTest safety pattern cases
```

</details>

<br/>

---

<br/>

## Compatibility

<div align="center">

| | Requirement |
|:--|:--|
| **IDE** | IntelliJ IDEA 2025.3.2+ &nbsp; (build 253.30387+) |
| **Java** | 21 &nbsp; (JetBrains Runtime) |
| **Platform** | Windows, Linux |
| **File Types** | `.mq4` `.mql4` `.mq5` `.mql5` `.mqh` |

</div>

<br/>

---

<br/>

## <img src="https://img.shields.io/badge/GPL-3.0-lightgrey?style=flat-square" alt="GPL-3.0" /> License

GPL-3.0 -- see [LICENSE.txt](LICENSE.txt) for details.

**RIGGWIRE MQL** is maintained by [RIGGWIRE Trading Systems](https://github.com/WIRERIGG). It is a fork of the [Lime MQL Editing](https://github.com/LimeMojito/mqlidea) plugin by [Lime Mojito Pty Ltd](https://limemojito.com/), which was itself forked from the [InvestFlow MQL Idea](https://github.com/investflow/mqlidea) plugin. All original copyright notices are retained per GPL-3.0; the original authors do not endorse this fork.

<br/>

<div align="center">

**Found a bug or have a feature request?**

[Open an issue](https://github.com/WIRERIGG/mqlidea/issues)

<br/><br/>

</div>
