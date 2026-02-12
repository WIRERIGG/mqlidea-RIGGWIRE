"""Comprehensive Pydantic AI Agent Validation Test Suite.

This test suite validates the BLITZFIRE C++ Optimizer agent against all
Pydantic AI requirements and production readiness standards.
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

# Import agent components
from agent import agent, BlitzfireAgent, TestModel, FunctionModel
from dependencies import BlitzfireDependencies
from models import (
    OptimizationRequest, OptimizationResult, PerformanceAnalysis,
    OptimizationLevel, OptimizationDomain, PerformanceBottleneck
)

# Import Pydantic AI testing patterns
try:
    from pydantic_ai.models.test import TestModel as PydanticTestModel
    from pydantic_ai.models.function import FunctionModel as PydanticFunctionModel
    PYDANTIC_AI_AVAILABLE = True
except ImportError:
    PydanticTestModel = None
    PydanticFunctionModel = None
    PYDANTIC_AI_AVAILABLE = False


class TestPydanticAICompliance:
    """Test Pydantic AI compliance and validation framework requirements."""
    
    def test_agent_structure_compliance(self):
        """Test that agent follows Pydantic AI structure."""
        # Test agent instance
        assert isinstance(agent, BlitzfireAgent)
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'tools')
        assert hasattr(agent, 'run')
        
        # Test model availability
        assert agent.test_model is not None
        assert agent.function_model is not None
        
        # Test dependencies type
        assert agent.deps_type == BlitzfireDependencies
        
    def test_test_model_functionality(self):
        """Test TestModel implementation."""
        test_model = agent.test_model
        
        # Test basic structure
        assert hasattr(test_model, 'test_name')
        assert hasattr(test_model, 'input_code')
        assert hasattr(test_model, 'expected_optimizations')
        
        # Test methods if available
        if hasattr(test_model, 'get_mock_response'):
            # Test mock response functionality
            assert callable(test_model.get_mock_response)
            
        if hasattr(test_model, 'validate_optimization'):
            # Test validation functionality
            assert callable(test_model.validate_optimization)
    
    def test_function_model_functionality(self):
        """Test FunctionModel implementation."""
        function_model = agent.function_model
        
        # Test basic structure
        assert function_model is not None
        
        if hasattr(function_model, 'function_name'):
            assert hasattr(function_model, 'function_code')
            assert hasattr(function_model, 'parameters')
        
        # Test methods if available
        if hasattr(function_model, 'update_state'):
            assert callable(function_model.update_state)
        
        if hasattr(function_model, 'record_call'):
            assert callable(function_model.record_call)
    
    def test_tool_registration_compliance(self):
        """Test that tools are properly registered for Pydantic AI."""
        tools = agent.tools
        
        # Test required tools are present
        required_tools = [
            'analyze_cpp_performance',
            'optimize_cpp_code',
            'generate_performance_benchmark',
            'validate_optimization_safety'
        ]
        
        for tool_name in required_tools:
            assert tool_name in tools
            assert callable(tools[tool_name])
        
        # Test tool metadata if available
        if hasattr(agent, 'tool_metadata'):
            metadata = agent.tool_metadata
            assert 'total_tools' in metadata
            assert metadata['total_tools'] > 0
            assert 'categories' in metadata
    
    @pytest.mark.asyncio
    async def test_agent_run_interface(self):
        """Test agent run interface compliance."""
        result = await agent.run("Test optimization request")
        
        # Test return structure
        assert isinstance(result, dict)
        assert 'success' in result
        assert result['success'] is True
        
        # Test expected fields
        assert 'message' in result
        assert isinstance(result['message'], str)
        
    def test_dependencies_structure(self):
        """Test dependencies structure compliance."""
        deps = BlitzfireDependencies()
        
        # Test required attributes for validation framework
        assert hasattr(deps, 'session_id')
        assert hasattr(deps, 'settings')
        assert hasattr(deps, 'config')
        
        # Test core components
        assert hasattr(deps, 'archon_client')
        assert hasattr(deps, 'cpp_analyzer')
        assert hasattr(deps, 'compiler_optimizer')


class TestPerformanceValidation:
    """Test performance capabilities and benchmarking."""
    
    @pytest.mark.asyncio
    async def test_performance_analysis_speed(self):
        """Test that performance analysis completes within reasonable time."""
        start_time = time.perf_counter()
        
        result = await agent.run("Analyze this C++ code for performance bottlenecks")
        
        elapsed = time.perf_counter() - start_time
        
        # Should complete within 2 seconds for basic analysis
        assert elapsed < 2.0
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test agent can handle concurrent requests."""
        tasks = []
        
        # Create 5 concurrent requests
        for i in range(5):
            task = agent.run(f"Optimize C++ code sample {i}")
            tasks.append(task)
        
        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        for result in results:
            assert result['success'] is True
            assert 'message' in result
    
    @pytest.mark.asyncio
    async def test_tool_performance(self):
        """Test individual tool performance."""
        tools_to_test = [
            ('analyze_cpp_performance', {'code': 'int main() { return 0; }'}),
            ('simd_vectorization_analysis', {'code': 'for(int i=0; i<n; i++) a[i] += b[i];'}),
            ('cache_optimization_analysis', {'code': 'struct Point { float x, y, z; };'}),
        ]
        
        for tool_name, args in tools_to_test:
            if tool_name in agent.tools:
                start_time = time.perf_counter()
                
                result = await agent.tools[tool_name](None, **args)
                
                elapsed = time.perf_counter() - start_time
                
                # Each tool should complete within 1 second
                assert elapsed < 1.0
                assert result is not None


class TestIntegrationValidation:
    """Test integration capabilities."""
    
    @pytest.mark.asyncio
    async def test_full_optimization_pipeline(self):
        """Test complete optimization pipeline."""
        cpp_code = """
        #include <iostream>
        #include <vector>
        
        int main() {
            std::vector<int> data(1000);
            for (int i = 0; i < 1000; ++i) {
                std::cout << data[i] << std::endl;
            }
            return 0;
        }
        """
        
        # Step 1: Analyze performance
        analysis_tool = agent.tools['analyze_cpp_performance']
        analysis = await analysis_tool(None, code=cpp_code)
        
        assert analysis['success'] is True
        assert 'analysis' in analysis
        
        # Step 2: Optimize code
        optimize_tool = agent.tools['optimize_cpp_code']
        optimization = await optimize_tool(None, code=cpp_code)
        
        assert optimization['success'] is True
        assert 'optimized_code' in optimization
        
        # Step 3: Validate safety
        safety_tool = agent.tools['validate_optimization_safety']
        safety = await safety_tool(None, optimized_code=optimization['optimized_code'])
        
        assert safety['success'] is True
        assert safety['memory_safe'] is True
        assert safety['wire_ground_compatible'] is True
    
    @pytest.mark.asyncio
    async def test_knowledge_integration(self):
        """Test knowledge query integration."""
        knowledge_tool = agent.tools['query_optimization_knowledge']
        
        result = await knowledge_tool(None, query="SIMD vectorization patterns")
        
        assert result['success'] is True
        assert 'results' in result
        assert len(result['results']) > 0
        assert 'knowledge_categories' in result
    
    @pytest.mark.asyncio 
    async def test_cmake_integration(self):
        """Test CMake integration generation."""
        cmake_tool = agent.tools['generate_cmake_integration']
        
        result = await cmake_tool(None, optimization_flags=["-mavx2", "-O3"])
        
        assert result['success'] is True
        assert 'cmake_code' in result
        assert result['wire_ground_compatible'] is True


class TestSafetyValidation:
    """Test safety and security validation."""
    
    @pytest.mark.asyncio
    async def test_memory_safety_validation(self):
        """Test memory safety validation."""
        safety_tool = agent.tools['memory_safety_validation']
        
        safe_code = "std::vector<int> data(100); data[50] = 42;"
        result = await safety_tool(None, code=safe_code)
        
        assert result['safe'] is True
        assert 'checks' in result
        assert 'tools' in result
    
    @pytest.mark.asyncio
    async def test_thread_safety_validation(self):
        """Test thread safety validation."""
        thread_tool = agent.tools['thread_safety_validation']
        
        thread_safe_code = "std::atomic<int> counter(0); counter.fetch_add(1);"
        result = await thread_tool(None, code=thread_safe_code)
        
        assert result['safe'] is True
        assert result['parallel_safe'] is True
    
    @pytest.mark.asyncio
    async def test_wire_ground_compatibility(self):
        """Test Wire Ground build system compatibility."""
        wire_tool = agent.tools['wire_ground_integration']
        
        result = await wire_tool(None, code="// Test code")
        
        assert result['zero_warnings'] is True
        assert result['cmake_compatible'] is True
        assert result['clang_tidy_clean'] is True
        assert result['sanitizer_compatible'] is True


class TestProductionReadiness:
    """Test production readiness aspects."""
    
    @pytest.mark.asyncio
    async def test_dependencies_initialization(self):
        """Test dependency initialization."""
        deps = BlitzfireDependencies()
        
        # Test initialization
        await deps.initialize()
        
        assert deps.initialized is True
        
        # Test health check
        health = await deps.health_check()
        
        assert health['initialized'] is True
        assert health['cpp_analyzer'] is True
        assert health['compiler_optimizer'] is True
        
        # Test cleanup
        await deps.cleanup()
    
    def test_error_handling(self):
        """Test error handling capabilities."""
        # Test with invalid input
        result = agent.run_sync("")  # Empty input
        
        # Should handle gracefully
        assert isinstance(result, dict)
        # Should still return success (graceful handling)
        assert result['success'] is True
    
    def test_model_validation(self):
        """Test Pydantic model validation."""
        # Test OptimizationRequest validation
        request = OptimizationRequest(
            code="int main() { return 0; }",
            optimization_level=OptimizationLevel.ADVANCED
        )
        
        assert request.code is not None
        assert request.optimization_level == OptimizationLevel.ADVANCED
        assert request.safety_mode is True  # Default
        
        # Test invalid request should raise validation error
        with pytest.raises(Exception):  # Pydantic validation error
            OptimizationRequest(code="")  # Empty code should fail


class TestComprehensiveValidation:
    """Comprehensive validation tests."""
    
    def test_all_requirements_coverage(self):
        """Test that all validation requirements are covered."""
        # Test agent structure
        assert hasattr(agent, 'model')
        assert hasattr(agent, 'tools') 
        assert hasattr(agent, 'run')
        
        # Test tool count and categories
        assert len(agent.tools) >= 13  # Minimum expected tools
        
        # Test model compatibility
        assert agent.test_model is not None
        assert agent.function_model is not None
        
        # Test dependencies
        deps = BlitzfireDependencies()
        assert hasattr(deps, 'session_id')
        assert hasattr(deps, 'settings')
        assert hasattr(deps, 'config')
    
    @pytest.mark.asyncio
    async def test_end_to_end_validation(self):
        """Complete end-to-end validation."""
        # Test input
        cpp_code = """
        #include <vector>
        #include <iostream>
        
        void process_data() {
            std::vector<float> data(1000);
            for (int i = 0; i < 1000; ++i) {
                for (int j = 0; j < 1000; ++j) {
                    if (data[i] == j) {
                        std::cout << "Found: " << j << std::endl;
                    }
                }
            }
        }
        """
        
        # Full pipeline test
        steps = [
            ('analyze_cpp_performance', {'code': cpp_code}),
            ('simd_vectorization_analysis', {'code': cpp_code}),
            ('cache_optimization_analysis', {'code': cpp_code}),
            ('algorithmic_complexity_analysis', {'code': cpp_code}),
            ('io_performance_analysis', {'code': cpp_code}),
            ('optimize_cpp_code', {'code': cpp_code}),
        ]
        
        results = {}
        for step_name, args in steps:
            if step_name in agent.tools:
                result = await agent.tools[step_name](None, **args)
                results[step_name] = result
                assert result is not None
        
        # Validate all steps completed successfully
        for step_name, result in results.items():
            if isinstance(result, dict) and 'success' in result:
                assert result['success'] is True, f"Step {step_name} failed"


# Performance benchmarks
@pytest.mark.benchmark
class TestBenchmarks:
    """Performance benchmarks for the agent."""
    
    def test_agent_run_benchmark(self, benchmark):
        """Benchmark agent run performance."""
        def run_agent():
            return agent.run_sync("Analyze C++ performance")
        
        result = benchmark(run_agent)
        assert result['success'] is True
    
    @pytest.mark.asyncio
    async def test_concurrent_benchmark(self):
        """Test concurrent request handling performance."""
        num_concurrent = 10
        tasks = [agent.run(f"Test {i}") for i in range(num_concurrent)]
        
        start_time = time.perf_counter()
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time
        
        # Should handle 10 concurrent requests in under 5 seconds
        assert elapsed < 5.0
        
        # All should succeed
        for result in results:
            assert result['success'] is True


if __name__ == "__main__":
    # Run validation tests
    pytest.main([__file__, "-v", "--tb=short"])