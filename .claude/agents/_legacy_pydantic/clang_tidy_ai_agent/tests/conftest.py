"""Test configuration for the Clang-Tidy AI Agent tests."""

import pytest
import pytest_asyncio
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from dependencies import create_test_dependencies
    from models import ClangTidyDependencies, IssueDiscoveryResponse
    
    # Test imports successful
    IMPORTS_SUCCESSFUL = True
    
except ImportError:
    # Create mock classes for fallback
    IMPORTS_SUCCESSFUL = False
    
    def create_test_dependencies():
        return Mock()
    
    class ClangTidyDependencies:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
    
    class IssueDiscoveryResponse:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


@pytest.fixture
def temp_dir():
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_dependencies():
    """Create test dependencies."""
    if not IMPORTS_SUCCESSFUL:
        return Mock()
    return create_test_dependencies()


@pytest.fixture
def sample_cpp_file(temp_dir):
    """Create a sample C++ file for testing."""
    cpp_content = """
#include <iostream>
#include <string>

int main() {
    int myVar = 42;  // naming convention issue
    std::string myString = "hello";  // another naming issue
    
    for (int i = 0; i < 10; ++i) {
        std::cout << myVar + i << std::endl;  // performance issue: avoid endl
    }
    
    return 0;
}
"""
    
    cpp_file = temp_dir / "src" / "test.cpp"
    cpp_file.parent.mkdir(parents=True)
    cpp_file.write_text(cpp_content)
    return cpp_file


@pytest.fixture
def mock_clang_tidy_output():
    """Mock clang-tidy command output."""
    stderr_output = """
src/test.cpp:5:9: warning: variable name 'myVar' doesn't follow naming convention [readability-identifier-naming]
    int myVar = 42;
        ^~~~~
        my_var
src/test.cpp:6:17: warning: variable name 'myString' doesn't follow naming convention [readability-identifier-naming]  
    std::string myString = "hello";
                ^~~~~~~~
                my_string
src/test.cpp:9:36: warning: use '\\n' instead of std::endl for performance [performance-avoid-endl]
        std::cout << myVar + i << std::endl;
                                  ^~~~~~~~~
                                  '\\n'
"""
    return "", stderr_output, 0


@pytest.fixture
def mock_subprocess_run(mock_clang_tidy_output):
    """Mock subprocess.run for clang-tidy execution."""
    stdout, stderr, returncode = mock_clang_tidy_output
    
    mock_result = Mock()
    mock_result.stdout = stdout
    mock_result.stderr = stderr
    mock_result.returncode = returncode
    
    with patch('subprocess.run', return_value=mock_result) as mock_run:
        yield mock_run


@pytest.fixture
def integration_test_project(temp_dir):
    """Create a realistic test project structure."""
    project_root = temp_dir
    
    # Create directory structure
    (project_root / "src").mkdir()
    (project_root / "include").mkdir()
    (project_root / "tests").mkdir()
    
    # Create test files with various issues
    main_cpp = project_root / "src" / "main.cpp"
    main_cpp.write_text("""
#include <iostream>
#include <vector>
#include <string>

class TestClass {
private:
    int memberVar;  // naming issue
    std::vector<int> data;
    
public:
    TestClass() : memberVar(0) {}
    
    void processData() {
        for (int i = 0; i < 1000; ++i) {
            data.push_back(i);  // performance: should reserve
        }
        
        for (const auto& item : data) {
            std::cout << item << std::endl;  // performance: avoid endl
        }
    }
};

int main() {
    TestClass testObj;
    testObj.processData();
    return 0;
}
""")
    
    return project_root


# Cleanup fixtures
@pytest.fixture(autouse=True)
def cleanup_test_artifacts():
    """Automatically cleanup test artifacts after each test."""
    yield
    # Any cleanup code would go here
    pass