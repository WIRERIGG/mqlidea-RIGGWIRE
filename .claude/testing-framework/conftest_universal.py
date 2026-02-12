"""Universal Test Configuration for Pydantic AI Agents Testing Framework

This module provides shared fixtures and configuration for all four agents:
- valgrind_memory_ai_agent
- never_fail_build_resolver  
- blitzfire_cpp_optimizer
- clang_tidy_ai_agent

Usage:
    Copy this file to your agent's tests/ directory or import fixtures directly.
"""

import asyncio
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Any, Dict, Generator, AsyncGenerator
import pytest
import pytest_asyncio
import logging
from contextlib import asynccontextmanager

# Pydantic AI imports
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


# =============================================================================
# CORE FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_file(temp_dir: Path) -> Path:
    """Create temporary file for testing."""
    temp_file = temp_dir / "test_file.txt"
    temp_file.write_text("test content")
    return temp_file


@pytest.fixture
def test_project_root(temp_dir: Path) -> Path:
    """Create mock project root directory structure."""
    project_root = temp_dir / "test_project"
    project_root.mkdir()
    
    # Create common project structure
    (project_root / "src").mkdir()
    (project_root / "include").mkdir()
    (project_root / "tests").mkdir()
    (project_root / "build").mkdir()
    
    # Create CMakeLists.txt
    (project_root / "CMakeLists.txt").write_text("""
cmake_minimum_required(VERSION 3.16)
project(test_project)
set(CMAKE_CXX_STANDARD 17)
add_executable(test_app src/main.cpp)
""")
    
    # Create sample C++ file
    (project_root / "src" / "main.cpp").write_text("""
#include <iostream>
int main() {
    std::cout << "Hello World" << std::endl;
    return 0;
}
""")
    
    return project_root


# =============================================================================
# PYDANTIC AI TEST MODEL FIXTURES
# =============================================================================

@pytest.fixture
def test_model() -> TestModel:
    """Create TestModel for mocking LLM responses."""
    return TestModel()


@pytest.fixture
def test_agent_basic(test_model: TestModel) -> Agent:
    """Create basic test agent with TestModel."""
    return Agent(test_model, system_prompt="You are a test assistant.")


@pytest.fixture
def mock_llm_response() -> str:
    """Standard mock LLM response for testing."""
    return "This is a mock response for testing purposes."


@pytest.fixture
def mock_structured_response() -> Dict[str, Any]:
    """Mock structured response for testing."""
    return {
        "success": True,
        "analysis": "Mock analysis result",
        "recommendations": ["recommendation1", "recommendation2"],
        "severity": "medium",
        "confidence": 0.85
    }


# =============================================================================
# DATABASE FIXTURES  
# =============================================================================

@pytest.fixture
def test_db(temp_dir: Path) -> Generator[sqlite3.Connection, None, None]:
    """Create test database connection."""
    db_path = temp_dir / "test.db"
    connection = sqlite3.connect(db_path)
    
    # Create common tables used by agents
    connection.executescript("""
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            file_path TEXT,
            analysis_type TEXT,
            results TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            preference_key TEXT,
            preference_value TEXT,
            context_tags TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS cache_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cache_key TEXT UNIQUE,
            cache_value TEXT,
            expires_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    connection.commit()
    yield connection
    connection.close()


# =============================================================================
# EXTERNAL TOOL MOCKS
# =============================================================================

@pytest.fixture
def mock_subprocess():
    """Mock subprocess for external tool calls."""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Mock stdout"
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture  
def mock_valgrind_output() -> str:
    """Mock Valgrind XML output for testing."""
    return """<?xml version="1.0"?>
<valgrindoutput>
<protocolversion>4</protocolversion>
<protocoltool>memcheck</protocoltool>
<preamble>
<line>Memcheck, a memory error detector</line>
</preamble>
<pid>12345</pid>
<ppid>12344</ppid>
<tool>memcheck</tool>

<error>
<unique>0x1</unique>
<tid>1</tid>
<kind>Leak_DefinitelyLost</kind>
<xwhat>
<text>40 bytes in 1 blocks are definitely lost in loss record 1 of 1</text>
<leakedbytes>40</leakedbytes>
<leakedblocks>1</leakedblocks>
</xwhat>
<stack>
<frame>
<ip>0x4C2FB55</ip>
<fn>malloc</fn>
</frame>
</stack>
</error>

</valgrindoutput>"""


@pytest.fixture
def mock_clang_tidy_output() -> str:
    """Mock clang-tidy output for testing."""
    return """src/main.cpp:5:5: warning: variable 'x' is not used [-Wunused-variable]
    int x = 42;
    ^
src/main.cpp:10:1: error: expected ';' after class [clang-diagnostic-error]
class TestClass {
^
               ;
2 warnings and 1 error generated.
"""


@pytest.fixture
def mock_cmake_output() -> str:
    """Mock CMake build output for testing."""
    return """-- The C compiler identification is GNU 11.4.0
-- The CXX compiler identification is GNU 11.4.0
-- Detecting C compiler ABI info - done
-- Detecting CXX compiler ABI info - done
-- Configuring done
-- Generating done
-- Build files have been written to: /path/to/build
"""


# =============================================================================
# PERFORMANCE TESTING FIXTURES
# =============================================================================

@pytest.fixture
def performance_baseline() -> Dict[str, float]:
    """Performance baseline metrics for regression testing."""
    return {
        "max_execution_time": 1.0,  # seconds
        "max_memory_usage": 100.0,  # MB
        "max_cpu_percent": 80.0,    # percentage
        "api_calls_per_minute": 60  # rate limit
    }


@pytest.fixture
def benchmark_timer():
    """Timer for performance benchmarking."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
        
        @property
        def elapsed(self) -> float:
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0.0
    
    return Timer()


# =============================================================================
# LOGGING AND ERROR HANDLING
# =============================================================================

@pytest.fixture
def caplog_setup(caplog):
    """Setup logging capture for tests."""
    caplog.set_level(logging.INFO)
    return caplog


@pytest.fixture
def mock_logger():
    """Mock logger for testing logging behavior."""
    return Mock(spec=logging.Logger)


# =============================================================================
# FILE SYSTEM MOCKS
# =============================================================================

@pytest.fixture
def mock_file_system():
    """Mock file system operations."""
    with patch('pathlib.Path.exists') as mock_exists, \
         patch('pathlib.Path.is_file') as mock_is_file, \
         patch('pathlib.Path.is_dir') as mock_is_dir, \
         patch('pathlib.Path.read_text') as mock_read_text, \
         patch('pathlib.Path.write_text') as mock_write_text:
        
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_is_dir.return_value = True
        mock_read_text.return_value = "mock file content"
        
        yield {
            'exists': mock_exists,
            'is_file': mock_is_file, 
            'is_dir': mock_is_dir,
            'read_text': mock_read_text,
            'write_text': mock_write_text
        }


# =============================================================================
# AGENT-SPECIFIC FIXTURES (to be customized per agent)
# =============================================================================

@pytest.fixture
def mock_agent_settings():
    """Mock agent settings - customize per agent."""
    return {
        'llm_provider': 'test',
        'llm_api_key': 'test-key',
        'llm_model': 'test-model',
        'llm_base_url': 'http://test.local',
        'project_root': '/test/project',
        'enable_learning_mode': True,
        'cache_analysis_results': False
    }


@pytest.fixture
def mock_external_dependencies():
    """Mock external dependencies - customize per agent."""
    mocks = {}
    
    # Mock common external tools
    with patch('subprocess.Popen') as mock_popen:
        mock_process = Mock()
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        mocks['popen'] = mock_popen
        
        yield mocks


# =============================================================================
# ASYNC FIXTURES
# =============================================================================

@pytest_asyncio.fixture
async def async_test_agent(test_model: TestModel) -> Agent:
    """Create async test agent."""
    return Agent(test_model, system_prompt="Async test assistant")


@pytest_asyncio.fixture
async def async_mock_response():
    """Async mock response."""
    await asyncio.sleep(0.01)  # Simulate async operation
    return "Async mock response"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_test_files(base_path: Path, file_structure: Dict[str, str]):
    """Helper to create test file structure.
    
    Args:
        base_path: Base directory path
        file_structure: Dict mapping file paths to content
    """
    for file_path, content in file_structure.items():
        full_path = base_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)


def assert_performance_within_limits(
    actual_time: float,
    baseline: Dict[str, float],
    tolerance_percent: float = 20.0
):
    """Helper to assert performance is within acceptable limits.
    
    Args:
        actual_time: Measured execution time
        baseline: Performance baseline metrics
        tolerance_percent: Acceptable deviation percentage
    """
    max_allowed = baseline['max_execution_time'] * (1 + tolerance_percent / 100)
    assert actual_time <= max_allowed, f"Performance regression: {actual_time}s > {max_allowed}s"


# =============================================================================
# PARAMETRIZED FIXTURES FOR CROSS-AGENT TESTING
# =============================================================================

@pytest.fixture(params=[
    'valgrind_memory_ai_agent',
    'never_fail_build_resolver', 
    'blitzfire_cpp_optimizer',
    'clang_tidy_ai_agent'
])
def agent_type(request):
    """Parametrized fixture for testing across all agent types."""
    return request.param


@pytest.fixture(params=['sqlite', 'memory'])
def database_type(request, temp_dir):
    """Parametrized fixture for different database configurations."""
    if request.param == 'sqlite':
        return temp_dir / "test.db"
    else:
        return ":memory:"