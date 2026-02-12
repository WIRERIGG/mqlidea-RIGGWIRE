"""Test configuration and fixtures for never_fail_build_resolver.

This module provides comprehensive test fixtures for the never_fail_build_resolver
including mock services, TestModel integration, and performance benchmarking.
"""

import pytest
import asyncio
import tempfile
import json
import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Pydantic AI imports
from pydantic_ai.models.test import TestModel

# Import with proper module resolution
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Agent imports
try:
    from agent import NeverFailBuildResolver
    from dependencies import BuildResolverDependencies, create_dependencies
    from models import BuildSystem, ErrorType, BuildError, BuildConfig
    from tools import analyze_build_error, suggest_build_fixes, apply_build_fix
    from performance_benchmarks import AgentPerformanceBenchmark
except ImportError:
    # Fallback imports for testing
    NeverFailBuildResolver = None
    BuildResolverDependencies = None
    create_dependencies = lambda: None
    BuildSystem = None
    ErrorType = None
    BuildError = None
    BuildConfig = None
    analyze_build_error = lambda x, y, z: None
    suggest_build_fixes = lambda x, y, z: None
    apply_build_fix = lambda x, y, z: None
    AgentPerformanceBenchmark = None


# =============================================================================
# PYTEST CONFIGURATION
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom settings."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "build_systems: Build system specific tests")


def pytest_collection_modifyitems(config, items):
    """Mark tests based on their names and paths."""
    for item in items:
        # Auto-mark based on test name patterns
        if "unit" in item.name.lower() or "test_unit" in item.name:
            item.add_marker(pytest.mark.unit)
        if "integration" in item.name.lower() or "test_integration" in item.name:
            item.add_marker(pytest.mark.integration)
        if "performance" in item.name.lower() or "benchmark" in item.name:
            item.add_marker(pytest.mark.performance)
        if "cmake" in item.name.lower() or "make" in item.name.lower():
            item.add_marker(pytest.mark.build_systems)
        
        # Mark based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# =============================================================================
# CORE FIXTURES
# =============================================================================

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_project(temp_dir):
    """Create a test project structure."""
    project_root = temp_dir / "test_project"
    project_root.mkdir()
    
    # Create CMakeLists.txt
    cmake_content = '''
cmake_minimum_required(VERSION 3.16)
project(TestProject)
set(CMAKE_CXX_STANDARD 20)

add_executable(test_app main.cpp)
target_link_libraries(test_app pthread)
'''
    (project_root / "CMakeLists.txt").write_text(cmake_content)
    
    # Create main.cpp
    main_content = '''
#include <iostream>
#include <thread>

int main() {
    std::cout << "Hello World!" << std::endl;
    
    std::thread t([]() {
        std::cout << "Thread running" << std::endl;
    });
    
    t.join();
    return 0;
}
'''
    (project_root / "main.cpp").write_text(main_content)
    
    # Create Makefile as fallback
    makefile_content = '''
CXX = g++
CXXFLAGS = -std=c++20 -pthread
TARGET = test_app
SOURCES = main.cpp

$(TARGET): $(SOURCES)
\t$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCES)

clean:
\trm -f $(TARGET)

.PHONY: clean
'''
    (project_root / "Makefile").write_text(makefile_content)
    
    return project_root


@pytest.fixture
def broken_project(temp_dir):
    """Create a project with various build issues."""
    project_root = temp_dir / "broken_project"
    project_root.mkdir()
    
    # CMakeLists.txt with error
    cmake_content = '''
cmake_minimum_required(VERSION 3.16)
project(BrokenProject)
set(CMAKE_CXX_STANDARD 20)

# Missing source file reference
add_executable(broken_app missing_file.cpp)
'''
    (project_root / "CMakeLists.txt").write_text(cmake_content)
    
    # main.cpp with compilation errors
    main_content = '''
// Missing includes
int main() {
    std::cout << "This will fail" << std::endl;  // missing iostream
    std::vector<int> vec;  // missing vector
    
    // Undefined function
    undefined_function();
    
    return 0
}  // missing semicolon
'''
    (project_root / "main.cpp").write_text(main_content)
    
    return project_root


# =============================================================================
# PYDANTIC AI TEST MODEL FIXTURES
# =============================================================================

@pytest.fixture
def test_model():
    """Create a TestModel for mocking LLM responses."""
    return TestModel()


@pytest.fixture
def mock_agent_response():
    """Mock agent response for build resolution testing."""
    return {
        "analysis": {
            "error_type": "missing_source_file",
            "severity": "high",
            "missing_files": ["missing_file.cpp"],
            "build_system": "cmake"
        },
        "suggestions": [
            "Create the missing source file missing_file.cpp",
            "Update CMakeLists.txt to reference correct files",
            "Check file paths and naming conventions"
        ],
        "fix_strategy": {
            "priority": "high",
            "automated": True,
            "estimated_time": "2 minutes"
        }
    }


@pytest.fixture
def test_agent_with_mock(test_model, mock_agent_response):
    """Create agent with TestModel for controlled responses."""
    # Configure TestModel with expected responses
    test_model.add_response(json.dumps(mock_agent_response))
    
    # Create agent with test model
    from pydantic_ai import Agent
    agent = Agent(
        test_model,
        deps_type=BuildResolverDependencies,
        system_prompt="Test Never Fail Build Resolver agent"
    )
    
    # Register tools
    agent.tool(analyze_build_error)
    agent.tool(suggest_build_fixes)
    agent.tool(apply_build_fix)
    
    return agent


# =============================================================================
# BUILD SYSTEM FIXTURES
# =============================================================================

@pytest.fixture
def mock_cmake_output():
    """Mock CMake output for different scenarios."""
    return {
        'successful_config': {
            'returncode': 0,
            'stdout': '-- Configuring done\n-- Generating done\n-- Build files have been written',
            'stderr': ''
        },
        'missing_file': {
            'returncode': 1,
            'stdout': '',
            'stderr': 'CMake Error: Cannot find source file: missing_file.cpp'
        },
        'missing_cmake': {
            'returncode': 1,
            'stdout': '',
            'stderr': 'CMakeLists.txt not found'
        }
    }


@pytest.fixture
def mock_compiler_output():
    """Mock compiler output for different scenarios."""
    return {
        'successful_compile': {
            'returncode': 0,
            'stdout': '',
            'stderr': ''
        },
        'missing_include': {
            'returncode': 1,
            'stdout': '',
            'stderr': "main.cpp:5:5: error: 'cout' was not declared in this scope"
        },
        'syntax_error': {
            'returncode': 1,
            'stdout': '',
            'stderr': "main.cpp:10:5: error: expected ';' before '}' token"
        },
        'linker_error': {
            'returncode': 1,
            'stdout': '',
            'stderr': "undefined reference to 'pthread_create'"
        }
    }


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for build command execution."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


# =============================================================================
# DEPENDENCY FIXTURES
# =============================================================================

@pytest.fixture
def build_resolver_dependencies():
    """Create BuildResolverDependencies for testing."""
    return create_build_resolver_dependencies()


@pytest.fixture
def mock_build_resolver_dependencies():
    """Create mock BuildResolverDependencies."""
    deps = Mock(spec=BuildResolverDependencies)
    deps.project_root = Path("/test/project")
    deps.build_system = "cmake"
    deps.build_directory = Path("/test/project/build")
    deps.max_retry_attempts = 3
    deps.retry_delay = 1.0
    deps.enable_automatic_fixes = True
    deps.backup_enabled = True
    deps.safety_checks = True
    deps.build_timeout = 300
    deps.parallel_jobs = 4
    deps.compiler_path = "/usr/bin/gcc"
    deps.record_fix = Mock()
    deps.create_backup = Mock()
    deps.session_id = "test-session-123"
    return deps


# =============================================================================
# ERROR SCENARIO FIXTURES
# =============================================================================

@pytest.fixture
def build_error_scenarios():
    """Provide various build error scenarios for testing."""
    return {
        'cmake_missing_file': {
            'log': 'CMake Error at CMakeLists.txt:5 (add_executable): Cannot find source file: main.cpp',
            'type': 'missing_source_file',
            'severity': 'high'
        },
        'compiler_missing_include': {
            'log': "main.cpp:3:5: error: 'cout' was not declared in this scope",
            'type': 'missing_include',
            'severity': 'medium'
        },
        'linker_missing_library': {
            'log': '/usr/bin/ld: main.o: undefined reference to `pthread_create\'',
            'type': 'missing_library',
            'severity': 'high'
        },
        'syntax_error': {
            'log': "main.cpp:10:5: error: expected ';' before '}' token",
            'type': 'syntax_error',
            'severity': 'medium'
        },
        'permission_denied': {
            'log': 'Permission denied: cannot write to build directory',
            'type': 'permission_error',
            'severity': 'high'
        }
    }


@pytest.fixture
def build_fix_scenarios():
    """Provide various build fix scenarios for testing."""
    return {
        'create_missing_file': {
            'fix_type': 'create_missing_file',
            'file_path': '/test/project/main.cpp',
            'content': 'int main() { return 0; }',
            'success_expected': True
        },
        'add_include': {
            'fix_type': 'add_include',
            'file_path': '/test/project/main.cpp',
            'include_directive': '#include <iostream>',
            'success_expected': True
        },
        'link_library': {
            'fix_type': 'add_library_link',
            'cmake_file': '/test/project/CMakeLists.txt',
            'library': 'pthread',
            'target': 'test_app',
            'success_expected': True
        },
        'fix_permission': {
            'fix_type': 'fix_permissions',
            'path': '/test/project/build',
            'permissions': 0o755,
            'success_expected': True
        }
    }


# =============================================================================
# PERFORMANCE FIXTURES
# =============================================================================

@pytest.fixture
def performance_benchmark():
    """Create performance benchmark for testing."""
    benchmark = AgentPerformanceBenchmark("never_fail_build_resolver")
    
    # Set appropriate thresholds for build operations
    benchmark.set_threshold('max_execution_time', 10.0)  # Build analysis should be fast
    benchmark.set_threshold('max_memory_usage', 200.0)
    benchmark.set_threshold('max_cpu_percent', 80.0)
    
    return benchmark


@pytest.fixture
def build_performance_metrics():
    """Provide build performance metrics for testing."""
    return {
        'cmake_configure': {
            'baseline_time': 5.0,
            'optimized_time': 2.5,
            'improvement_factor': 2.0
        },
        'build_analysis': {
            'baseline_time': 3.0,
            'optimized_time': 1.0,
            'improvement_factor': 3.0
        },
        'fix_application': {
            'baseline_time': 2.0,
            'optimized_time': 0.5,
            'improvement_factor': 4.0
        }
    }


# =============================================================================
# INTEGRATION TEST FIXTURES
# =============================================================================

@pytest.fixture
def integration_test_environment(temp_dir):
    """Create complete test environment for integration testing."""
    env_root = temp_dir / "integration_env"
    env_root.mkdir()
    
    # Create multiple test projects
    projects = ["simple_project", "complex_project", "broken_project"]
    
    for project_name in projects:
        project_dir = env_root / project_name
        project_dir.mkdir()
        
        if project_name == "simple_project":
            # Simple working project
            (project_dir / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.16)
project(SimpleProject)
add_executable(simple main.cpp)
""")
            (project_dir / "main.cpp").write_text("""
#include <iostream>
int main() {
    std::cout << "Simple project" << std::endl;
    return 0;
}
""")
        elif project_name == "complex_project":
            # Complex project with dependencies
            (project_dir / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.16)
project(ComplexProject)
set(CMAKE_CXX_STANDARD 20)

find_package(Threads REQUIRED)
add_executable(complex main.cpp utils.cpp)
target_link_libraries(complex Threads::Threads)
""")
            (project_dir / "main.cpp").write_text("""
#include <iostream>
#include <thread>
#include "utils.h"

int main() {
    std::thread t(utility_function);
    t.join();
    return 0;
}
""")
            (project_dir / "utils.cpp").write_text("""
#include <iostream>
#include "utils.h"

void utility_function() {
    std::cout << "Utility function" << std::endl;
}
""")
            (project_dir / "utils.h").write_text("""
#ifndef UTILS_H
#define UTILS_H
void utility_function();
#endif
""")
        else:  # broken_project
            # Project with intentional errors
            (project_dir / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.16)
project(BrokenProject)
add_executable(broken nonexistent.cpp)
""")
            (project_dir / "main.cpp").write_text("""
// This file exists but CMakeLists.txt references nonexistent.cpp
int main() {
    return 0;
}
""")
    
    return env_root


# =============================================================================
# MOCK FIXTURES
# =============================================================================

@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.is_file') as mock_is_file, \
         patch('pathlib.Path.read_text') as mock_read, \
         patch('pathlib.Path.write_text') as mock_write:
        
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_read.return_value = "Mock file content"
        
        yield {
            'exists': mock_exists,
            'is_file': mock_is_file,
            'read_text': mock_read,
            'write_text': mock_write
        }


@pytest.fixture
def mock_git_operations():
    """Mock Git operations for backup and versioning."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = Mock(
            returncode=0,
            stdout="mock git output",
            stderr=""
        )
        yield mock_run


# =============================================================================
# CUSTOM ASSERTIONS
# =============================================================================

class BuildResolverAssertions:
    """Custom assertions for build resolver testing."""
    
    @staticmethod
    def assert_build_success(result: Dict):
        """Assert that build operation was successful."""
        assert result.get("success") is True
        assert result.get("exit_code") == 0
    
    @staticmethod
    def assert_error_detected(analysis: Dict, error_type: str):
        """Assert that specific error type was detected."""
        assert analysis.get("error_type") == error_type
        assert analysis.get("severity") in ["low", "medium", "high", "critical"]
    
    @staticmethod
    def assert_fix_applied(result: Dict, fix_type: str):
        """Assert that specific fix was applied successfully."""
        assert result.get("success") is True
        assert fix_type in str(result.get("description", "")).lower()
    
    @staticmethod
    def assert_backup_created(result: Dict):
        """Assert that backup was created successfully."""
        assert result.get("success") is True
        assert len(result.get("backed_up_files", [])) > 0


@pytest.fixture
def build_resolver_assertions():
    """Provide custom build resolver assertions."""
    return BuildResolverAssertions()


# =============================================================================
# SESSION FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def build_resolution_baselines():
    """Load build resolution baselines for regression testing."""
    return {
        'cmake_analysis': {'max_time': 5.0, 'max_memory': 100.0},
        'make_analysis': {'max_time': 3.0, 'max_memory': 50.0},
        'fix_application': {'max_time': 2.0, 'max_memory': 30.0},
        'build_validation': {'max_time': 10.0, 'max_memory': 150.0},
        'agent_initialization': {'max_time': 1.0, 'max_memory': 50.0}
    }


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up global test environment."""
    # Set test environment variables
    import os
    os.environ['LLM_PROVIDER'] = 'test'
    os.environ['LLM_MODEL'] = 'test-model'
    os.environ['BUILD_RESOLVER_TESTING'] = 'true'
    os.environ['NO_INTERACTIVE'] = 'true'
    
    yield
    
    # Cleanup
    os.environ.pop('LLM_PROVIDER', None)
    os.environ.pop('LLM_MODEL', None)
    os.environ.pop('BUILD_RESOLVER_TESTING', None)
    os.environ.pop('NO_INTERACTIVE', None)


# =============================================================================
# UTILITY FIXTURES
# =============================================================================

@pytest.fixture
def capture_logs():
    """Capture log output for testing."""
    import logging
    import io
    
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    logger = logging.getLogger('never_fail_build_resolver')
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    
    yield log_capture
    
    logger.removeHandler(handler)


@pytest.fixture
def timeout_context():
    """Provide timeout context for long-running tests."""
    import asyncio
    
    async def with_timeout(coro, timeout_seconds=30):
        """Run coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_seconds)
        except asyncio.TimeoutError:
            pytest.fail(f"Test timed out after {timeout_seconds} seconds")
    
    return with_timeout