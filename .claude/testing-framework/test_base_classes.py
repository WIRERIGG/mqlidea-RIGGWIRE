"""Universal Base Test Classes for Pydantic AI Agents

This module provides base test classes that all agents can inherit from,
ensuring consistent testing patterns and reducing code duplication.

Usage:
    class TestMyAgent(BaseAgentTest):
        def setup_agent_specific_fixtures(self):
            # Agent-specific setup
            pass
"""

import asyncio
import time
import pytest
import pytest_asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List, Optional, Type
from unittest.mock import Mock, AsyncMock, patch

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel


class BaseAgentTest(ABC):
    """Base class for all agent tests."""
    
    @abstractmethod
    def setup_agent_specific_fixtures(self):
        """Setup agent-specific test fixtures. Override in subclass."""
        pass
    
    def setup_method(self, method):
        """Setup for each test method."""
        self.setup_agent_specific_fixtures()
    
    def teardown_method(self, method):
        """Cleanup after each test method."""
        pass


class BaseUnitTest(BaseAgentTest):
    """Base class for unit tests."""
    
    def test_imports(self):
        """Test that all required modules can be imported."""
        # Override in subclass with agent-specific imports
        pass
    
    def test_basic_instantiation(self):
        """Test basic class instantiation."""
        # Override in subclass
        pass


class BaseIntegrationTest(BaseAgentTest):
    """Base class for integration tests."""
    
    def setup_agent_specific_fixtures(self):
        """Default integration test setup."""
        super().setup_agent_specific_fixtures()
        self.test_model = TestModel()
        self.mock_responses = []
    
    @pytest_asyncio.fixture
    async def integration_agent(self) -> Agent:
        """Create agent for integration testing."""
        return Agent(self.test_model, system_prompt="Integration test agent")
    
    def add_mock_response(self, response: str):
        """Add a mock response to the test model."""
        self.mock_responses.append(response)
    
    async def run_agent_with_mocks(self, agent: Agent, prompt: str) -> Any:
        """Run agent with predefined mock responses."""
        # Set up mock responses in TestModel
        for response in self.mock_responses:
            agent.model.add_response(response)
        
        result = await agent.run(prompt)
        return result


class BasePerformanceTest(BaseAgentTest):
    """Base class for performance tests."""
    
    def setup_agent_specific_fixtures(self):
        """Setup performance testing fixtures."""
        super().setup_agent_specific_fixtures()
        self.performance_baseline = {
            'max_execution_time': 1.0,
            'max_memory_usage': 100.0,
            'max_cpu_percent': 80.0
        }
        self.tolerance_percent = 20.0
    
    def measure_execution_time(self, func, *args, **kwargs):
        """Measure function execution time."""
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    async def measure_async_execution_time(self, func, *args, **kwargs):
        """Measure async function execution time."""
        start_time = time.time()
        result = await func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    def assert_performance_within_limits(self, actual_time: float, operation: str = 'default'):
        """Assert performance is within acceptable limits."""
        max_allowed = self.performance_baseline['max_execution_time'] * (1 + self.tolerance_percent / 100)
        assert actual_time <= max_allowed, \
            f"Performance regression in {operation}: {actual_time:.3f}s > {max_allowed:.3f}s"
    
    @pytest.mark.performance
    def test_basic_operation_performance(self):
        """Test basic operation performance. Override in subclass."""
        pass


class BaseEndToEndTest(BaseAgentTest):
    """Base class for end-to-end tests."""
    
    def setup_agent_specific_fixtures(self):
        """Setup E2E test environment."""
        super().setup_agent_specific_fixtures()
        self.test_scenarios = []
        self.expected_outcomes = []
    
    def add_test_scenario(self, scenario: Dict[str, Any], expected_outcome: Any):
        """Add test scenario with expected outcome."""
        self.test_scenarios.append(scenario)
        self.expected_outcomes.append(expected_outcome)
    
    @pytest.mark.e2e
    def test_complete_workflow(self):
        """Test complete agent workflow. Override in subclass."""
        pass


class BaseMockingTest(BaseAgentTest):
    """Base class for tests that heavily use mocking."""
    
    def setup_agent_specific_fixtures(self):
        """Setup mocking infrastructure."""
        super().setup_agent_specific_fixtures()
        self.mocks = {}
        self.patches = {}
    
    def add_mock(self, name: str, mock_obj: Mock):
        """Add a named mock object."""
        self.mocks[name] = mock_obj
    
    def get_mock(self, name: str) -> Mock:
        """Get a named mock object."""
        return self.mocks.get(name)
    
    def patch_method(self, target: str, mock_obj: Mock = None):
        """Patch a method and store the patcher."""
        if mock_obj is None:
            mock_obj = Mock()
        
        patcher = patch(target, mock_obj)
        self.patches[target] = patcher
        return patcher.start()
    
    def teardown_method(self, method):
        """Stop all patches."""
        for patcher in self.patches.values():
            patcher.stop()
        self.patches.clear()
        super().teardown_method(method)


class BaseTestModelTest(BaseAgentTest):
    """Base class for tests using Pydantic AI TestModel."""
    
    def setup_agent_specific_fixtures(self):
        """Setup TestModel infrastructure."""
        super().setup_agent_specific_fixtures()
        self.test_model = TestModel()
        self.agent = Agent(self.test_model, system_prompt="Test assistant")
    
    def set_mock_response(self, response: str):
        """Set a single mock response."""
        # Clear previous responses
        self.test_model = TestModel()
        self.agent = Agent(self.test_model, system_prompt="Test assistant")
        # Add the response (implementation depends on TestModel API)
        pass  # TODO: Implement based on actual TestModel API
    
    def set_mock_responses(self, responses: List[str]):
        """Set multiple mock responses in order."""
        # Clear previous responses
        self.test_model = TestModel()
        self.agent = Agent(self.test_model, system_prompt="Test assistant")
        # Add responses (implementation depends on TestModel API)
        pass  # TODO: Implement based on actual TestModel API
    
    async def run_with_mock_response(self, prompt: str, expected_response: str) -> Any:
        """Run agent with a specific mock response."""
        self.set_mock_response(expected_response)
        result = await self.agent.run(prompt)
        return result
    
    def assert_model_called_with(self, expected_prompt: str):
        """Assert the model was called with expected prompt."""
        # Implementation depends on TestModel API
        pass  # TODO: Implement based on actual TestModel API


class BaseFileSystemTest(BaseAgentTest):
    """Base class for tests involving file system operations."""
    
    def setup_agent_specific_fixtures(self):
        """Setup file system test fixtures."""
        super().setup_agent_specific_fixtures()
        self.test_files = {}
        self.temp_directories = []
    
    def create_test_file(self, temp_dir: Path, relative_path: str, content: str) -> Path:
        """Create a test file with content."""
        file_path = temp_dir / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.test_files[relative_path] = file_path
        return file_path
    
    def create_test_directory_structure(self, temp_dir: Path, structure: Dict[str, str]):
        """Create a directory structure with files.
        
        Args:
            temp_dir: Base temporary directory
            structure: Dict mapping file paths to content
        """
        for file_path, content in structure.items():
            self.create_test_file(temp_dir, file_path, content)
    
    def get_test_file(self, relative_path: str) -> Optional[Path]:
        """Get path to a created test file."""
        return self.test_files.get(relative_path)


class BaseAsyncTest(BaseAgentTest):
    """Base class for async-heavy tests."""
    
    def setup_agent_specific_fixtures(self):
        """Setup async test infrastructure."""
        super().setup_agent_specific_fixtures()
        self.event_loop = None
        self.async_mocks = {}
    
    def create_async_mock(self, name: str, return_value: Any = None) -> AsyncMock:
        """Create and store an async mock."""
        async_mock = AsyncMock(return_value=return_value)
        self.async_mocks[name] = async_mock
        return async_mock
    
    def get_async_mock(self, name: str) -> Optional[AsyncMock]:
        """Get a stored async mock."""
        return self.async_mocks.get(name)
    
    async def run_with_timeout(self, coro, timeout: float = 5.0):
        """Run coroutine with timeout."""
        return await asyncio.wait_for(coro, timeout=timeout)


class BaseErrorHandlingTest(BaseAgentTest):
    """Base class for error handling tests."""
    
    def setup_agent_specific_fixtures(self):
        """Setup error testing fixtures."""
        super().setup_agent_specific_fixtures()
        self.expected_errors = {}
        self.error_scenarios = []
    
    def add_error_scenario(self, scenario_name: str, exception_type: Type[Exception], 
                          trigger_condition: Any):
        """Add an error scenario to test."""
        self.error_scenarios.append({
            'name': scenario_name,
            'exception_type': exception_type,
            'trigger': trigger_condition
        })
    
    def assert_raises_expected_error(self, scenario_name: str, func, *args, **kwargs):
        """Assert that function raises expected error for scenario."""
        scenario = next((s for s in self.error_scenarios if s['name'] == scenario_name), None)
        if scenario:
            with pytest.raises(scenario['exception_type']):
                func(*args, **kwargs)
    
    async def assert_raises_expected_error_async(self, scenario_name: str, func, *args, **kwargs):
        """Assert that async function raises expected error for scenario."""
        scenario = next((s for s in self.error_scenarios if s['name'] == scenario_name), None)
        if scenario:
            with pytest.raises(scenario['exception_type']):
                await func(*args, **kwargs)


class BaseConfigurationTest(BaseAgentTest):
    """Base class for configuration and settings tests."""
    
    def setup_agent_specific_fixtures(self):
        """Setup configuration test fixtures."""
        super().setup_agent_specific_fixtures()
        self.test_configs = {}
        self.default_config = {}
        self.invalid_configs = []
    
    def add_test_config(self, name: str, config: Dict[str, Any]):
        """Add a test configuration."""
        self.test_configs[name] = config
    
    def add_invalid_config(self, config: Dict[str, Any], expected_error: Type[Exception]):
        """Add an invalid configuration that should raise an error."""
        self.invalid_configs.append({
            'config': config,
            'expected_error': expected_error
        })
    
    def test_valid_configurations(self):
        """Test all valid configurations. Override in subclass."""
        pass
    
    def test_invalid_configurations(self):
        """Test all invalid configurations. Override in subclass."""
        pass


# =============================================================================
# TEST UTILITIES
# =============================================================================

class TestDataGenerator:
    """Utility class for generating test data."""
    
    @staticmethod
    def create_mock_cpp_file(file_path: Path, include_errors: bool = False):
        """Create a mock C++ file for testing."""
        content = """#include <iostream>
#include <vector>
#include <memory>

class TestClass {
public:
    TestClass() = default;
    ~TestClass() = default;
    
    void doSomething() {
        std::cout << "Doing something" << std::endl;
    }
    
private:
    int member_var_{0};
};

int main() {
    auto test_obj = std::make_unique<TestClass>();
    test_obj->doSomething();
"""
        
        if include_errors:
            content += """
    // Intentional errors for testing
    int unused_var = 42;  // unused variable warning
    std::vector<int> vec;
    vec[100] = 1;  // potential out of bounds
    
    int* ptr = new int(42);
    // Missing delete - memory leak
"""
        
        content += """
    return 0;
}
"""
        file_path.write_text(content)
        return file_path
    
    @staticmethod 
    def create_mock_cmake_file(file_path: Path):
        """Create a mock CMakeLists.txt for testing."""
        content = """cmake_minimum_required(VERSION 3.16)
project(TestProject CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Compiler flags
set(CMAKE_CXX_FLAGS "-Wall -Wextra -Wpedantic")
set(CMAKE_CXX_FLAGS_DEBUG "-g -O0")
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")

# Source files
file(GLOB_RECURSE SOURCES "src/*.cpp" "src/*.hpp")
file(GLOB_RECURSE HEADERS "include/*.hpp")

# Include directories
include_directories(include)

# Create executable
add_executable(${PROJECT_NAME} ${SOURCES})

# Tests
enable_testing()
add_subdirectory(tests)
"""
        file_path.write_text(content)
        return file_path