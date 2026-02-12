# Awareness Orchestrator - Claude Code Interaction Workflow

## 🎯 How Claude Code Automatically Interacts with the Orchestrator

This document explains the complete workflow for how Claude Code will use the Awareness Orchestrator system automatically during development tasks.

---

## 📋 Table of Contents

1. [Automatic Trigger Scenarios](#automatic-trigger-scenarios)
2. [Complete Workflow](#complete-workflow)
3. [Deep Validation Results](#deep-validation-results)
4. [Integration Points](#integration-points)
5. [Example Sessions](#example-sessions)

---

## 🚀 Automatic Trigger Scenarios

The Awareness Orchestrator is automatically invoked when Claude Code encounters:

### 1. **User Requests for Code Analysis**
```
User: "Analyze tests/safe_test.cpp for potential improvements"
```
**→ Triggers**: Full orchestration workflow

### 2. **Complex Refactoring Tasks**
```
User: "Refactor the BLITZFIRE system to improve performance"
```
**→ Triggers**: Architecture Agent → Analysis Agent → Validation Agent sequence

### 3. **Code Quality Concerns**
```
User: "Why are we getting so many warnings in include/blitzfire_trading.hpp?"
```
**→ Triggers**: Analysis Agent with proactive suggestions

### 4. **Build or Test Failures**
```
User: "Tests are failing after my changes"
```
**→ Triggers**: Validation Agent → Build System Adapter

### 5. **Performance Optimization Requests**
```
User: "Optimize this function for speed"
```
**→ Triggers**: Analysis Agent (performance focus) + Pattern Learning

---

## 🔄 Complete Workflow

### Phase 1: Detection & Planning (Automatic)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Claude Code Receives User Request                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  2. CLAUDE.md Instructions Trigger Orchestrator Check       │
│     → "Use Archon-first rule"                               │
│     → "Deploy awareness orchestrator for analysis"          │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Pattern Recognition Recommends Agent Sequence            │
│     → Loads historical patterns                             │
│     → Suggests optimal agent order                          │
│     → Example: [Analysis → Architecture → Validation]       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Proactive Suggestions Scan Target File                  │
│     → Quick pre-scan for obvious issues                     │
│     → Returns 35+ suggestion types                          │
│     → Prioritizes critical/high severity items              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
                 START ORCHESTRATION
```

### Phase 2: Agent Execution (Sequential with Context)

```
┌─────────────────────────────────────────────────────────────┐
│  ANALYSIS AGENT (First)                                     │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                      │
│  - File path: tests/safe_test.cpp                          │
│  - Task: "Analyze for improvements"                        │
│  - Proactive findings: 35 suggestions                      │
│                                                              │
│  Tools Available:                                           │
│  - scan_file() → Get detailed code analysis                │
│  - build_project() → Compile and check warnings/errors     │
│                                                              │
│  Output:                                                     │
│  - AgentFindings with severity-ranked issues               │
│  - 10-50 specific findings with file:line locations        │
│  - Duration: ~20-30s                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓ (Context passed automatically)
                   │
┌─────────────────────────────────────────────────────────────┐
│  ARCHITECTURE AGENT (Second)                                │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                      │
│  - Analysis Agent findings (full context)                  │
│  - Identified code smells and structural issues            │
│                                                              │
│  Tools Available:                                           │
│  - get_recommended_agents() → Check pattern database       │
│                                                              │
│  Output:                                                     │
│  - Design pattern recommendations                          │
│  - Modularization strategies                               │
│  - Migration/refactoring plans                             │
│  - Duration: ~15-25s                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓ (Context accumulated)
                   │
┌─────────────────────────────────────────────────────────────┐
│  VALIDATION AGENT (Third)                                   │
├─────────────────────────────────────────────────────────────┤
│  Input:                                                      │
│  - Analysis findings                                        │
│  - Architecture recommendations                            │
│                                                              │
│  Tools Available:                                           │
│  - run_tests() → Execute GoogleTest suite                  │
│                                                              │
│  Output:                                                     │
│  - Testing strategy for proposed changes                   │
│  - Regression prevention plan                              │
│  - Quality assurance checklist                             │
│  - Duration: ~10-20s                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
               ORCHESTRATION RESULT
```

### Phase 3: Learning & Reporting (Automatic)

```
┌─────────────────────────────────────────────────────────────┐
│  1. Record Results in Pattern Database                      │
│     → Success/failure status                                │
│     → Agent sequence used                                   │
│     → Duration metrics                                      │
│     → Issues found vs resolved                              │
│                                                              │
│  Storage: .claude/agents/awareness_orchestrator/patterns/   │
│  - patterns.json (learned patterns)                         │
│  - orchestration_runs.json (historical runs)                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Update Metrics Dashboard                                │
│     → Success rate trends (7-day)                           │
│     → Agent performance comparison                          │
│     → Code quality metrics                                  │
│     → Time savings calculations                             │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Generate Report for Claude Code                         │
│     → Orchestration Result with all findings               │
│     → Prioritized recommendations                           │
│     → Implementation roadmap                                │
│     → Risk assessment                                       │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Claude Code Presents Results to User                    │
│     → Formatted findings with emojis                        │
│     → File:line references for easy navigation             │
│     → Actionable next steps                                 │
│     → Option to view full dashboard                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔍 Deep Validation Results

### System Component Validation

```
✅ Core Components (All Present):
├── __init__.py          (927 bytes)  - Package exports
├── __main__.py          (305 bytes)  - CLI entry point
├── agent.py             (9.4 KB)     - PydanticAI agents
├── models.py            (4.9 KB)     - Data structures
├── dependencies.py      (6.3 KB)     - Dependency injection
├── providers.py         (999 bytes)  - LLM configuration
├── prompts.py           (5.7 KB)     - Agent prompts
├── settings.py          (2.4 KB)     - Configuration
├── cli.py               (7.0 KB)     - CLI interface
├── requirements.txt     - Dependencies
├── README.md            - Documentation
└── .env.example         - Config template

✅ Integration Modules (backup_old/):
├── build_system_adapter.py    (18.6 KB)  - CMake/GoogleTest
├── pattern_recognition.py     (24.3 KB)  - Learning system
├── proactive_suggestions.py   (31.4 KB)  - Issue detection
├── metrics_dashboard.py       (22.9 KB)  - Performance tracking
├── progress_reporter.py       (13.3 KB)  - Real-time updates
└── prompt_templates.py        (19.9 KB)  - Context-rich prompts

✅ Class Name Validation:
├── BuildSystemAdapter          ✓ Correct
├── PatternRecognitionSystem    ✓ Correct
├── ProactiveSuggestionsEngine  ✓ Correct
├── MetricsDashboard            ✓ Correct
├── ProgressReporter            ✓ Correct
└── PromptTemplate              ✓ Correct

✅ Import Chain:
dependencies.py → backup_old/ modules → models.py → ✓ Working
```

### PydanticAI Agent Structure

```python
# awareness_orchestrator (Main Orchestrator)
Agent(
    model=AnthropicModel("claude-sonnet-4-5-20250929"),
    deps_type=OrchestrationDeps,
    result_type=OrchestrationResult,
    tools=[
        run_analysis_agent(),
        run_architecture_agent(),
        run_validation_agent(),
        record_results(),
        show_dashboard()
    ]
)

# AnalysisAgent
Agent(
    model=AnthropicModel(...),
    deps_type=OrchestrationDeps,
    result_type=AgentFindings,
    tools=[
        scan_file(),        # Proactive suggestions scan
        build_project()     # CMake build with error parsing
    ]
)

# ArchitectureAgent
Agent(
    model=AnthropicModel(...),
    deps_type=OrchestrationDeps,
    result_type=AgentFindings,
    tools=[
        get_recommended_agents()  # Pattern-based recommendations
    ]
)

# ValidationAgent
Agent(
    model=AnthropicModel(...),
    deps_type=OrchestrationDeps,
    result_type=AgentFindings,
    tools=[
        run_tests()  # GoogleTest execution with filtering
    ]
)
```

---

## 🔗 Integration Points

### 1. **Claude Code → Orchestrator**

**Trigger Method**: Task tool invocation
```python
# In CLAUDE.md workflow requirements:
# "ALL work must be consulted through the awareness orchestrator workflow"

# Claude Code automatically calls:
from awareness_orchestrator import orchestrate

result = await orchestrate(
    file_path="tests/safe_test.cpp",
    task_description="Analyze for code quality improvements"
)
```

### 2. **Orchestrator → Archon MCP**

**Integration**: Task management and knowledge queries
```python
# From within orchestrator agents:
- Update Archon tasks during execution
- Query knowledge base for implementation patterns
- Record results for project tracking
```

### 3. **Orchestrator → Build System**

**Integration**: Direct CMake/GoogleTest execution
```python
# BuildSystemAdapter automatically:
- Detects CLion CMake binary
- Runs parallel builds (14 cores)
- Parses warnings/errors
- Executes GoogleTest with filters
```

### 4. **Orchestrator → Logging Infrastructure**

**Integration**: Shared /tmp/clang_tidy_logs
```python
# Pattern Recognition reads:
- /tmp/clang_tidy_logs/comprehensive_report_*.txt
- /tmp/clang_tidy_logs/clang_tidy_tasks_*.json
- Learns from historical runs
```

---

## 💡 Example Sessions

### Example 1: Code Quality Analysis

```
User: "Analyze tests/safe_test.cpp for improvements"

Claude Code (Automatic Workflow):
┌─ Step 1: Check Archon for existing tasks
│  → archon:manage_task(action="list", filter_by="status", filter_value="todo")
│
├─ Step 2: Deploy Awareness Orchestrator
│  → from awareness_orchestrator import orchestrate
│  → result = await orchestrate("tests/safe_test.cpp", "Code quality analysis")
│
│  ┌─ Orchestrator Internal Workflow:
│  │  1. Pattern Recognition suggests [Analysis, Architecture, Validation]
│  │  2. Proactive Suggestions pre-scan: 35 issues found
│  │  3. Analysis Agent executes:
│  │     - scan_file() returns detailed suggestions
│  │     - build_project() shows 0 warnings, 0 errors
│  │     - Findings: 12 code smells, 8 performance issues
│  │  4. Architecture Agent recommends:
│  │     - Extract BLITZFIRE infrastructure to separate module
│  │     - Reduce test file size through categorization
│  │     - Apply Factory pattern for test fixtures
│  │  5. Validation Agent proposes:
│  │     - Split tests maintain 100% pass rate
│  │     - Add performance regression tests
│  │     - Create test coverage baselines
│  │  6. Record results in pattern database
│  │  7. Update metrics dashboard
│  └─ Return OrchestrationResult
│
├─ Step 3: Present Results to User
│  🎯 ORCHESTRATION COMPLETE
│  ✅ Success: true
│  ⏱️ Duration: 55.3s
│
│  📋 FINDINGS (20 total):
│
│  🔴 CRITICAL (0)
│  🟠 HIGH (3):
│     1. Magic numbers in performance tests [tests/safe_test.cpp:245]
│     2. Unchecked array access in loop [tests/safe_test.cpp:1892]
│     3. Raw pointer usage without RAII [tests/safe_test.cpp:3421]
│
│  🟡 MEDIUM (9):
│     ...
│
│  💡 TOP RECOMMENDATIONS:
│     1. Extract BLITZFIRE infrastructure → src/blitzfire/
│     2. Replace magic numbers with named constants
│     3. Apply RAII pattern for resource management
│     4. Add performance regression baselines
│
│  📊 Show dashboard? (yes/no)
│
└─ Step 4: Update Archon
   → archon:manage_task(action="update", task_id="...", status="review")
```

### Example 2: Refactoring Task

```
User: "Refactor safe_test.cpp to reduce complexity"

Claude Code (Automatic):
┌─ Orchestrator Deploys Architecture-First Sequence
│
│  Architecture Agent (Lead):
│  → Analyzes 63K line monolithic test file
│  → Recommends modularization strategy
│  → Proposes 5-phase migration plan
│
│  Analysis Agent (Support):
│  → Validates no functionality loss
│  → Checks dependency impacts
│  → Assesses risk levels
│
│  Validation Agent (Safety):
│  → Creates test matrix for each phase
│  → Proposes rollback strategies
│  → Defines acceptance criteria
│
│  Result: Comprehensive refactoring plan with:
│  - Phase-by-phase implementation
│  - Risk mitigation strategies
│  - Testing checkpoints
│  - Estimated timelines
│
└─ Claude presents plan and waits for user approval
```

---

## 🎓 Key Features of Automatic Interaction

### 1. **Zero Manual Configuration**
- Claude Code reads CLAUDE.md
- Automatically knows to use orchestrator
- No user intervention needed

### 2. **Context Preservation**
- Findings flow between agents
- No duplicate work
- Historical patterns improve recommendations

### 3. **Learning System**
- Every orchestration improves future runs
- Success patterns are reinforced
- Failed approaches are avoided

### 4. **Real-Time Progress**
- Progress Reporter emits events
- Claude can show live updates
- User sees what's happening

### 5. **Integration with Existing Tools**
- Works with Archon MCP
- Uses build system directly
- Reads clang-tidy logs
- Updates metrics automatically

---

## 🚦 Status Indicators During Orchestration

```
🚀 Starting orchestration...
📁 File: tests/safe_test.cpp
📝 Task: Code quality analysis

🔍 Scanning for issues...
   Found 35 potential improvements

🤖 Starting Analysis Agent...
   ✓ Scanned file structure
   ✓ Built project (0 warnings)
   ✓ Generated 20 findings
   Duration: 28.3s

🏗️ Starting Architecture Agent...
   ✓ Analyzed design patterns
   ✓ Recommended modularization
   ✓ Created migration plan
   Duration: 18.7s

✅ Starting Validation Agent...
   ✓ Defined testing strategy
   ✓ Created QA checklist
   ✓ Validated approach
   Duration: 12.1s

📊 Recording results...
   ✓ Updated pattern database
   ✓ Refreshed metrics dashboard

✅ Orchestration complete in 59.1s
```

---

## 🎯 Success Criteria

The orchestrator is working correctly when:

✅ **Automatic Invocation**: Claude Code uses it without being explicitly told
✅ **Context Flow**: Agents receive findings from previous agents
✅ **Pattern Learning**: Recommendations improve over time
✅ **Build Integration**: Can compile and test automatically
✅ **Results Quality**: Provides actionable, prioritized findings
✅ **Performance**: Completes in <60s for typical files
✅ **Metrics Tracking**: Dashboard shows trends and improvements

---

## 📚 Related Documentation

- [README.md](./README.md) - Installation and usage
- [COMPLETE_THREE_PHASE_SUMMARY.md](./COMPLETE_THREE_PHASE_SUMMARY.md) - System architecture
- [INTEGRATION_NOTICE.md](./INTEGRATION_NOTICE.md) - Clang-tidy integration
- [/IdeaProjects/wire_ground/CLAUDE.md](../../CLAUDE.md) - Claude Code instructions

---

**Status**: ✅ VALIDATED AND READY FOR PRODUCTION
**Last Updated**: 2025-10-01
**Version**: 1.0.0
