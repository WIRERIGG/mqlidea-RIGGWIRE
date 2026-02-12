"""BLITZFIRE C++ Optimizer Agent - Ultra-high performance C++ optimization system.

This package provides comprehensive C++ optimization capabilities including:
- Algorithmic optimization (O(n²) → O(n log n))
- Memory optimization (cache-friendly patterns, RAII)
- SIMD vectorization (SSE, AVX)
- Compiler optimization integration (PGO, LTO)
- Performance profiling and benchmarking
- Wire_ground build system integration

The agent follows enterprise-grade patterns with zero-warning policy compliance.
"""

from .agent import blitzfire_agent, BlitzfireAgent, get_blitzfire_agent, get_agent, get_dependencies
from .models import (
    OptimizationRequest,
    OptimizationResult,
    PerformanceAnalysis,
    TestModel,
    FunctionModel
)
from .dependencies import BlitzfireDependencies, create_dependencies
from .tools import (
    analyze_cpp_performance,
    optimize_cpp_code,
    generate_performance_benchmark,
    validate_optimization_safety
)
from .providers import get_llm_model

__version__ = "1.0.0"
__author__ = "BLITZFIRE Optimization Team"

# Backward compatibility aliases
BlitzfireCppOptimizer = BlitzfireAgent
main_agent = blitzfire_agent

__all__ = [
    "blitzfire_agent",
    "BlitzfireAgent",
    "BlitzfireCppOptimizer",  # Backward compatibility
    "main_agent",
    "get_blitzfire_agent",
    "get_agent",
    "get_dependencies",
    "OptimizationRequest",
    "OptimizationResult",
    "PerformanceAnalysis",
    "TestModel",
    "FunctionModel",
    "BlitzfireDependencies",
    "create_dependencies",
    "analyze_cpp_performance",
    "optimize_cpp_code", 
    "generate_performance_benchmark",
    "validate_optimization_safety",
    "get_llm_model"
]