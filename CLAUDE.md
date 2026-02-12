# mqlidea-RIGGWIRE — Project Instructions

## What This Is

An IntelliJ IDEA plugin providing MQL4/MQL5 language support for MetaTrader trading development. Being enhanced with code safety inspections, AI-assisted development, and comprehensive MQL5 support.

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

## Project Structure

```
src/main/java/com/limemojito/oss/mql/   # Plugin Java source (101 files)
src/main/resources/META-INF/plugin.xml   # Plugin manifest — register ALL new features here
src/main/resources/mql/                  # MQL docs (1,314 HTML) + JSON catalogs
src/test/                                # Parser tests + MQL sample files
cpp_tests/                               # C++ safety test patterns (134 GoogleTest cases)
.claude/agents/                          # Claude Code agent definitions
.claude/MQL5_REFERENCE.md               # MQL5 API reference
```

## Rules

- Never remove existing features — only add or enhance
- All new extensions must be registered in `plugin.xml`
- All 9 existing tests must pass after changes
- Source is Java (not Kotlin) targeting Java 21
- Both MQL4 and MQL5 use `language="MQL4"` in plugin.xml
- Stub schema version is 19 — increment when changing stub structure
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
