# mqlidea-RIGGWIRE — Project Instructions

## What This Is

An IntelliJ IDEA plugin providing MQL4/MQL5 language support for MetaTrader trading development. Features 75 code safety inspections, AI-powered code healing (Grok analysis + Claude refactoring), and comprehensive MQL5 support.

## Build

```bash
# Requires JAVA_HOME pointing to JBR 21
export JAVA_HOME="/c/Program Files/JetBrains/IntelliJ IDEA 2025.3.2/jbr"
./gradlew.bat --no-daemon --console=plain build
```

- Java 21 (JetBrains Runtime 21.0.9)
- Gradle 9.3 via wrapper
- IntelliJ Platform Gradle Plugin 2.11.0
- Target IDE: IntelliJ IDEA 2025.3.2+

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `org.xerial:sqlite-jdbc` | 3.45.1.0 | Healing database (`.idea/mql-healing.db`) |
| `com.squareup.okhttp3:okhttp` | 4.12.0 | Grok + Claude API HTTP clients |
| `com.google.code.gson:gson` | 2.10.1 | JSON serialization for API calls |

## Project Structure

```
src/main/java/com/limemojito/oss/mql/
├── healing/                              # AI Code Healing system
│   ├── HealingService.java              # Orchestrator — schedules Grok + Claude cycles
│   ├── ai/
│   │   ├── ApiKeyStorage.java           # PasswordSafe wrapper for API keys
│   │   ├── ClaudeClient.java            # Claude API — generates unified diffs
│   │   ├── DiffParser.java              # Parses unified diff into DiffPatch/Hunk records
│   │   └── GrokClient.java              # Grok API — analyzes problems with MQL5 context
│   ├── actions/
│   │   ├── ApplyClaudeDiffFix.java      # LocalQuickFix for applying Claude diffs
│   │   └── DiffApplier.java             # Applies diffs via WriteCommandAction (bottom-up)
│   ├── db/
│   │   ├── ClaudeTask.java              # Record: diff task status tracking
│   │   ├── GrokInsight.java             # Record: Grok analysis results
│   │   ├── HealingDatabase.java         # SQLite project service (3 tables)
│   │   ├── HealingStartupActivity.java  # Init DB + start service on project open
│   │   └── ProblemRecord.java           # Record: problem data from inspections
│   ├── ui/
│   │   ├── HealingAnnotator.java        # Alt+Enter "Apply AI fix" intentions
│   │   ├── HealingLineMarkerProvider.java # Gutter icon on files with AI fixes
│   │   └── HealingToolWindowFactory.java # Tool window: AI Healing + Claude Code tabs
│   └── vcs/
│       └── HealingCheckinHandlerFactory.java # Pre-commit prompt for pending fixes
├── inspection/                           # 75 MQL5 safety inspections
│   ├── MQL5SafetyInspectionBase.java    # Base class for inspections
│   ├── MqlProblemsLoggerService.java    # Scans files, caches results, syncs to healing DB
│   ├── BracketBlockTokenWalker.java     # Token scanner for opaque {} blocks
│   └── ...                               # 72 inspection classes
├── settings/
│   ├── MQL4PluginSettings.java          # Settings interface (includes healing settings)
│   ├── MQL4PluginSettingsImpl.java      # Persistent state (healing fields added)
│   └── MQL4PluginSettingsPanel.java     # Settings UI (AI Healing section)
├── MQL4Icons.java                        # Icons including Healing/Healing16
└── ...                                   # Parser, editor, SDK, indexing (60+ files)

src/main/resources/
├── META-INF/plugin.xml                   # Plugin manifest — ALL extensions registered here
├── icons/
│   ├── mql_healing.png                   # 13x13 healing icon
│   ├── mql_healing_16.png               # 16x16 healing icon (tool window, gutter)
│   └── ...                               # File type icons
├── inspectionDescriptions/               # 52 HTML inspection descriptions
├── liveTemplates/                        # MQL5 live templates
└── mql/                                  # MQL docs (1,314 HTML) + JSON catalogs

src/test/                                 # Parser tests + MQL sample files (9 tests)
cpp_tests/                                # C++ safety test patterns (134 GoogleTest cases)
.claude/agents/                           # Claude Code agent definitions
.claude/MQL5_REFERENCE.md               # MQL5 API reference
```

## AI Healing Architecture

### Database Schema (`.idea/mql-healing.db`)
```sql
problems(id, file_url, file_path, line, severity, message, inspection_name, fix_hint, first_seen_at, last_seen_at, resolved_at)
grok_insights(id, problem_id FK, insight, created_at)
claude_tasks(id, problem_id FK, diff, status, created_at, applied_at)
```

### Data Flow
1. `MqlProblemsLoggerService` scans all MQL files → caches problems → syncs to `HealingDatabase`
2. `HealingService` (scheduled) queries DB for unanalyzed problems → sends to `GrokClient` → stores insights
3. `HealingService` queries problems with insights but no Claude tasks → sends to `ClaudeClient` → stores diffs
4. `DiffApplier` applies diffs via `WriteCommandAction` (bottom-up hunk order, conflict detection)
5. UI surfaces fixes via tool window, gutter icons, Alt+Enter intentions, and pre-commit prompts

### Settings (persisted in `mql4-plugin.xml`)
- `healingDelayMinutes` (default: 5) — interval between healing cycles
- `autoHealEnabled` (default: false) — master switch for automatic healing
- `grokModel` (default: "grok-2") — Grok model for analysis
- `claudeModel` (default: "claude-sonnet-4-5-20250929") — Claude model for diffs
- API keys stored in IntelliJ PasswordSafe (not in settings file)

### Plugin.xml Extensions (healing)
- `projectService`: HealingDatabase, HealingService
- `postStartupActivity`: HealingStartupActivity
- `toolWindow`: MQL Healing (AI Healing + Claude Code tabs)
- `codeInsight.lineMarkerProvider`: HealingLineMarkerProvider
- `annotator`: HealingAnnotator
- `checkinHandlerFactory`: HealingCheckinHandlerFactory

## Rules

- Never remove existing features — only add or enhance
- All new extensions must be registered in `plugin.xml`
- All 9 existing tests must pass after changes
- Source is Java (not Kotlin) targeting Java 21
- Both MQL4 and MQL5 use `language="MQL4"` in plugin.xml
- Stub schema version is 19 — increment when changing stub structure
- PasswordSafe calls must use `SlowOperations.allowSlowOperations()` or run off EDT
- Tool window refresh must run DB/PasswordSafe queries on pooled thread, update UI via `SwingUtilities.invokeLater()`
- Run `./gradlew.bat build` to verify after every change

## Available Agents

| Agent | Purpose |
|-------|---------|
| `orchestrator` | Coordinates multi-domain changes |
| `plugin-developer` | IntelliJ plugin architecture and extensions |
| `mql5-specialist` | MQL5 language expertise and parser guidance |
| `code-quality` | Code inspections and quality rules |
| `code-optimizer` | Performance optimization |
| `build-resolver` | Gradle build and CI/CD issues |
| `safety-analyzer` | C++ safety patterns → MQL5 inspections |
