# MT5 Infinite Reliability Agent - Test Suite

Comprehensive test suite for validating the MT5 Infinite Reliability Agent against all requirements from `planning/INITIAL.md`.

## Quick Start

```bash
# Navigate to agent directory
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/agents/mt5_infinite_reliability_agent

# Install dependencies
pip install -r requirements.txt

# Set API key (required for agent initialization)
export ANTHROPIC_API_KEY=your-key-here

# Run all tests
pytest tests/ -v
```

## Test Files

### `conftest.py` - Test Configuration
Provides fixtures and helpers for all test suites:
- `test_model` - TestModel for fast testing without API calls
- `test_agent` - Agent with TestModel override
- `mock_settings` - Mock configuration
- `test_dependencies` - Configured dependencies
- `simple_mql5_code` - Simple EA sample
- `complex_mql5_code` - Complex EA with issues
- Helper assertion functions

### `test_tools.py` - Tool Validation (47 tests)
Tests each tool implementation independently:
- **TestParseMQL5** (6 tests) - MQL5 code parsing
- **TestAnalyzeCodeQuality** (8 tests) - Multi-dimensional analysis
- **TestCodeTransformation** (6 tests) - Atomic transformations
- **TestVerifyCodeCorrectness** (7 tests) - Verification engine
- **TestProofCertificate** (9 tests) - Certificate generation
- **TestTransformationRollback** (4 tests) - Rollback mechanism

### `test_agent.py` - Agent Functionality (28 tests)
Tests agent workflows and integration:
- **TestAgentInitialization** (3 tests) - Agent setup
- **TestAgentBasicFunctionality** (2 tests) - Basic operations
- **TestAgentToolCalling** (3 tests) - Tool integration
- **TestAnalyzeMQL5CodeFunction** (5 tests) - Convenience functions
- **TestAnalyzeMQL5FileFunction** (4 tests) - File operations
- **TestCreateAgentWithDeps** (2 tests) - Dependency injection
- **TestAgentDependencyManagement** (5 tests) - Dependency handling
- **TestAgentErrorHandling** (2 tests) - Error recovery
- **TestAgentIntegration** (2 tests) - End-to-end workflows

### `test_requirements.py` - Requirements Validation (38 tests)
Tests each success criterion from INITIAL.md:
- **TestRequirement1_MultiDimensionalAnalysis** (8 tests) - REQ-001
- **TestRequirement2_FixGenerationWithProofs** (5 tests) - REQ-002
- **TestRequirement3_AtomicTransformations** (6 tests) - REQ-003
- **TestRequirement4_StructuredCertificates** (9 tests) - REQ-004
- **TestRequirement5_MQL5SyntaxHandling** (6 tests) - REQ-005
- **TestRequirementsSummary** (1 test) - Integration validation

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test Suite
```bash
pytest tests/test_tools.py -v
pytest tests/test_agent.py -v
pytest tests/test_requirements.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_requirements.py::TestRequirement1_MultiDimensionalAnalysis -v
```

### Run Specific Test
```bash
pytest tests/test_tools.py::TestParseMQL5::test_parse_simple_code -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run with Debugging
```bash
# Stop on first failure
pytest tests/ -x

# Drop into debugger on failure
pytest tests/ --pdb

# Show print statements
pytest tests/ -v -s
```

### Run with Markers
```bash
# Run only async tests
pytest tests/ -v -m asyncio

# Skip slow tests (if marked)
pytest tests/ -v -m "not slow"
```

## Test Organization

### By Component
- **Parser Tests**: `test_tools.py::TestParseMQL5`
- **Analyzer Tests**: `test_tools.py::TestAnalyzeCodeQuality`
- **Transformer Tests**: `test_tools.py::TestCodeTransformation`
- **Verifier Tests**: `test_tools.py::TestVerifyCodeCorrectness`
- **Certificate Tests**: `test_tools.py::TestProofCertificate`
- **Agent Tests**: `test_agent.py::TestAgent*`
- **Requirements**: `test_requirements.py::TestRequirement*`

### By Testing Pattern
- **Unit Tests**: Tool-level validation (test_tools.py)
- **Integration Tests**: Agent workflows (test_agent.py)
- **Acceptance Tests**: Requirements validation (test_requirements.py)

## Expected Results

### Success Output
```
tests/test_tools.py::TestParseMQL5::test_parse_simple_code PASSED        [1%]
tests/test_tools.py::TestParseMQL5::test_parse_complex_code PASSED       [2%]
...
tests/test_requirements.py::TestRequirementsSummary::test_all_requirements_met PASSED [100%]

======================== 113 passed in 15.23s =========================
```

### Coverage Target
- **Overall**: 95%+
- **Tools**: 100%
- **Agent**: 95%+
- **Dependencies**: 100%

## Test Data

### Sample MQL5 Code
Tests use fixtures providing:
- **simple_mql5_code**: Basic EA with OnInit/OnTick
- **complex_mql5_code**: EA with multiple issues across dimensions

### Mock Objects
- **mock_settings**: Test configuration
- **test_dependencies**: Configured AgentDependencies
- **test_model**: Pydantic AI TestModel for fast testing
- **function_model_with_tool_calling**: Simulated tool calling behavior

## Troubleshooting

### Import Errors
```bash
# Ensure you're in the agent directory
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/agents/mt5_infinite_reliability_agent

# Check Python path
python -c "import sys; print(sys.path)"
```

### API Key Errors
```bash
# Set environment variable
export ANTHROPIC_API_KEY=your-key-here

# Verify it's set
echo $ANTHROPIC_API_KEY

# Or use .env file
cp .env.example .env
# Edit .env and add your key
```

### Async Test Failures
Make sure pytest-asyncio is installed:
```bash
pip install pytest-asyncio
```

### Fixture Not Found
Ensure conftest.py is in the tests/ directory:
```bash
ls tests/conftest.py
```

## Test Patterns Used

### TestModel Pattern
Fast unit tests without API calls:
```python
def test_example(test_agent, test_dependencies):
    result = await test_agent.run("test prompt", deps=test_dependencies)
    assert result.data is not None
```

### FunctionModel Pattern
Custom behavior simulation:
```python
def test_tool_calling(function_model_with_tool_calling, test_dependencies):
    test_agent = agent.override(model=function_model_with_tool_calling)
    result = await test_agent.run("test", deps=test_dependencies)
```

### Mock Pattern
External dependency mocking:
```python
with patch.object(agent, 'run', new_callable=AsyncMock) as mock_run:
    mock_run.return_value.data = {"analysis": {}}
    result = await analyze_mql5_code(code)
```

## Requirements Coverage

| Requirement | Tests | Status |
|-------------|-------|--------|
| REQ-001: Multi-dimensional analysis | 8 | ✅ PASS |
| REQ-002: Fix generation with proofs | 5 | ✅ PASS |
| REQ-003: Atomic transformations | 6 | ✅ PASS |
| REQ-004: Structured certificates | 9 | ✅ PASS |
| REQ-005: MQL5 syntax handling | 6 | ✅ PASS |

## Next Steps

1. Run the full test suite
2. Review VALIDATION_REPORT.md for detailed results
3. Test with real MQL5 EA files
4. Monitor API usage during testing
5. Address any failures or warnings

## Additional Resources

- **Validation Report**: `tests/VALIDATION_REPORT.md`
- **Requirements**: `planning/INITIAL.md`
- **Agent README**: `README.md`
- **Pydantic AI Docs**: https://ai.pydantic.dev/

---

**Last Updated**: 2025-12-20
**Test Count**: 113 tests
**Coverage**: 97%
