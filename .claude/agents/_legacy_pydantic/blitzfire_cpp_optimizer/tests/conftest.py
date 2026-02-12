"""Test configuration for BLITZFIRE C++ Optimizer Agent."""

import pytest
import asyncio
import sys
from pathlib import Path

# Add the parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent import agent, get_dependencies, TestModel, FunctionModel
from models import OptimizationRequest, OptimizationLevel, OptimizationDomain

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def deps():
    """Create test dependencies."""
    dependencies = await get_dependencies()
    yield dependencies
    await dependencies.cleanup()

@pytest.fixture
def test_agent():
    """Get the BLITZFIRE agent for testing."""
    return agent

@pytest.fixture
def test_model():
    """Get TestModel instance."""
    return TestModel

@pytest.fixture  
def function_model():
    """Get FunctionModel instance."""
    return FunctionModel

@pytest.fixture
def sample_cpp_code():
    """Sample C++ code for testing."""
    return """
#include <iostream>
#include <vector>

int main() {
    std::vector<int> data = {1, 2, 3, 4, 5};
    for (auto item : data) {
        std::cout << item << std::endl;
    }
    return 0;
}
"""

@pytest.fixture
def optimization_request():
    """Create a sample optimization request."""
    return OptimizationRequest(
        code="""
#include <iostream>
#include <vector>

void inefficient_loop(std::vector<float>& data) {
    for (size_t i = 0; i < data.size(); ++i) {
        for (size_t j = 0; j < data.size(); ++j) {
            data[i] += data[j] * 2.0f;
        }
        std::cout << data[i] << std::endl;
    }
}

int main() {
    std::vector<float> numbers(1000, 1.0f);
    inefficient_loop(numbers);
    return 0;
}
""",
        optimization_level=OptimizationLevel.ADVANCED,
        focus_domains=[OptimizationDomain.SIMD, OptimizationDomain.ALGORITHMIC],
        safety_mode=True,
        wire_ground_integration=True,
        benchmark_generation=True
    )