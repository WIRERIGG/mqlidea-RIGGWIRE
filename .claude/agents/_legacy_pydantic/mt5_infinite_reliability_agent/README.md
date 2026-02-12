# MT5 Infinite Reliability Agent v2.0

An advanced, **pedantic MQL5 code optimizer** using a multi-agent architecture for comprehensive optimization of Expert Advisors (EAs), indicators, and scripts for MetaTrader 5.

## Core Philosophy

**Optimizations MUST strictly preserve all original features, logic, and functionalities.** Never remove, alter, or add new trading strategies, signals, or behaviors unless explicitly requested.

Focus solely on improving efficiency, performance, reliability, and compliance through refactoring, algorithmic refinements, and best practices derived from official MQL5 documentation.

## Target Directory

```
/Users/shemarrigg/CLionProjects/RIGGWIRE-EA/RIGGWIRE-EA-FTMO-LIVE
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     MT5 OPTIMIZATION ORCHESTRATOR                        │
│                         (Main Coordinator)                               │
├─────────────────────────────────────────────────────────────────────────┤
│  🔍 Parser Agent         │ AST analysis, code structure mapping          │
│  ⚡ Optimizer Agent      │ Performance and efficiency improvements       │
│  🛡️ FTMO Compliance Agent│ Risk management validation                    │
│  ✅ Verification Agent   │ Mathematical proofs and correctness           │
│  📚 Documentation Agent  │ MQL5 reference research                       │
├─────────────────────────────────────────────────────────────────────────┤
│                     EXTERNAL INTEGRATIONS                                │
│  → awareness_orchestrator      : State tracking, dependency management   │
│  → multi_agent_debugging_system: Deep performance analysis               │
│  → never-fail-build-resolver   : Escalation patterns                     │
└─────────────────────────────────────────────────────────────────────────┘
```

## Features

### Multi-Dimensional Optimization

| Dimension | Focus |
|-----------|-------|
| **Performance** | Reduce computational load, speed up execution |
| **Memory** | Efficient array handling, proper resource management |
| **Reliability** | Error handling, handle validation, bounds checking |
| **FTMO Compliance** | Risk management, drawdown monitoring, daily loss limits |
| **Backtest Accuracy** | Proper tick handling, consistent modeling |
| **Event-Driven** | New bar triggers, OnTimer optimization |

### Research-Based Optimization

All optimizations are based on official MQL5 documentation:
- **Primary**: https://www.mql5.com/en/docs
- **PDF Reference**: https://www.mql5.com/files/pdf/mql5.pdf (mandatory for citations)
- **Articles**: https://www.mql5.com/en/articles

### Optimization Patterns (Preserve Features, Minimal Changes)

#### 1. Event-Driven Logic
```mql5
// OPTIMIZED: Event-driven new bar detection
// Reference: MQL5 PDF - Event Handling section
// Reduces OnTick() execution to only process on new bars
bool NewBarTrigger()
{
    static datetime last_bar_time = 0;
    datetime current_bar_time = iTime(_Symbol, PERIOD_CURRENT, 0);
    if(current_bar_time != last_bar_time)
    {
        last_bar_time = current_bar_time;
        return true;
    }
    return false;
}
```

#### 2. Indicator Caching
```mql5
// OPTIMIZED: Initialize handles in OnInit(), cache values
// Reference: MQL5 PDF - Technical Indicators section
// Reduces CopyBuffer() calls by caching
static int s_handle = INVALID_HANDLE;
static double s_buffer[];

int OnInit()
{
    s_handle = iMA(_Symbol, PERIOD_CURRENT, 14, 0, MODE_SMA, PRICE_CLOSE);
    if(s_handle == INVALID_HANDLE)
    {
        Print("Error creating indicator: ", GetLastError());
        return INIT_FAILED;
    }
    ArraySetAsSeries(s_buffer, true);
    return INIT_SUCCEEDED;
}
```

#### 3. FTMO Compliance Monitoring
```mql5
// OPTIMIZED: FTMO compliance monitoring methods
// Ensures trading stays within prop firm rules
double GetCurrentDrawdown()
{
    static double equityHighWaterMark = 0;
    double currentEquity = AccountInfoDouble(ACCOUNT_EQUITY);
    if(currentEquity > equityHighWaterMark)
        equityHighWaterMark = currentEquity;
    if(equityHighWaterMark == 0) return 0;
    return (equityHighWaterMark - currentEquity) / equityHighWaterMark * 100.0;
}

bool IsTradingAllowed()
{
    if(GetCurrentDrawdown() >= 9.5) // Buffer before 10% limit
    {
        Print("FTMO: Approaching max drawdown, halting trading");
        return false;
    }
    return true;
}
```

#### 4. Pedantic Error Handling
```mql5
// OPTIMIZED: Pedantic error handling for all MQL5 API calls
// Reference: MQL5 PDF - Error Codes section
bool ValidateOrderSend(MqlTradeRequest &request, MqlTradeResult &result)
{
    ResetLastError();
    bool success = OrderSend(request, result);
    if(!success)
    {
        int error = GetLastError();
        PrintFormat("OrderSend failed. Error: %d, Retcode: %u", error, result.retcode);
        // ESCALATE: If failures persist, forward to mt5_infinite_reliability_agent
        return false;
    }
    return true;
}
```

## Installation

```bash
# From the agent directory
cd /Users/shemarrigg/CLionProjects/RIGGWIRE-EA/.claude/agents/mt5_infinite_reliability_agent

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Python API

```python
import asyncio
from mt5_infinite_reliability_agent import (
    optimize_mql5_code,
    optimize_mql5_file,
    AgentDependencies,
)

async def main():
    # Optimize code string with full workflow
    result = await optimize_mql5_code(
        code=mql5_source_code,
        mode="full",
        ftmo_compliance=True
    )

    print(f"Issues found: {len(result.get_all_issues())}")
    print(f"Transformations: {len(result.transformations)}")
    print(f"FTMO Compliant: {result.ftmo_compliance.overall_compliant}")

    # Optimize file
    result = await optimize_mql5_file(
        file_path="/path/to/EA.mq5",
        output_path="/path/to/EA_optimized.mq5"
    )

asyncio.run(main())
```

### Advanced Usage - Custom Dependencies

```python
from mt5_infinite_reliability_agent import mt5_optimizer, AgentDependencies

async def advanced_analysis():
    # Create custom dependencies
    deps = AgentDependencies(
        verification_depth="comprehensive",
        dimensions=["performance", "memory", "reliability", "ftmo_compliance"],
        proof_level="comprehensive",
        preserve_features=True,  # CRITICAL: Never alter trading logic
        ftmo_compliance_required=True,
        escalation_tier="smart",
        debug=True
    )

    # Add code snapshot for rollback
    deps.add_snapshot(your_code)

    # Set progress callback
    deps.set_progress_callback(lambda e: print(f"[{e.event_type}] {e.message}"))

    # Run orchestrator
    result = await mt5_optimizer.run(
        "Orchestrate comprehensive MQL5 optimization...",
        deps=deps
    )

    return result.data
```

## Subagent Workflow

### Phase 1: Research & Parsing
```
Documentation Agent → Parser Agent
│                     │
│ MQL5 best practices │ AST structure
│ Reference citations │ Pattern detection
│                     │ Anti-pattern flags
↓                     ↓
```

### Phase 2: Optimization
```
Optimizer Agent → FTMO Compliance Agent
│                 │
│ Transformations │ Risk validation
│ Proof annotations│ Limit checks
│                 │
↓                 ↓
```

### Phase 3: Verification & Certification
```
Verification Agent → Certificate Generation
│                    │
│ Semantic equiv.    │ Proof chain
│ Safety guarantees  │ Audit trail
│                    │
↓                    ↓
```

## Escalation Strategy

Following the `never-fail-build-resolver` pattern:

| Tier | Duration | Success Rate | Actions |
|------|----------|--------------|---------|
| FAST | 2-3 min | 90% | Common patterns, quick fixes |
| SMART | 5-10 min | 99% | Intelligent analysis, context-aware |
| THOROUGH | 10-20 min | 99.9% | Comprehensive, all dimensions |
| EMERGENCY | 1-2 min | 95% | Nuclear reset, rollback to snapshot |

## Agent Handoff Protocol

```python
# Escalate to awareness_orchestrator for state tracking
// ESCALATE: Forward to awareness_orchestrator
// Context: {optimization_result, agent_findings}

# Escalate for deep performance analysis
// ESCALATE: Forward to multi_agent_debugging_system
// Context: {execution_traces, memory_profile}

# Escalate for trade execution issues
// ESCALATE: Forward to mt5_infinite_reliability_agent
// Context: {log_excerpts, retry_count}
```

## Configuration

### Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Optional
LLM_MODEL=claude-opus-4-5-20251101
DEFAULT_PROOF_LEVEL=detailed
MAX_CODE_SIZE_KB=500
ENABLE_ATOMIC_ROLLBACK=true
LOG_LEVEL=INFO
```

### Settings

```python
from mt5_infinite_reliability_agent import settings

settings.llm_model  # "claude-opus-4-5-20251101"
settings.default_proof_level  # "detailed"
settings.max_code_size_kb  # 500
settings.analysis_timeout_seconds  # 300
settings.enable_atomic_rollback  # True
```

## Output Formats

### Optimization Result
```python
OptimizationResult(
    success=True,
    agent_findings=[...],  # Findings from all subagents
    transformations=[...],  # Applied code transformations
    ftmo_compliance=FTMOComplianceReport(...),
    optimized_code="...",
    summary="...",
    total_duration=45.2,
    recommendations=[...],
    escalation_history=["fast->smart:performance_issue"]
)
```

### Proof Certificate
```json
{
  "id": "sha256_certificate_hash",
  "version": "2.0",
  "timestamp": "2025-01-01T00:00:00Z",
  "proof_chain": [
    {"step": "analysis", "hash": "abc123..."},
    {"step": "transform_def456", "hash": "ghi789..."},
    {"step": "verification", "hash": "jkl012..."}
  ],
  "summary": {
    "issues_found": 15,
    "transformations_applied": 12,
    "verification_status": "verified",
    "confidence": 95.0,
    "semantic_equivalence": true
  },
  "mql5_references": [
    "MQL5 PDF - Technical Indicators section",
    "MQL5 PDF - Event Handling section"
  ],
  "escalation_notes": "// ESCALATE: If issues persist, forward to awareness_orchestrator"
}
```

## Project Structure

```
mt5_infinite_reliability_agent/
├── planning/               # Agent factory planning docs
│   ├── INITIAL.md
│   ├── prompts.md
│   ├── tools.md
│   └── dependencies.md
├── tests/                  # Test suite
│   ├── test_agent.py
│   ├── test_tools.py
│   └── conftest.py
├── __init__.py            # Package exports (v2.0)
├── agent.py               # Main orchestrator + 5 subagents
├── models.py              # Data models (NEW in v2.0)
├── settings.py            # Configuration management
├── providers.py           # LLM provider setup
├── dependencies.py        # Enhanced dependencies with orchestration
├── tools.py               # MQL5 optimization tools
├── prompts.py             # System prompts for all agents
├── .env.example           # Environment template
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_agent.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## API Reference

### Main Functions

#### `optimize_mql5_code(code, mode="full", ftmo_compliance=True, **kwargs)`
Optimize MQL5 code string using full subagent workflow.

#### `optimize_mql5_file(file_path, output_path=None, **kwargs)`
Optimize MQL5 file.

### Subagents

| Agent | System Prompt | Tools |
|-------|---------------|-------|
| `ParserAgent` | `PARSER_AGENT_PROMPT` | `parse_mql5_structure` |
| `OptimizerAgent` | `OPTIMIZER_AGENT_PROMPT` | `identify_optimization_opportunities` |
| `FTMOComplianceAgent` | `FTMO_COMPLIANCE_AGENT_PROMPT` | `validate_ftmo_compliance` |
| `VerificationAgent` | `VERIFICATION_AGENT_PROMPT` | `verify_transformation` |
| `DocumentationAgent` | `DOCUMENTATION_AGENT_PROMPT` | `search_mql5_documentation` |

### Models

- `OptimizationResult` - Complete optimization workflow result
- `AgentFindings` - Findings from a single subagent
- `OptimizationIssue` - Individual optimization issue
- `OptimizationTransformation` - Code transformation with proof
- `FTMOComplianceReport` - FTMO compliance assessment
- `OptimizationProof` - Mathematical proof for transformation

## Version History

- **v2.0.0** - Multi-agent architecture, subagent orchestration, FTMO compliance, awareness_orchestrator integration, escalation patterns
- **v1.0.0** - Initial release with basic analysis and verification

## Credits

Built with:
- [Pydantic AI](https://ai.pydantic.dev) - Agent framework
- [Anthropic Claude Opus 4.5](https://www.anthropic.com) - Mathematical reasoning
- [MQL5 Documentation](https://www.mql5.com/en/docs) - Official reference

---

**Generated with the Pydantic AI Agent Factory** | Built for infinite reliability

Integration: awareness_orchestrator | Patterns: never-fail-build-resolver
