# Awareness Orchestrator - Complete Testing Guide

## Overview

This guide provides **step-by-step testing procedures** for validating all 23 fixes from `PRIORITIZED_FIX_LIST.md`.

**Testing Philosophy:**
- **Zero-tolerance for failures** - All tests must pass before production
- **Multi-layer validation** - Unit → Integration → System → Production
- **Automated first** - Run automated tests before manual validation
- **Evidence-based** - Collect metrics, logs, and test results

**Time Investment:**
- Phase 1-3 (Automated): ~30 minutes
- Phase 4-6 (Manual): ~60 minutes
- Phase 7 (Production): ~1 week

**Total:** ~2 hours + 1 week production validation

---

## Testing Phases

### Phase 1: Environment Setup & Validation (5 minutes)

**Goal:** Verify clean Python environment and dependencies.

#### Step 1.1: Verify Python Version
```bash
python3 --version
# Expected: Python 3.9+ (3.10 or 3.11 recommended)
```

#### Step 1.2: Create Virtual Environment
```bash
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/.claude/agents/awareness_orchestrator

# Create venv
python3 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Verify activation
which python  # Should show venv/bin/python
```

#### Step 1.3: Install Dependencies
```bash
# Install testing tools
pip install --upgrade pip
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Install PydanticAI
pip install pydantic-ai

# Install other dependencies
pip install -r requirements.txt  # If exists

# Verify installations
pip list | grep pytest
# Expected: pytest, pytest-asyncio, pytest-cov, pytest-mock
```

#### Step 1.4: Verify sys.path Clean
```bash
python3 -c "
import sys
original_path = sys.path.copy()
from awareness_orchestrator.dependencies import OrchestrationDeps
assert sys.path == original_path, 'sys.path polluted!'
print('✅ sys.path clean')
"
```

**Pass Criteria:**
- ✅ Python 3.9+
- ✅ Virtual environment activated
- ✅ All dependencies installed
- ✅ sys.path clean after imports

**Red Flags:**
- ❌ Python <3.9
- ❌ Import errors
- ❌ sys.path modified after import (indicates Fix #1 not applied)

---

### Phase 2: Automated Test Suite (10 minutes)

**Goal:** Run complete automated test suite and verify 100% pass rate.

#### Step 2.1: Run All Tests with Verbose Output
```bash
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/.claude/agents/awareness_orchestrator

# Run all tests
pytest test_orchestrator_suite.py -v

# Expected output:
# ============================= test session starts ==============================
# ...
# test_orchestrator_suite.py::TestCriticalFixes::test_fix1_no_syspath_pollution PASSED
# test_orchestrator_suite.py::TestCriticalFixes::test_fix2_no_hardcoded_paths PASSED
# ...
# ============================== X passed, Y skipped in Z.XXs ===============================
```

#### Step 2.2: Run Tests by Category
```bash
# Critical tests only (must all pass)
pytest test_orchestrator_suite.py::TestCriticalFixes -v

# High-priority tests
pytest test_orchestrator_suite.py::TestHighPriorityFixes -v

# Integration tests
pytest test_orchestrator_suite.py::TestIntegration -v
```

#### Step 2.3: Run with Coverage
```bash
# Generate coverage report
pytest test_orchestrator_suite.py --cov=awareness_orchestrator --cov-report=html --cov-report=term

# Expected output:
# Name                                    Stmts   Miss  Cover
# -----------------------------------------------------------
# awareness_orchestrator/__init__.py         10      0   100%
# awareness_orchestrator/agent.py           150     20    87%
# awareness_orchestrator/dependencies.py     80     10    88%
# awareness_orchestrator/models.py           40      5    88%
# -----------------------------------------------------------
# TOTAL                                     280     35    87%

# Open HTML report
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

#### Step 2.4: Run Specific Fix Tests
```bash
# Test Fix #1 (sys.path pollution)
pytest test_orchestrator_suite.py::TestCriticalFixes::test_fix1_no_syspath_pollution -v

# Test Fix #2 (hard-coded paths)
pytest test_orchestrator_suite.py::TestCriticalFixes::test_fix2_no_hardcoded_paths -v

# Test Fix #4 (error handling)
pytest test_orchestrator_suite.py::TestCriticalFixes::test_fix4_error_handling_nonexistent_file -v
```

**Pass Criteria:**
- ✅ All critical tests pass (8/8)
- ✅ All high-priority tests pass or skip (6/6)
- ✅ All integration tests pass or skip (3/3)
- ✅ Code coverage >80%
- ✅ No test failures (FAILED)
- ⚠️ Skipped tests acceptable (indicates fix not yet applied)

**Red Flags:**
- ❌ Any FAILED tests
- ❌ Coverage <60%
- ❌ Import errors during test collection
- ❌ Segmentation faults or crashes

**Interpreting Results:**

```
PASSED - ✅ Test passed, fix is working
SKIPPED - ⚠️ Test skipped, fix may not be applied yet (acceptable)
FAILED - ❌ Test failed, fix is broken or not applied (MUST FIX)
ERROR - ❌ Test raised unexpected error (MUST FIX)
```

---

### Phase 3: Type Safety Validation (5 minutes)

**Goal:** Verify type hints are correct using mypy.

#### Step 3.1: Install mypy
```bash
pip install mypy
```

#### Step 3.2: Run mypy on All Files
```bash
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/.claude/agents/awareness_orchestrator

# Run mypy (lenient mode first)
mypy agent.py dependencies.py models.py

# Expected: 0 errors
# If errors, fix them before proceeding
```

#### Step 3.3: Run mypy in Strict Mode
```bash
# Strict mode (after fixes applied)
mypy --strict agent.py dependencies.py models.py

# Target: 0 errors
# Acceptable: Some errors if Fix #13 not fully applied
```

#### Step 3.4: Check Type Coverage
```bash
mypy --any-exprs-report mypy_report agent.py dependencies.py models.py

# Review report
cat mypy_report/*.txt
```

**Pass Criteria:**
- ✅ mypy runs without crashing
- ✅ 0 errors in lenient mode
- ⚠️ <10 errors in strict mode (acceptable if Fix #13 not applied)

**Red Flags:**
- ❌ Import errors
- ❌ >20 type errors in lenient mode
- ❌ Type errors in critical functions

---

### Phase 4: Manual Code Quality Review (15 minutes)

**Goal:** Manually verify code quality improvements.

#### Step 4.1: Review sys.path Handling
```bash
# Check dependencies.py
grep -n "sys.path" awareness_orchestrator/dependencies.py

# Expected: No sys.path.insert or sys.path.append
# If found, Fix #1 not applied
```

#### Step 4.2: Review Hard-Coded Paths
```bash
# Check for hard-coded paths
grep -rn "/IdeaProjects/wire_ground" awareness_orchestrator/

# Expected: No matches
# If matches found, Fix #2 not applied
```

#### Step 4.3: Review Error Handling
```bash
# Check agent.py for error handling
grep -A 5 "try:" awareness_orchestrator/agent.py | head -30

# Expected: See try/except blocks in tool functions
# If not found, Fix #4 not applied
```

#### Step 4.4: Review Logging
```bash
# Check for logging usage
grep -n "logger\." awareness_orchestrator/agent.py | head -10

# Expected: Multiple logger.info, logger.error calls
# If not found, Fix #12 not applied
```

#### Step 4.5: Review Configuration
```bash
# Check OrchestrationConfig
grep -A 20 "class OrchestrationConfig" awareness_orchestrator/dependencies.py

# Expected: See max_files_per_workflow, timeouts
# If not found, Fix #10 not applied
```

**Pass Criteria:**
- ✅ No sys.path manipulation
- ✅ No hard-coded paths
- ✅ Error handling present
- ✅ Logging configured
- ✅ Configuration class exists

**Red Flags:**
- ❌ sys.path.insert found
- ❌ /IdeaProjects/wire_ground found
- ❌ No try/except blocks
- ❌ No logging

---

### Phase 5: Integration Testing (20 minutes)

**Goal:** Verify complete workflows work end-to-end.

#### Step 5.1: Test Dependency Creation
```python
# Run in Python REPL
python3

>>> from awareness_orchestrator.dependencies import OrchestrationDeps
>>> deps = OrchestrationDeps.create_default()
>>> print(f"Project root: {deps.project_root}")
>>> print(f"Build dir: {deps.build_dir}")
>>> assert deps.project_root.exists()
>>> print("✅ Dependency creation works")
```

#### Step 5.2: Test Configuration
```python
>>> from awareness_orchestrator.dependencies import OrchestrationConfig
>>> config = OrchestrationConfig(max_files_per_workflow=50)
>>> print(f"Max files: {config.max_files_per_workflow}")
>>> assert config.max_files_per_workflow == 50
>>> print("✅ Configuration works")
```

#### Step 5.3: Test File Validation
```python
>>> import tempfile
>>> import os
>>>
>>> # Create test file
>>> with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
...     f.write("int main() { return 0; }")
...     temp_file = f.name
>>>
>>> # Test file validation
>>> from pathlib import Path
>>> path = Path(temp_file)
>>> assert path.exists()
>>> print(f"✅ File validation works: {path}")
>>>
>>> # Cleanup
>>> os.unlink(temp_file)
```

#### Step 5.4: Test Error Scenarios
```python
>>> # Test nonexistent file
>>> import asyncio
>>> from awareness_orchestrator.agent import awareness_orchestrator
>>>
>>> async def test_error():
...     try:
...         result = await awareness_orchestrator.run(
...             "run_analysis_agent",
...             file_path="/nonexistent/file.cpp",
...             deps=deps
...         )
...         print("❌ Should have raised error!")
...     except Exception as e:
...         print(f"✅ Error handled: {type(e).__name__}")
>>>
>>> asyncio.run(test_error())
```

**Pass Criteria:**
- ✅ Dependencies created successfully
- ✅ Configuration works
- ✅ File validation works
- ✅ Error handling works
- ✅ No crashes or hangs

**Red Flags:**
- ❌ Dependency creation fails
- ❌ Hard-coded path errors
- ❌ Unhandled exceptions
- ❌ Crashes or hangs

---

### Phase 6: Performance & Memory Testing (10 minutes)

**Goal:** Verify no memory leaks or performance regressions.

#### Step 6.1: Memory Leak Test
```python
# Run in Python REPL
import tracemalloc
import gc

tracemalloc.start()

# Take initial snapshot
snapshot1 = tracemalloc.take_snapshot()

# Create and destroy dependencies 100 times
from awareness_orchestrator.dependencies import OrchestrationDeps

for i in range(100):
    deps = OrchestrationDeps.create_default()
    del deps
    if i % 10 == 0:
        gc.collect()

# Take final snapshot
snapshot2 = tracemalloc.take_snapshot()

# Compare
top_stats = snapshot2.compare_to(snapshot1, 'lineno')

print("\n[ Top 10 memory increases ]")
for stat in top_stats[:10]:
    print(stat)

# Expected: Memory growth <1MB for 100 iterations
```

#### Step 6.2: Performance Benchmark
```python
import time

# Benchmark dependency creation
start = time.time()

for i in range(100):
    deps = OrchestrationDeps.create_default()

end = time.time()
avg_time = (end - start) / 100 * 1000  # Convert to ms

print(f"Average creation time: {avg_time:.2f}ms")
# Expected: <10ms per creation
```

#### Step 6.3: Concurrent Test
```python
import asyncio

async def concurrent_test():
    """Test concurrent agent execution."""
    deps = OrchestrationDeps.create_default()

    # Create test file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write("int main() { return 0; }")
        temp_file = f.name

    # Launch 5 concurrent analysis tasks
    tasks = []
    for i in range(5):
        task = awareness_orchestrator.run(
            "run_analysis_agent",
            file_path=temp_file,
            deps=deps
        )
        tasks.append(task)

    # Gather results (or exceptions)
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Cleanup
    import os
    os.unlink(temp_file)

    return results

# Run test
results = asyncio.run(concurrent_test())
print(f"Completed {len(results)} concurrent tasks")
print("✅ No race conditions detected" if len(results) == 5 else "❌ FAILED")
```

**Pass Criteria:**
- ✅ Memory growth <1MB for 100 iterations
- ✅ Dependency creation <10ms average
- ✅ Concurrent execution works
- ✅ No deadlocks or race conditions

**Red Flags:**
- ❌ Memory growth >10MB
- ❌ Creation time >100ms
- ❌ Concurrent test hangs
- ❌ Exceptions from race conditions

---

### Phase 7: Production Deployment Validation (1 week)

**Goal:** Validate in production-like environment before live deployment.

#### Step 7.1: Deploy to Staging Environment
```bash
# Set production environment variables
export PROJECT_ROOT=/path/to/real/project
export BUILD_DIR=/path/to/real/project/cmake-build-debug
export MAX_FILES=200
export ANALYSIS_TIMEOUT=600.0

# Verify environment
python3 -c "
from awareness_orchestrator.dependencies import OrchestrationDeps
deps = OrchestrationDeps.from_env()
print(f'Project root: {deps.project_root}')
print(f'Max files: {deps.config.max_files_per_workflow}')
"
```

#### Step 7.2: Run on Real Codebase
```bash
# Test on small subset first (5 files)
python3 -c "
import asyncio
from awareness_orchestrator.agent import awareness_orchestrator
from awareness_orchestrator.dependencies import OrchestrationDeps

async def test_real():
    deps = OrchestrationDeps.from_env()
    result = await awareness_orchestrator.run(
        'coordinate_full_workflow',
        target_files=[
            'src/main.cpp',
            'src/utils.cpp',
            'include/config.hpp'
        ],
        deps=deps
    )
    return result

result = asyncio.run(test_real())
print(f'Analysis completed: {result.total_files} files')
"
```

#### Step 7.3: Monitor for Issues (24 hours)
```bash
# Run with logging enabled
python3 orchestrator_runner.py --log-level DEBUG --log-file orchestrator.log

# Monitor log file
tail -f orchestrator.log

# Check for errors
grep ERROR orchestrator.log
grep CRITICAL orchestrator.log

# Expected: No ERROR or CRITICAL logs
```

#### Step 7.4: Stress Test (1 week)
```bash
# Run continuous analysis (1 file every 5 minutes)
while true; do
    python3 run_analysis.py --random-file
    sleep 300
done

# Monitor memory usage
watch -n 60 'ps aux | grep python | grep orchestrator'

# Expected: Memory stable, no leaks
```

**Pass Criteria:**
- ✅ Works on real codebase
- ✅ No crashes over 24 hours
- ✅ No memory leaks over 1 week
- ✅ Performance acceptable (<5 min per file)
- ✅ No ERROR logs

**Red Flags:**
- ❌ Crashes on real code
- ❌ Memory growth >100MB/day
- ❌ Analysis fails frequently
- ❌ Performance degradation

---

## Test Results Template

Use this template to record test results:

```markdown
# Awareness Orchestrator Test Results

**Date:** YYYY-MM-DD
**Tester:** [Your Name]
**Environment:** [Development/Staging/Production]

## Phase 1: Environment Setup
- [ ] Python version: ___________
- [ ] Dependencies installed: ✅/❌
- [ ] sys.path clean: ✅/❌
- [ ] Status: PASS/FAIL

## Phase 2: Automated Tests
- [ ] Total tests: ___ passed, ___ skipped, ___ failed
- [ ] Critical tests: ___/8 passed
- [ ] High-priority tests: ___/6 passed
- [ ] Integration tests: ___/3 passed
- [ ] Coverage: ___%
- [ ] Status: PASS/FAIL

## Phase 3: Type Safety
- [ ] mypy errors (lenient): ___
- [ ] mypy errors (strict): ___
- [ ] Status: PASS/FAIL

## Phase 4: Code Quality Review
- [ ] No sys.path manipulation: ✅/❌
- [ ] No hard-coded paths: ✅/❌
- [ ] Error handling present: ✅/❌
- [ ] Logging configured: ✅/❌
- [ ] Status: PASS/FAIL

## Phase 5: Integration Testing
- [ ] Dependency creation: ✅/❌
- [ ] Configuration works: ✅/❌
- [ ] File validation works: ✅/❌
- [ ] Error handling works: ✅/❌
- [ ] Status: PASS/FAIL

## Phase 6: Performance Testing
- [ ] Memory growth: ___ MB (target: <1MB)
- [ ] Creation time: ___ ms (target: <10ms)
- [ ] Concurrent execution: ✅/❌
- [ ] Status: PASS/FAIL

## Phase 7: Production Validation
- [ ] Works on real codebase: ✅/❌
- [ ] 24h stability: ✅/❌
- [ ] 1 week stability: ✅/❌
- [ ] Memory leaks: ✅/❌
- [ ] Status: PASS/FAIL

## Overall Status
- [ ] **PRODUCTION READY** ✅
- [ ] **NEEDS FIXES** ⚠️
- [ ] **NOT READY** ❌

## Issues Found
[List any issues discovered during testing]

## Recommendations
[List recommendations for improvement]
```

---

## Troubleshooting Guide

### Issue: Tests fail with "Module not found"

**Symptom:**
```
ModuleNotFoundError: No module named 'awareness_orchestrator'
```

**Solution:**
```bash
# Ensure you're in the correct directory
cd /home/RIGG_dev/CLionProjects/RIGGWIRE-EA/.claude/agents/awareness_orchestrator

# Add parent directory to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/.claude/agents"

# Or install in development mode
pip install -e .
```

### Issue: sys.path pollution test fails

**Symptom:**
```
AssertionError: sys.path was modified by import!
```

**Solution:**
This indicates Fix #1 was not applied. Review `dependencies.py` lines 12-15:

```bash
grep -n "sys.path" awareness_orchestrator/dependencies.py

# If you see sys.path.insert, apply Fix #1 from PRIORITIZED_FIX_LIST.md
```

### Issue: Hard-coded path test fails

**Symptom:**
```
AssertionError: Hard-coded path still present!
```

**Solution:**
Apply Fix #2 from PRIORITIZED_FIX_LIST.md:

```bash
# Check for hard-coded paths
grep -n "/IdeaProjects/wire_ground" awareness_orchestrator/dependencies.py

# Replace with _detect_project_root()
```

### Issue: mypy reports many errors

**Symptom:**
```
agent.py:142: error: Function is missing a type annotation
```

**Solution:**
Apply Fix #13 from PRIORITIZED_FIX_LIST.md. Add type hints:

```python
# Before
def get_analysis_prompt(file_path, context):
    return f"Analyze {file_path}"

# After
def get_analysis_prompt(file_path: str, context: str = "") -> str:
    return f"Analyze {file_path}"
```

### Issue: Memory leak detected

**Symptom:**
```
Memory growth: 50MB for 100 iterations (expected: <1MB)
```

**Solution:**
Review Fix #7 (lazy initialization) and Fix #14 (graceful shutdown):

```python
# Ensure cleanup in __del__ methods
def __del__(self):
    if self.build_adapter:
        self.build_adapter.cleanup()
```

### Issue: Concurrent test hangs

**Symptom:**
```
Concurrent test never completes, hangs indefinitely
```

**Solution:**
Apply Fix #5 (async locks). Add proper locking:

```python
import asyncio

_agent_locks: Dict[str, asyncio.Lock] = {}

async with _agent_locks["analysis"]:
    # ... agent execution
```

---

## Production Deployment Checklist

Before deploying to production, verify:

### Pre-Deployment
- [ ] All automated tests pass (0 failures)
- [ ] mypy --strict reports <10 errors
- [ ] Code coverage >80%
- [ ] All critical fixes applied (Fix #1-8)
- [ ] All high-priority fixes applied (Fix #9-14)
- [ ] Logging configured for production
- [ ] Environment variables documented
- [ ] Configuration externalized
- [ ] Error handling comprehensive

### Deployment
- [ ] Deploy to staging first
- [ ] Run integration tests on staging
- [ ] Monitor for 24 hours on staging
- [ ] No errors in logs
- [ ] Performance acceptable
- [ ] Memory usage stable
- [ ] Rollback procedure documented
- [ ] Monitoring alerts configured

### Post-Deployment
- [ ] Monitor logs for errors
- [ ] Check memory usage daily
- [ ] Verify performance metrics
- [ ] Collect user feedback
- [ ] Run weekly test suite
- [ ] Update documentation

### Success Criteria
- ✅ 0 test failures
- ✅ 0 production crashes
- ✅ Memory stable (<50MB growth/week)
- ✅ Performance <5 min/file
- ✅ Error rate <1%

---

## Summary

**Testing Time Investment:**
- Environment setup: 5 min
- Automated tests: 10 min
- Type safety: 5 min
- Code review: 15 min
- Integration tests: 20 min
- Performance tests: 10 min
- **Total:** ~65 minutes

**Production Validation:**
- Staging deployment: 30 min
- 24h monitoring: 24 hours
- 1 week stress test: 1 week
- **Total:** ~1 week

**Value:**
- Prevents production crashes
- Ensures code quality
- Validates all fixes
- Provides confidence for deployment

**Next Steps:**
1. Run all testing phases
2. Document results
3. Apply any remaining fixes
4. Re-test until 100% pass
5. Deploy to staging
6. Monitor for 1 week
7. Deploy to production

---

**Ready for Production When:**
- ✅ All tests pass
- ✅ All critical fixes applied
- ✅ No memory leaks
- ✅ Performance acceptable
- ✅ 1 week stability proven

**Do not skip testing phases.** Each phase validates different aspects of the system.

---

*Testing completed: [DATE]*
*Production deployment: [APPROVED/NOT APPROVED]*
