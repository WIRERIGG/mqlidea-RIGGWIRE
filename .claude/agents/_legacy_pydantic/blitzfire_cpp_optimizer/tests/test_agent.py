"""Test the BLITZFIRE C++ Optimizer Agent."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from agent import agent, BlitzfireAgent, TestModel, FunctionModel


@pytest.fixture
def test_agent():
    """Create a test agent."""
    return agent

def test_agent_import():
    """Test that the agent can be imported."""
    assert agent is not None
    assert isinstance(agent, BlitzfireAgent)

def test_agent_tools_available(test_agent):
    """Test that agent tools are properly registered."""
    tools = test_agent.tools
    assert len(tools) >= 14  # We registered 14 tools
    
    required_tools = [
        'analyze_cpp_performance',
        'optimize_cpp_code', 
        'generate_performance_benchmark',
        'validate_optimization_safety',
        'query_optimization_knowledge',
        'generate_cmake_integration'
    ]
    
    for tool in required_tools:
        assert tool in tools

@pytest.mark.asyncio
async def test_agent_run(test_agent):
    """Test basic agent run functionality."""
    result = await test_agent.run("Optimize this C++ code for performance")
    
    assert result is not None
    assert result['success'] is True
    assert 'message' in result
    assert 'recommendations' in result

@pytest.mark.asyncio  
async def test_analyze_cpp_performance_tool(test_agent):
    """Test the analyze_cpp_performance tool."""
    tool = test_agent._tools['analyze_cpp_performance']
    
    result = await tool(
        ctx=None,
        code="for (int i = 0; i < n; ++i) { sum += data[i]; }"
    )
    
    assert result is not None
    assert result['success'] is True
    assert 'analysis' in result
    assert 'recommendations' in result

@pytest.mark.asyncio
async def test_optimize_cpp_code_tool(test_agent):
    """Test the optimize_cpp_code tool."""
    tool = test_agent._tools['optimize_cpp_code']
    original_code = "std::cout << value << std::endl;"
    
    result = await tool(
        ctx=None,
        code=original_code
    )
    
    assert result is not None  
    assert result['success'] is True
    assert 'optimized_code' in result
    assert result['wire_ground_compatible'] is True

@pytest.mark.asyncio
async def test_generate_performance_benchmark_tool(test_agent):
    """Test the generate_performance_benchmark tool."""
    tool = test_agent._tools['generate_performance_benchmark']
    
    original_code = "for (int i = 0; i < n; ++i) { sum += data[i]; }"
    optimized_code = "// AVX2 optimized version"
    
    result = await tool(
        ctx=None,
        original_code=original_code,
        optimized_code=optimized_code
    )
    
    assert result is not None
    assert result['success'] is True
    assert 'benchmark_code' in result
    assert result['wire_ground_compatible'] is True

@pytest.mark.asyncio
async def test_validate_optimization_safety_tool(test_agent):
    """Test the validate_optimization_safety tool."""
    tool = test_agent._tools['validate_optimization_safety']
    
    result = await tool(
        ctx=None,
        optimized_code="// Safe optimized code"
    )
    
    assert result is not None
    assert result['success'] is True
    assert result['memory_safe'] is True
    assert result['wire_ground_compatible'] is True

@pytest.mark.asyncio
async def test_query_optimization_knowledge_tool(test_agent):
    """Test the query_optimization_knowledge tool."""
    tool = test_agent._tools['query_optimization_knowledge'] 
    
    result = await tool(
        ctx=None,
        query="SIMD optimization techniques"
    )
    
    assert result is not None
    assert result['success'] is True
    assert 'results' in result
    assert 'knowledge_categories' in result

@pytest.mark.asyncio
async def test_generate_cmake_integration_tool(test_agent):
    """Test the generate_cmake_integration tool."""
    tool = test_agent._tools['generate_cmake_integration']
    
    result = await tool(
        ctx=None,
        optimization_flags=["-mavx2", "-O3"]
    )
    
    assert result is not None
    assert result['success'] is True
    assert 'cmake_code' in result
    assert result['wire_ground_compatible'] is True

@pytest.mark.asyncio
async def test_simd_analysis_tool(test_agent):
    """Test SIMD vectorization analysis tool."""
    tool = test_agent._tools['simd_vectorization_analysis']
    
    result = await tool(
        ctx=None,
        code="for (int i = 0; i < n; ++i) { result[i] = a[i] + b[i]; }"
    )
    
    assert result is not None
    assert 'vectorizable_loops' in result
    assert 'simd_potential' in result
    assert 'estimated_speedup' in result

@pytest.mark.asyncio
async def test_cache_analysis_tool(test_agent):
    """Test cache optimization analysis tool."""
    tool = test_agent._tools['cache_optimization_analysis']
    
    result = await tool(
        ctx=None,
        code="struct Point { float x, y, z; }; std::vector<Point> points;"
    )
    
    assert result is not None
    assert 'cache_misses' in result
    assert 'optimization' in result
    assert 'estimated_speedup' in result

@pytest.mark.asyncio
async def test_algorithmic_analysis_tool(test_agent):
    """Test algorithmic complexity analysis tool."""
    tool = test_agent._tools['algorithmic_complexity_analysis']
    
    result = await tool(
        ctx=None,
        code="for (auto& item : vec) { if (item == target) return true; }"
    )
    
    assert result is not None
    assert 'current_complexity' in result
    assert 'optimized_complexity' in result
    assert 'estimated_speedup' in result

@pytest.mark.asyncio
async def test_io_analysis_tool(test_agent):
    """Test I/O performance analysis tool."""
    tool = test_agent._tools['io_performance_analysis']
    
    result = await tool(
        ctx=None,
        code="std::cout << item << std::endl;"
    )
    
    assert result is not None
    assert 'io_operations' in result
    assert 'optimization' in result
    assert 'estimated_speedup' in result

@pytest.mark.asyncio
async def test_compiler_analysis_tool(test_agent):
    """Test compiler optimization analysis tool."""
    tool = test_agent._tools['compiler_optimization_analysis']
    
    result = await tool(
        ctx=None,
        code="void process() { /* code */ }"
    )
    
    assert result is not None
    assert 'recommended_flags' in result
    assert 'estimated_speedup' in result

@pytest.mark.asyncio  
async def test_memory_safety_validation_tool(test_agent):
    """Test memory safety validation tool."""
    tool = test_agent._tools['memory_safety_validation']
    
    result = await tool(
        ctx=None,
        code="std::vector<int> data(100);"
    )
    
    assert result is not None
    assert 'safe' in result
    assert 'checks' in result

@pytest.mark.asyncio
async def test_thread_safety_validation_tool(test_agent):
    """Test thread safety validation tool.""" 
    tool = test_agent._tools['thread_safety_validation']
    
    result = await tool(
        ctx=None,
        code="std::atomic<int> counter(0);"
    )
    
    assert result is not None
    assert 'safe' in result
    assert 'parallel_safe' in result

@pytest.mark.asyncio
async def test_wire_ground_integration_tool(test_agent):
    """Test wire ground integration validation tool."""
    tool = test_agent._tools['wire_ground_integration']
    
    result = await tool(
        ctx=None,
        code="// Wire ground compatible code"
    )
    
    assert result is not None
    assert 'zero_warnings' in result
    assert 'cmake_compatible' in result

def test_test_model_available():
    """Test that TestModel is available."""
    assert TestModel is not None

def test_function_model_available(): 
    """Test that FunctionModel is available."""
    assert FunctionModel is not None

def test_agent_dependencies_creation():
    """Test that dependencies can be created successfully."""
    from dependencies import BlitzfireDependencies
    deps = BlitzfireDependencies()
    
    assert deps is not None
    assert hasattr(deps, 'session_id')
    assert hasattr(deps, 'settings')
    assert hasattr(deps, 'config')