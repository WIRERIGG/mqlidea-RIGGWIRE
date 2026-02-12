"""Test configuration for Blitzfire Code Agent."""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock

from blitzfire_code_agent.settings import BlitzfireSettings
from blitzfire_code_agent.dependencies import BlitzfireDependencies
from blitzfire_code_agent.providers import get_test_model


@pytest.fixture
def sample_cpp_code():
    """Sample C++ code for testing."""
    return '''
#include <iostream>
#include <vector>
#include <string>

int main() {
    std::vector<int> numbers;
    for (int i = 0; i < 1000; i++) {
        numbers.push_back(i);  // Inefficient growth
    }

    std::string result = "";
    for (int i = 0; i < numbers.size(); i++) {
        result += std::to_string(numbers[i]);  // Inefficient concatenation
    }

    // Nested loops - O(n²)
    int sum = 0;
    for (int i = 0; i < numbers.size(); i++) {
        for (int j = 0; j < numbers.size(); j++) {
            sum += numbers[i] * numbers[j];
        }
    }

    std::cout << result << " Sum: " << sum << std::endl;
    return 0;
}
'''


@pytest.fixture
def hft_sample_code():
    """Sample HFT code with typical issues."""
    return '''
#include <queue>
#include <mutex>

struct Order {
    double price;
    int quantity;
    uint64_t timestamp;
};

std::queue<Order> order_queue;
std::mutex queue_mutex;
double current_price = 100.50;

void process_order(const Order& order) {
    if (order.price == current_price) {  // Dangerous equality
        std::lock_guard<std::mutex> lock(queue_mutex);
        current_price = order.price;  // Race condition potential
        order_queue.push(order);     // Blocking operation
    }
}

void update_price(double new_price) {
    current_price += new_price * 0.01;  // Potential overflow
}

int calculate_position(int base, int multiplier) {
    return base * multiplier;  // Unchecked multiplication
}
'''


@pytest.fixture
def test_settings():
    """Test settings with mocked external services."""
    return BlitzfireSettings(
        llm_provider="test",
        llm_api_key="test-key",
        llm_model="test-model",
        godbolt_base_url="http://test-godbolt",
        docker_enabled=False,  # Disable Docker for tests
        project_root="/tmp/test_project",
        blitzfire_mode="general"
    )


@pytest.fixture
def mock_dependencies(test_settings):
    """Mock dependencies for testing."""
    deps = BlitzfireDependencies.create(test_settings, "test_session")

    # Mock external services
    deps.godbolt_session = Mock()
    deps.docker_client = None  # Disable Docker for tests

    return deps


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir)

        # Create project structure
        (project_path / "src").mkdir()
        (project_path / "include").mkdir()
        (project_path / "tests").mkdir()

        # Create sample files
        with open(project_path / "src" / "main.cpp", "w") as f:
            f.write('''
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
''')

        with open(project_path / "include" / "math_utils.hpp", "w") as f:
            f.write('''
#pragma once

class MathUtils {
public:
    static int add(int a, int b) {
        return a + b;
    }

    static double multiply_matrix_element(double a, double b) {
        return a * b;
    }
};
''')

        yield project_path


@pytest.fixture
def test_model():
    """Get test model for agent testing."""
    return get_test_model()


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# Test data fixtures
@pytest.fixture
def optimization_test_cases():
    """Various code snippets for optimization testing."""
    return {
        "string_concatenation": '''
std::string build_message(const std::vector<std::string>& words) {
    std::string message = "";
    for (const auto& word : words) {
        message += word + " ";
    }
    return message;
}
''',

        "vector_growth": '''
std::vector<int> generate_sequence(int n) {
    std::vector<int> sequence;
    for (int i = 0; i < n; i++) {
        sequence.push_back(i * i);
    }
    return sequence;
}
''',

        "nested_loops": '''
void matrix_multiply(const std::vector<std::vector<double>>& A,
                    const std::vector<std::vector<double>>& B,
                    std::vector<std::vector<double>>& C) {
    for (int i = 0; i < A.size(); i++) {
        for (int j = 0; j < B[0].size(); j++) {
            for (int k = 0; k < A[0].size(); k++) {
                C[i][j] += A[i][k] * B[k][j];
            }
        }
    }
}
''',

        "simd_candidate": '''
void vector_add(const std::vector<float>& a,
               const std::vector<float>& b,
               std::vector<float>& result) {
    for (size_t i = 0; i < a.size(); i++) {
        result[i] = a[i] + b[i];
    }
}
'''
    }


@pytest.fixture
def expected_analysis_results():
    """Expected results for test cases."""
    return {
        "string_concatenation": {
            "issues_expected": 1,
            "complexity": "O(n)",
            "optimization_candidates": ["Use stringstream for string concatenation"]
        },

        "vector_growth": {
            "issues_expected": 1,
            "complexity": "O(n)",
            "optimization_candidates": ["Reserve vector capacity before push_back operations"]
        },

        "nested_loops": {
            "issues_expected": 0,  # No specific issues, but optimization opportunities
            "complexity": "O(n³)",
            "optimization_candidates": ["Consider loop interchange or blocking for cache efficiency"]
        },

        "simd_candidate": {
            "issues_expected": 0,
            "complexity": "O(n)",
            "optimization_candidates": ["Consider SIMD vectorization for floating-point operations"]
        }
    }


# Mock external service responses
@pytest.fixture
def mock_godbolt_response():
    """Mock Godbolt API response."""
    return {
        "asm": [
            {"text": "    movq    %rdi, %rax"},
            {"text": "    addq    %rsi, %rax"},
            {"text": "    ret"}
        ],
        "stdout": [],
        "stderr": [],
        "code": 0,
        "okToCache": True,
        "execTime": "0.1s"
    }


@pytest.fixture
def mock_benchmark_results():
    """Mock benchmark results."""
    return [
        {
            "function_name": "baseline_function",
            "input_size": 1000,
            "mean_time_ns": 1000000,
            "std_dev_ns": 50000,
            "iterations": 1000,
            "speedup_ratio": 1.0
        },
        {
            "function_name": "optimized_function",
            "input_size": 1000,
            "mean_time_ns": 400000,
            "std_dev_ns": 20000,
            "iterations": 1000,
            "speedup_ratio": 2.5
        }
    ]