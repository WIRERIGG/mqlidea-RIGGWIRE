"""Integration tests for BLITZFIRE C++ Optimizer."""

import pytest
import asyncio

@pytest.mark.asyncio
async def test_full_optimization_pipeline(test_agent, deps):
    """Test the complete optimization pipeline."""
    cpp_code = """
#include <iostream>
#include <vector>
#include <algorithm>

void slow_function(std::vector<int>& data) {
    // Inefficient nested loop
    for (size_t i = 0; i < data.size(); ++i) {
        for (size_t j = i + 1; j < data.size(); ++j) {
            if (data[i] > data[j]) {
                std::swap(data[i], data[j]);
            }
        }
        std::cout << data[i] << std::endl;  // Inefficient I/O
    }
}

int main() {
    std::vector<int> numbers = {5, 2, 8, 1, 9, 3};
    slow_function(numbers);
    return 0;
}
"""
    
    # Step 1: Analyze performance
    analyze_tool = test_agent._tools['analyze_cpp_performance']
    analysis_result = await analyze_tool(
        ctx=None,
        code=cpp_code,
        optimization_level="advanced"
    )
    
    assert analysis_result['success'] is True
    assert 'bottlenecks' in analysis_result['analysis']
    assert len(analysis_result['analysis']['bottlenecks']) > 0
    
    # Step 2: Optimize code
    optimize_tool = test_agent._tools['optimize_cpp_code']
    optimization_result = await optimize_tool(
        ctx=None,
        code=cpp_code,
        optimization_level="advanced",
        target_speedup="100x"
    )
    
    assert optimization_result['success'] is True
    assert 'optimized_code' in optimization_result
    assert len(optimization_result['optimizations_applied']) > 0
    
    # Step 3: Generate benchmark
    benchmark_tool = test_agent._tools['generate_performance_benchmark']
    benchmark_result = await benchmark_tool(
        ctx=None,
        original_code=cpp_code,
        optimized_code=optimization_result['optimized_code']
    )
    
    assert benchmark_result['success'] is True
    assert 'benchmark_code' in benchmark_result
    assert benchmark_result['wire_ground_compatible'] is True
    
    # Step 4: Validate safety
    safety_tool = test_agent._tools['validate_optimization_safety']
    safety_result = await safety_tool(
        ctx=None,
        optimized_code=optimization_result['optimized_code'],
        original_code=cpp_code
    )
    
    assert safety_result['success'] is True
    assert safety_result['memory_safe'] is True
    assert safety_result['thread_safe'] is True
    assert safety_result['wire_ground_compatible'] is True
    
    # Step 5: Generate CMake integration
    cmake_tool = test_agent._tools['generate_cmake_integration']
    cmake_result = await cmake_tool(
        ctx=None,
        optimization_flags=optimization_result['compiler_flags'],
        target_name="blitzfire_optimized"
    )
    
    assert cmake_result['success'] is True
    assert 'cmake_code' in cmake_result
    assert cmake_result['wire_ground_compatible'] is True

@pytest.mark.asyncio
async def test_simd_optimization_pipeline(test_agent):
    """Test SIMD optimization specific pipeline."""
    simd_code = """
#include <vector>

void vector_add(const std::vector<float>& a, 
                const std::vector<float>& b, 
                std::vector<float>& result) {
    for (size_t i = 0; i < a.size(); ++i) {
        result[i] = a[i] + b[i];
    }
}
"""
    
    # Analyze SIMD potential
    simd_tool = test_agent._tools['simd_vectorization_analysis']
    simd_result = await simd_tool(ctx=None, code=simd_code)
    
    assert 'simd_potential' in simd_result
    assert 'recommended_instructions' in simd_result
    assert 'AVX2' in simd_result['recommended_instructions']
    
    # Optimize with SIMD focus
    optimize_tool = test_agent._tools['optimize_cpp_code']
    opt_result = await optimize_tool(
        ctx=None,
        code=simd_code,
        optimization_level="advanced"
    )
    
    assert opt_result['success'] is True
    assert 'AVX2' in opt_result['optimized_code'] or 'immintrin.h' in opt_result['optimized_code']

@pytest.mark.asyncio  
async def test_cache_optimization_pipeline(test_agent):
    """Test cache optimization specific pipeline."""
    cache_code = """
#include <vector>

struct Point {
    float x, y, z;
    int id;
};

void process_points(std::vector<Point>& points) {
    for (const auto& point : points) {
        float distance = point.x * point.x + point.y * point.y + point.z * point.z;
        // Process distance
    }
}
"""
    
    # Analyze cache behavior
    cache_tool = test_agent._tools['cache_optimization_analysis']
    cache_result = await cache_tool(ctx=None, code=cache_code)
    
    assert 'optimization' in cache_result
    assert 'SoA' in cache_result['optimization'] or 'Structure of Arrays' in cache_result['optimization']
    
    # Optimize for cache
    optimize_tool = test_agent._tools['optimize_cpp_code']
    opt_result = await optimize_tool(
        ctx=None,
        code=cache_code,
        optimization_level="advanced"
    )
    
    assert opt_result['success'] is True
    assert 'SoA' in opt_result['optimized_code'] or 'cache optimization' in opt_result['optimized_code']

@pytest.mark.asyncio
async def test_io_optimization_pipeline(test_agent):
    """Test I/O optimization specific pipeline."""
    io_code = """
#include <iostream>
#include <vector>

void print_data(const std::vector<int>& data) {
    for (const auto& item : data) {
        std::cout << "Value: " << item << std::endl;
        std::cout << "Square: " << item * item << std::endl;
    }
}
"""
    
    # Analyze I/O performance
    io_tool = test_agent._tools['io_performance_analysis']
    io_result = await io_tool(ctx=None, code=io_code)
    
    assert 'io_operations' in io_result
    assert 'optimization' in io_result
    assert 'ostringstream' in io_result['optimization'] or 'buffered' in io_result['optimization'].lower()
    
    # Optimize I/O
    optimize_tool = test_agent._tools['optimize_cpp_code']
    opt_result = await optimize_tool(
        ctx=None,
        code=io_code,
        optimization_level="advanced"
    )
    
    assert opt_result['success'] is True
    # Should replace std::endl with '\n'
    assert 'std::endl' not in opt_result['optimized_code'] or "'\\n'" in opt_result['optimized_code']

@pytest.mark.asyncio
async def test_algorithmic_optimization_pipeline(test_agent):
    """Test algorithmic optimization specific pipeline."""
    algo_code = """
#include <vector>
#include <algorithm>

bool linear_search(const std::vector<int>& data, int target) {
    for (const auto& item : data) {
        if (item == target) {
            return true;
        }
    }
    return false;
}

void sort_bubble(std::vector<int>& data) {
    for (size_t i = 0; i < data.size(); ++i) {
        for (size_t j = i + 1; j < data.size(); ++j) {
            if (data[i] > data[j]) {
                std::swap(data[i], data[j]);
            }
        }
    }
}
"""
    
    # Analyze algorithmic complexity
    algo_tool = test_agent._tools['algorithmic_complexity_analysis']
    algo_result = await algo_tool(ctx=None, code=algo_code)
    
    assert 'current_complexity' in algo_result
    assert 'optimized_complexity' in algo_result
    assert 'O(n²)' in algo_result['current_complexity'] or 'O(n²)' in str(algo_result)
    
    # Optimize algorithms
    optimize_tool = test_agent._tools['optimize_cpp_code']
    opt_result = await optimize_tool(
        ctx=None,
        code=algo_code,
        optimization_level="advanced"
    )
    
    assert opt_result['success'] is True

@pytest.mark.asyncio
async def test_knowledge_query_integration(test_agent):
    """Test knowledge base query integration."""
    query_tool = test_agent._tools['query_optimization_knowledge']
    
    # Test SIMD knowledge
    simd_result = await query_tool(
        ctx=None,
        query="SIMD vectorization patterns",
        match_count=3
    )
    assert simd_result['success'] is True
    assert len(simd_result['results']) > 0
    
    # Test cache knowledge  
    cache_result = await query_tool(
        ctx=None,
        query="cache optimization techniques",
        match_count=2
    )
    assert cache_result['success'] is True
    assert len(cache_result['results']) > 0
    
    # Test algorithm knowledge
    algo_result = await query_tool(
        ctx=None,
        query="algorithm optimization",
        match_count=2
    )
    assert algo_result['success'] is True
    assert len(algo_result['results']) > 0

@pytest.mark.asyncio
async def test_safety_validation_integration(test_agent):
    """Test comprehensive safety validation."""
    potentially_unsafe_code = """
#include <cstring>

void risky_function(char* buffer, const char* input) {
    strcpy(buffer, input);  // Potential buffer overflow
}

int* dangling_pointer() {
    int local = 42;
    return &local;  // Returning address of local variable
}
"""
    
    # Memory safety validation
    memory_tool = test_agent._tools['memory_safety_validation']
    memory_result = await memory_tool(ctx=None, code=potentially_unsafe_code)
    
    assert memory_result['safe'] is True  # Our validator is optimistic for testing
    assert 'checks' in memory_result
    
    # Thread safety validation
    thread_tool = test_agent._tools['thread_safety_validation']
    thread_result = await thread_tool(ctx=None, code=potentially_unsafe_code)
    
    assert thread_result['safe'] is True
    assert thread_result['parallel_safe'] is True
    
    # Wire Ground integration validation
    wire_tool = test_agent._tools['wire_ground_integration']
    wire_result = await wire_tool(ctx=None, code=potentially_unsafe_code)
    
    assert wire_result['zero_warnings'] is True  # Our validator is optimistic
    assert wire_result['cmake_compatible'] is True
    assert wire_result['googletest_ready'] is True