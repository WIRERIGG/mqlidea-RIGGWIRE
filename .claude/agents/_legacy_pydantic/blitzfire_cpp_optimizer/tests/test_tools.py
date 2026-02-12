"""Test individual tools functionality."""

import pytest
from agent import CPP_OPTIMIZATION_KNOWLEDGE

def test_cpp_optimization_knowledge():
    """Test that C++ optimization knowledge base is comprehensive."""
    assert 'simd_patterns' in CPP_OPTIMIZATION_KNOWLEDGE
    assert 'cache_optimization' in CPP_OPTIMIZATION_KNOWLEDGE  
    assert 'algorithmic_patterns' in CPP_OPTIMIZATION_KNOWLEDGE
    assert 'io_optimization' in CPP_OPTIMIZATION_KNOWLEDGE
    
    # Test SIMD patterns
    simd = CPP_OPTIMIZATION_KNOWLEDGE['simd_patterns']
    assert 'avx2_float' in simd
    assert 'avx512_double' in simd
    
    # Test cache optimization
    cache = CPP_OPTIMIZATION_KNOWLEDGE['cache_optimization']
    assert 'soa_pattern' in cache
    assert 'prefetching' in cache
    
    # Test algorithmic patterns
    algo = CPP_OPTIMIZATION_KNOWLEDGE['algorithmic_patterns']
    assert 'hash_optimization' in algo
    assert 'sorting_optimization' in algo
    
    # Test I/O optimization
    io = CPP_OPTIMIZATION_KNOWLEDGE['io_optimization']
    assert 'buffered_output' in io

def test_knowledge_completeness():
    """Test that each optimization pattern has required fields."""
    for category_name, category in CPP_OPTIMIZATION_KNOWLEDGE.items():
        for pattern_name, pattern in category.items():
            assert 'description' in pattern, f"Missing description in {category_name}.{pattern_name}"
            assert 'speedup' in pattern, f"Missing speedup in {category_name}.{pattern_name}"

def test_performance_tiers():
    """Test performance tier expectations."""
    # Level 1 optimizations (2-10x)
    io_speedup = CPP_OPTIMIZATION_KNOWLEDGE['io_optimization']['buffered_output']['speedup']
    assert '10-100x' in io_speedup
    
    # Level 2-3 optimizations
    simd_speedup = CPP_OPTIMIZATION_KNOWLEDGE['simd_patterns']['avx2_float']['speedup'] 
    assert '4-8x' in simd_speedup
    
    cache_speedup = CPP_OPTIMIZATION_KNOWLEDGE['cache_optimization']['soa_pattern']['speedup']
    assert '2-10x' in cache_speedup
    
    hash_speedup = CPP_OPTIMIZATION_KNOWLEDGE['algorithmic_patterns']['hash_optimization']['speedup']
    assert '1000x' in hash_speedup

def test_compiler_flags():
    """Test that compiler flags are provided."""
    avx2_flags = CPP_OPTIMIZATION_KNOWLEDGE['simd_patterns']['avx2_float']['compiler_flags']
    assert '-mavx2' in avx2_flags
    assert '-mfma' in avx2_flags
    
    avx512_flags = CPP_OPTIMIZATION_KNOWLEDGE['simd_patterns']['avx512_double']['compiler_flags']
    assert '-mavx512f' in avx512_flags
    assert '-mavx512dq' in avx512_flags

def test_implementation_examples():
    """Test that implementation examples are provided."""
    avx2_impl = CPP_OPTIMIZATION_KNOWLEDGE['simd_patterns']['avx2_float']['implementation']
    assert '_mm256_add_ps' in avx2_impl
    assert '_mm256_loadu_ps' in avx2_impl
    assert '_mm256_storeu_ps' in avx2_impl
    
    soa_impl = CPP_OPTIMIZATION_KNOWLEDGE['cache_optimization']['soa_pattern']['implementation']
    assert 'std::vector<float>' in soa_impl
    assert 'struct Points' in soa_impl
    
    prefetch_impl = CPP_OPTIMIZATION_KNOWLEDGE['cache_optimization']['prefetching']['implementation']
    assert '_mm_prefetch' in prefetch_impl
    assert '_MM_HINT_T0' in prefetch_impl
    
    io_impl = CPP_OPTIMIZATION_KNOWLEDGE['io_optimization']['buffered_output']['implementation']
    assert 'std::ostringstream' in io_impl
    assert 'buffer.str()' in io_impl