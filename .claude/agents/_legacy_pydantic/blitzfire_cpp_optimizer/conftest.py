"""Configuration for BLITZFIRE C++ Optimizer tests with comprehensive coverage."""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def blitzfire_agent():
    """Mock BLITZFIRE agent for testing."""
    mock_agent = Mock()
    mock_agent._tools = {
        'analyze_cpp_performance': Mock(),
        'optimize_cpp_code': Mock(),
        'generate_performance_benchmark': Mock(),
        'validate_optimization_safety': Mock(),
        'query_optimization_knowledge': Mock(),
        'generate_cmake_integration': Mock(),
        'simd_vectorization_analysis': Mock(),
        'cache_optimization_analysis': Mock(),
        'algorithmic_complexity_analysis': Mock(),
        'io_performance_analysis': Mock(),
        'compiler_optimization_analysis': Mock(),
        'memory_safety_validation': Mock(),
        'thread_safety_validation': Mock(),
        'wire_ground_integration': Mock()
    }
    return mock_agent

@pytest.fixture
def blitzfire_dependencies():
    """Mock dependencies for BLITZFIRE testing."""
    mock_deps = Mock()
    mock_deps.session_id = "test_session"
    mock_deps.settings = {"optimization_level": "advanced", "safety_mode": True}
    mock_deps.config = {"compiler": "clang++", "target_cpu": "native"}
    mock_deps.initialized = True
    mock_deps.archon_available = False
    return mock_deps

# Add deps fixture for the failing test
@pytest.fixture  
def deps():
    """Dependencies fixture for agent tests."""
    from dependencies import BlitzfireDependencies
    return BlitzfireDependencies()

@pytest.fixture
def sample_cpp_code():
    """Sample C++ code for testing optimization."""
    return """
#include <iostream>
#include <vector>
#include <algorithm>

void inefficient_function(std::vector<int>& data) {
    // O(n²) bubble sort - algorithmic optimization opportunity
    for (size_t i = 0; i < data.size(); ++i) {
        for (size_t j = i + 1; j < data.size(); ++j) {
            if (data[i] > data[j]) {
                std::swap(data[i], data[j]);
            }
        }
    }
    
    // Inefficient I/O - I/O optimization opportunity
    for (const auto& item : data) {
        std::cout << item << std::endl;  // Forces buffer flush
    }
}

void vector_operations(const std::vector<float>& a, 
                      const std::vector<float>& b, 
                      std::vector<float>& result) {
    // Scalar operations - SIMD optimization opportunity
    for (size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] + b[i] * 2.0f;
    }
}

struct Point {  // Cache optimization opportunity - convert to SoA
    float x, y, z;
    int id;
};

void process_points(std::vector<Point>& points) {
    for (auto& point : points) {
        float distance = point.x * point.x + point.y * point.y + point.z * point.z;
        point.id = static_cast<int>(distance);
    }
}

int main() {
    std::vector<int> numbers = {64, 34, 25, 12, 22, 11, 90};
    inefficient_function(numbers);
    
    std::vector<float> a(1000, 1.0f), b(1000, 2.0f), result(1000);
    vector_operations(a, b, result);
    
    std::vector<Point> points(1000);
    process_points(points);
    
    return 0;
}
"""

@pytest.fixture
def optimization_scenarios():
    """Various C++ optimization scenarios for comprehensive testing."""
    return {
        "simd_candidate": """
float dot_product(const float* a, const float* b, size_t n) {
    float sum = 0.0f;
    for (size_t i = 0; i < n; ++i) {
        sum += a[i] * b[i];
    }
    return sum;
}
""",
        "cache_unfriendly": """
struct Data { float value; int metadata[100]; };
std::vector<Data> dataset(10000);
for (const auto& item : dataset) {
    process(item.value);  // Poor cache locality
}
""",
        "io_heavy": """
for (int i = 0; i < 1000; ++i) {
    std::cout << "Value " << i << ": " << data[i] << std::endl;
    std::cout << "Square: " << data[i] * data[i] << std::endl;
}
""",
        "algorithmic_bottleneck": """
bool contains(const std::vector<int>& vec, int target) {
    for (const auto& item : vec) {
        if (item == target) return true;
    }
    return false;  // O(n) linear search - use hash table
}
"""
    }

@pytest.fixture
def security_test_cases():
    """Security test cases for comprehensive validation."""
    return {
        "buffer_overflow": """
char buffer[10];
strcpy(buffer, user_input);  // Dangerous - no bounds checking
""",
        "command_injection": """
std::string cmd = "ls " + user_input;
system(cmd.c_str());  // Command injection vulnerability
""",
        "path_traversal": """
std::ifstream file("data/" + user_filename);  // Path traversal risk
""",
        "sql_injection": """
std::string query = "SELECT * FROM users WHERE name = '" + user_name + "'";
""",
        "format_string": """
printf(user_input);  // Format string vulnerability
"""
    }

@pytest.fixture
def performance_expectations():
    """Expected performance improvements for different optimization types."""
    return {
        "simd_vectorization": {"min_speedup": 2.0, "max_speedup": 8.0},
        "cache_optimization": {"min_speedup": 1.5, "max_speedup": 10.0},
        "algorithmic_improvement": {"min_speedup": 10.0, "max_speedup": 1000.0},
        "io_buffering": {"min_speedup": 5.0, "max_speedup": 100.0},
        "compiler_optimization": {"min_speedup": 1.2, "max_speedup": 3.0}
    }

@pytest.fixture
def mock_system_calls():
    """Mock system calls for safe testing."""
    with patch('subprocess.run') as mock_run, \
         patch('os.system') as mock_system, \
         patch('os.path.exists') as mock_exists:
        
        mock_run.return_value = Mock(returncode=0, stdout="success", stderr="")
        mock_system.return_value = 0
        mock_exists.return_value = True
        
        yield {
            'subprocess_run': mock_run,
            'os_system': mock_system, 
            'path_exists': mock_exists
        }

@pytest.fixture
def coverage_tracking():
    """Enable comprehensive coverage tracking."""
    return {
        "target_coverage": 95.0,
        "critical_modules": [
            "agent", "tools", "models", "dependencies", 
            "settings", "providers", "cli", "prompts"
        ],
        "excluded_patterns": ["test_*", "conftest.py", "__pycache__"]
    }

# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with BLITZFIRE-specific settings."""
    config.addinivalue_line(
        "markers", "blitzfire: mark test as BLITZFIRE C++ optimizer specific"
    )
    config.addinivalue_line(
        "markers", "optimization: mark test as optimization-related"
    )
    config.addinivalue_line(
        "markers", "cpp_analysis: mark test as C++ analysis-related"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection for comprehensive validation."""
    for item in items:
        # Add markers based on test names
        if "security" in item.name.lower():
            item.add_marker(pytest.mark.security)
        if "performance" in item.name.lower():
            item.add_marker(pytest.mark.performance)
        if "async" in item.name.lower():
            item.add_marker(pytest.mark.asyncio)
        if "blitzfire" in item.name.lower():
            item.add_marker(pytest.mark.blitzfire)

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Automatically setup test environment for all tests."""
    # Ensure clean state for each test
    import os
    original_cwd = os.getcwd()
    yield
    os.chdir(original_cwd)  # Restore working directory