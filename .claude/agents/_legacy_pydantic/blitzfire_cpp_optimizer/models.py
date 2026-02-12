"""BLITZFIRE C++ Optimizer Data Models.

Defines comprehensive data structures for C++ optimization analysis,
results, and validation following Pydantic AI patterns.
"""

from typing import Dict, List, Optional, Union, Any, Literal
from pydantic import BaseModel, Field, validator
from enum import Enum
import json

# Import Pydantic AI models for proper validation framework compliance
try:
    from pydantic_ai.models.test import TestModel as PydanticTestModel
    from pydantic_ai.models.function import FunctionModel as PydanticFunctionModel
except ImportError:
    # Fallback to base models if pydantic_ai not available
    PydanticTestModel = BaseModel
    PydanticFunctionModel = BaseModel

class OptimizationLevel(str, Enum):
    """Optimization performance levels."""
    QUICK_WINS = "quick_wins"  # 2-10x
    ALGORITHMIC = "algorithmic"  # 10-100x  
    ADVANCED = "advanced"  # 100-1000x
    EXTREME = "extreme"  # 1000x+

class OptimizationDomain(str, Enum):
    """Optimization focus domains."""
    ALGORITHMIC = "algorithmic"
    MEMORY = "memory"
    SIMD = "simd"
    COMPILER = "compiler"
    IO = "io"
    GENERAL = "general"

class PerformanceBottleneck(BaseModel):
    """Individual performance bottleneck analysis."""
    location: str = Field(..., description="Code location (function, line, etc.)")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="Bottleneck severity")
    domain: OptimizationDomain = Field(..., description="Optimization domain")
    issue_type: str = Field(..., description="Type of performance issue")
    current_complexity: str = Field(..., description="Current algorithmic complexity")
    optimized_complexity: str = Field(..., description="Achievable complexity after optimization")
    estimated_speedup: str = Field(..., description="Expected performance improvement")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis")
    optimization_priority: int = Field(..., ge=1, le=10, description="Optimization priority (1=lowest, 10=highest)")

class OptimizationStrategy(BaseModel):
    """Specific optimization strategy."""
    name: str = Field(..., description="Strategy name")
    domain: OptimizationDomain = Field(..., description="Optimization domain")
    level: OptimizationLevel = Field(..., description="Optimization level")
    description: str = Field(..., description="Strategy description")
    implementation_code: str = Field(..., description="Optimized code implementation")
    before_code: Optional[str] = Field(None, description="Original code for comparison")
    expected_speedup: str = Field(..., description="Expected performance improvement")
    compiler_flags: List[str] = Field(default_factory=list, description="Required compiler flags")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies/libraries")
    safety_validation: Dict[str, Any] = Field(default_factory=dict, description="Safety validation results")
    wire_ground_compatible: bool = Field(True, description="Compatible with wire_ground build system")

class PerformanceAnalysis(BaseModel):
    """Comprehensive performance analysis results."""
    file_path: str = Field(..., description="Path to analyzed file")
    total_lines: int = Field(..., gt=0, description="Total lines of code analyzed")
    analysis_timestamp: str = Field(..., description="Analysis timestamp")
    bottlenecks: List[PerformanceBottleneck] = Field(default_factory=list, description="Identified bottlenecks")
    optimization_opportunities: List[OptimizationStrategy] = Field(default_factory=list, description="Available optimizations")
    overall_score: float = Field(..., ge=0.0, le=100.0, description="Overall performance score")
    domains_analyzed: List[OptimizationDomain] = Field(default_factory=list, description="Analyzed domains")
    estimated_total_speedup: str = Field(..., description="Total expected speedup")
    safety_compliance: Dict[str, bool] = Field(default_factory=dict, description="Safety compliance checks")
    
class BenchmarkResult(BaseModel):
    """Performance benchmark results."""
    test_name: str = Field(..., description="Benchmark test name")
    original_time: float = Field(..., gt=0, description="Original execution time (seconds)")
    optimized_time: float = Field(..., gt=0, description="Optimized execution time (seconds)")
    speedup_factor: float = Field(..., gt=0, description="Speedup factor (original/optimized)")
    memory_usage_original: int = Field(..., ge=0, description="Original memory usage (bytes)")
    memory_usage_optimized: int = Field(..., ge=0, description="Optimized memory usage (bytes)")
    memory_improvement: float = Field(..., description="Memory improvement factor")
    compiler_optimizations: List[str] = Field(default_factory=list, description="Applied compiler optimizations")
    validation_passed: bool = Field(..., description="Safety validation passed")

class OptimizationRequest(BaseModel):
    """Request for C++ code optimization."""
    code: str = Field(..., min_length=1, description="C++ code to optimize")
    file_path: Optional[str] = Field(None, description="Source file path")
    optimization_level: OptimizationLevel = Field(OptimizationLevel.ALGORITHMIC, description="Target optimization level")
    focus_domains: List[OptimizationDomain] = Field(default_factory=lambda: [OptimizationDomain.GENERAL], description="Focus domains")
    safety_mode: bool = Field(True, description="Enable comprehensive safety validation")
    wire_ground_integration: bool = Field(True, description="Ensure wire_ground build system compatibility")
    benchmark_generation: bool = Field(True, description="Generate performance benchmarks")
    compiler_target: str = Field("clang++", description="Target compiler")
    additional_requirements: Optional[str] = Field(None, description="Additional optimization requirements")

class OptimizationResult(BaseModel):
    """Complete optimization analysis and results."""
    request_id: str = Field(..., description="Unique request identifier")
    analysis: PerformanceAnalysis = Field(..., description="Performance analysis")
    optimized_code: str = Field(..., description="Optimized C++ code")
    optimization_strategies: List[OptimizationStrategy] = Field(..., description="Applied optimization strategies")
    benchmarks: List[BenchmarkResult] = Field(default_factory=list, description="Performance benchmarks")
    compilation_validation: Dict[str, Any] = Field(default_factory=dict, description="Compilation validation results")
    safety_validation: Dict[str, Any] = Field(default_factory=dict, description="Safety validation results")
    cmake_integration: Optional[str] = Field(None, description="CMake integration code")
    test_suite_integration: Optional[str] = Field(None, description="Test suite integration code")
    summary: str = Field(..., description="Optimization summary")
    recommendations: List[str] = Field(default_factory=list, description="Additional recommendations")
    total_estimated_speedup: str = Field(..., description="Total estimated performance improvement")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in optimizations")

# Pydantic AI Required Models

class TestModel(PydanticTestModel):
    """Test model for validation and testing scenarios - extends Pydantic AI TestModel."""
    test_name: str = Field(default="blitzfire_test", description="Name of the test scenario")
    input_code: str = Field(default="", description="C++ code for testing")
    expected_optimizations: List[str] = Field(default_factory=list, description="Expected optimization types")
    expected_speedup_min: float = Field(default=1.0, ge=1.0, description="Minimum expected speedup")
    expected_speedup_max: float = Field(default=100.0, ge=1.0, description="Maximum expected speedup")
    validation_requirements: Dict[str, Any] = Field(default_factory=dict, description="Validation requirements")
    mock_responses: Dict[str, str] = Field(default_factory=dict, description="Mock responses for testing")
    
    def get_mock_response(self, key: str) -> Optional[str]:
        """Get mock response for testing."""
        return self.mock_responses.get(key)
        
    def validate_optimization(self, result: OptimizationResult) -> bool:
        """Validate optimization result against expectations."""
        if not result.optimized_code:
            return False
            
        # Check if expected optimizations were applied
        for expected_opt in self.expected_optimizations:
            if expected_opt not in result.summary.lower():
                return False
                
        return True
    
class FunctionModel(PydanticFunctionModel):
    """Function model for advanced optimization scenarios - extends Pydantic AI FunctionModel."""
    function_name: str = Field(default="optimize", description="Function name")
    function_code: str = Field(default="", description="Function source code")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Function parameters")
    optimization_state: Dict[str, Any] = Field(default_factory=dict, description="Current optimization state")
    call_count: int = Field(default=0, ge=0, description="Number of times function called")
    last_result: Optional[OptimizationResult] = Field(default=None, description="Last optimization result")
    performance_profile: Dict[str, Any] = Field(default_factory=dict, description="Performance profiling data")
    
    def update_state(self, new_state: Dict[str, Any]) -> None:
        """Update optimization state."""
        self.optimization_state.update(new_state)
        
    def record_call(self, result: OptimizationResult) -> None:
        """Record function call and result."""
        self.call_count += 1
        self.last_result = result
        
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            "call_count": self.call_count,
            "last_speedup": self.last_result.total_estimated_speedup if self.last_result else "N/A",
            "optimization_state": self.optimization_state,
            "performance_profile": self.performance_profile
        }
        
    def simulate_tool_call(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Simulate tool call for testing."""
        return {
            "tool": tool_name,
            "parameters": kwargs,
            "timestamp": "simulated",
            "result": f"Simulated {tool_name} call with {len(kwargs)} parameters"
        }

class ArchonTaskRequest(BaseModel):
    """Request for Archon MCP integration."""
    action: Literal["create", "get", "update", "list"] = Field(..., description="Archon action")
    project_id: Optional[str] = Field(None, description="Project ID")
    task_id: Optional[str] = Field(None, description="Task ID")
    title: Optional[str] = Field(None, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")

class ArchonKnowledgeRequest(BaseModel):
    """Request for Archon knowledge queries."""
    query_type: Literal["rag", "code_examples", "features"] = Field(..., description="Query type")
    query: str = Field(..., description="Query text")
    match_count: int = Field(3, ge=1, le=10, description="Number of matches to return")
    context: Optional[str] = Field(None, description="Additional context")

# Model validation and utilities

def validate_cpp_code(code: str) -> bool:
    """Basic C++ code validation."""
    if not code.strip():
        return False
    # Basic syntax checks
    required_elements = [
        any(keyword in code for keyword in ['int ', 'void ', 'class ', 'struct ']),
        '{' in code or ';' in code
    ]
    return all(required_elements)

def estimate_optimization_impact(bottlenecks: List[PerformanceBottleneck]) -> str:
    """Estimate total optimization impact."""
    if not bottlenecks:
        return "1x (no optimizations)"
    
    total_impact = 1.0
    for bottleneck in bottlenecks:
        if "x" in bottleneck.estimated_speedup:
            try:
                speedup = float(bottleneck.estimated_speedup.split('x')[0].split('-')[-1])
                total_impact *= speedup
            except (ValueError, IndexError):
                continue
    
    if total_impact >= 1000:
        return f"{total_impact:.0f}x (EXTREME)"
    elif total_impact >= 100:
        return f"{total_impact:.0f}x (ADVANCED)"
    elif total_impact >= 10:
        return f"{total_impact:.0f}x (ALGORITHMIC)"
    else:
        return f"{total_impact:.1f}x (QUICK_WINS)"

# Export all models
__all__ = [
    "OptimizationLevel",
    "OptimizationDomain", 
    "PerformanceBottleneck",
    "OptimizationStrategy",
    "PerformanceAnalysis",
    "BenchmarkResult",
    "OptimizationRequest",
    "OptimizationResult",
    "TestModel",
    "FunctionModel",
    "ArchonTaskRequest",
    "ArchonKnowledgeRequest",
    "validate_cpp_code",
    "estimate_optimization_impact"
]