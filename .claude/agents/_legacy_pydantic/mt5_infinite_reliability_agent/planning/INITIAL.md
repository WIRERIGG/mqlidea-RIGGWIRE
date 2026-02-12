# MT5 Infinite Reliability Agent - Simple Requirements

## What This Agent Does
Analyzes MQL5/MT5 code for safety issues, generates verified fixes with mathematical proofs, and produces certified refactored code. Think of it as a "proof-driven code doctor" that not only finds problems but fixes them with mathematical certainty.

## Core Features (MVP)

1. **Multi-Dimensional Code Analysis**
   - Parse MQL5 code and identify issues across 8 dimensions
   - Focus on: complexity, memory safety, security, and robustness
   - Generate detailed analysis reports with severity scoring

2. **Fix Generation with Verification**
   - Automatically generate code transformations for identified issues
   - Apply fixes atomically (all-or-nothing, with rollback capability)
   - Verify each transformation maintains code correctness

3. **Certification & Proof Chains**
   - Issue structured certificates for verified code
   - Create audit trails showing before/after transformations
   - Generate proof annotations embedded in output code

## Technical Setup

### Model
- **Provider**: Anthropic
- **Model**: claude-opus-4-5-20251101
- **Why**: Superior code reasoning and mathematical proof generation capabilities

### Required Tools

#### 1. MQL5 Code Parser
**Purpose**: Parse and analyze MQL5 source code structure
**Implementation**: Python tool (build custom parser)
- Extract functions, variables, control flow
- Identify patterns and anti-patterns
- Generate AST-like structure

#### 2. Static Analysis Engine
**Purpose**: Detect code quality and safety issues
**Implementation**: Python tool integrating:
- Basic pattern matching for common MQL5 vulnerabilities
- Complexity metrics (cyclomatic complexity, nesting depth)
- Memory safety checks (buffer access, pointer usage)
- Security checks (input validation, SQL injection in DB operations)

#### 3. Code Transformer
**Purpose**: Apply verified fixes to code
**Implementation**: Python tool
- Template-based code generation
- Atomic application with snapshot/rollback
- Syntax preservation and formatting

#### 4. Verification Engine
**Purpose**: Validate transformations maintain correctness
**Implementation**: Python tool
- Pre/post-condition checking
- Equivalence verification (simplified formal methods)
- Regression test generation

#### 5. Certificate Generator
**Purpose**: Create proof chains and certification documents
**Implementation**: Python tool
- Merkle tree structure for audit trails
- Structured proof annotations
- JSON/Markdown output formats

### External Services
- **None required for MVP**: All verification logic implemented in Python tools
- **Future**: Integration with MT5 compiler API for syntax validation

## Environment Variables
```bash
ANTHROPIC_API_KEY=your-anthropic-api-key
# Optional: MT5 installation path for compiler validation
MT5_TERMINAL_PATH=/path/to/mt5/terminal
```

## Input/Output Format

### Input
```python
{
    "code": "string (MQL5 source code)",
    "mode": "analyze | fix | certify | full",
    "options": {
        "dimensions": ["complexity", "memory", "security", "robustness"],
        "auto_apply": true,
        "proof_level": "basic | detailed | comprehensive"
    }
}
```

### Output
```python
{
    "analysis": {
        "issues_found": int,
        "severity_breakdown": {"critical": int, "high": int, "medium": int, "low": int},
        "dimensions": {
            "complexity": {"score": float, "issues": [...]},
            "memory": {"score": float, "issues": [...]},
            # ... other dimensions
        }
    },
    "transformations": [
        {
            "issue_id": "string",
            "original_code": "string",
            "fixed_code": "string",
            "proof": "string (mathematical justification)",
            "verification_status": "verified | unverified"
        }
    ],
    "refactored_code": "string (complete fixed code)",
    "certificate": {
        "id": "string (hash)",
        "timestamp": "ISO8601",
        "proof_chain": ["hash1", "hash2", ...],
        "verification_metrics": {...}
    }
}
```

## Success Criteria
- [ ] Can analyze MQL5 code and identify issues across 4+ dimensions
- [ ] Generates valid fix suggestions with proof justifications
- [ ] Applies transformations atomically (can rollback on failure)
- [ ] Produces structured certificates with audit trails
- [ ] Handles basic MQL5 syntax correctly (functions, variables, indicators)

## Implementation Phases

### Phase 1: Analysis (MVP Core)
- Build MQL5 parser in Python
- Implement 4 core analysis dimensions
- Generate structured analysis reports

### Phase 2: Fix Generation
- Create transformation templates for common issues
- Implement atomic code transformer
- Add basic verification checks

### Phase 3: Certification
- Build proof chain generator
- Create certificate structure
- Add audit trail capabilities

## Python Tools to Build

### 1. `mql5_parser.py`
- Lexer/parser for MQL5 syntax
- AST generation
- Pattern recognition

### 2. `static_analyzer.py`
- Complexity metrics calculator
- Memory safety checker
- Security vulnerability scanner
- Robustness analyzer

### 3. `code_transformer.py`
- Transformation engine
- Snapshot/rollback manager
- Syntax-preserving refactoring

### 4. `verifier.py`
- Pre/post-condition validator
- Equivalence checker
- Test case generator

### 5. `certificate_engine.py`
- Merkle tree builder
- Proof annotation generator
- Certificate serializer

## Assumptions Made

1. **No external MT5 compiler required for MVP**: We'll validate syntax using Python-based parsing. MT5 compiler integration is a future enhancement.

2. **Simplified formal verification**: Instead of full theorem proving, we use:
   - Pattern-based correctness checks
   - Pre/post-condition validation
   - Statistical verification (test generation)

3. **8D Analysis simplified to 4D for MVP**: Focus on complexity, memory, security, robustness. Add temporal, concurrency, probabilistic, adaptive in later iterations.

4. **Proof generation is LLM-assisted**: The agent generates mathematical justifications using Claude's reasoning, not external theorem provers. This is sufficient for practical verification.

5. **MQL5 subset support**: MVP targets common trading EA patterns. Full MQL5 language support is iterative.

6. **Local operation**: All processing happens locally with Python tools. No external API dependencies except the LLM.

7. **File-based I/O**: Agent reads/writes MQL5 files directly. Integration with IDEs/MT5 terminal comes later.

## Technical Architecture

```
User Request (MQL5 code)
    ↓
┌─────────────────────────────────────┐
│   Pydantic AI Agent (Orchestrator)  │
│   - Workflow management             │
│   - LLM reasoning for proofs        │
│   - Result aggregation              │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│         Python Tool Suite           │
│                                     │
│  [Parser] → [Analyzer] → [Transformer] │
│       ↓          ↓            ↓     │
│  [Verifier] ← [Certificate Engine] │
└─────────────────────────────────────┘
    ↓
Output (Refactored code + Certificate)
```

## Non-Functional Requirements

- **Performance**: Analyze typical EA (<1000 lines) in under 30 seconds
- **Reliability**: Rollback on any transformation failure (zero data loss)
- **Auditability**: Every transformation logged with proof chain
- **Extensibility**: Plugin architecture for adding new analysis dimensions

## Out of Scope (Post-MVP)

- Real-time MT5 terminal integration
- Distributed verification (blockchain)
- GUI/web interface
- Multi-file project analysis
- Full formal theorem proving
- Automated test execution in MT5 Strategy Tester

---

**Generated**: 2025-12-20

**Note**: This is an MVP designed to deliver working code analysis and verification quickly. The "infinite reliability" concept is implemented through iterative improvement - start with solid fundamentals (parsing, analysis, verification) and expand capabilities based on real-world usage.

**Philosophy**: Build Python-based verification tools rather than depending on external systems. This ensures the agent works reliably and can be extended without external dependencies.
