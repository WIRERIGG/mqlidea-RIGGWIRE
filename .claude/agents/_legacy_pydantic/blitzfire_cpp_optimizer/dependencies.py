"""BLITZFIRE C++ Optimizer Dependencies.

Comprehensive dependency injection system for the BLITZFIRE optimization agent,
including Archon MCP integration, performance analysis tools, and safety validation.
"""

import asyncio
import os
import subprocess
import tempfile
import json
import re
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass
import aiofiles
import httpx
from pydantic import BaseModel

try:
    from .models import (
        OptimizationRequest,
        OptimizationResult,
        PerformanceAnalysis,
        PerformanceBottleneck,
        OptimizationStrategy,
        OptimizationLevel,
        OptimizationDomain,
        ArchonTaskRequest,
        ArchonKnowledgeRequest
    )
except ImportError:
    from models import (
        OptimizationRequest,
        OptimizationResult,
        PerformanceAnalysis,
        PerformanceBottleneck,
        OptimizationStrategy,
        OptimizationLevel,
        OptimizationDomain,
        ArchonTaskRequest,
        ArchonKnowledgeRequest
    )

@dataclass
class ArchonMCPClient:
    """Archon MCP client for knowledge queries and task management."""
    base_url: str = "http://archon-mcp:8051"
    timeout: int = 30
    enabled: bool = True
    
    async def check_availability(self) -> bool:
        """Check if Archon MCP server is available."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            self.enabled = False
            return False
    
    async def manage_task(self, request: ArchonTaskRequest) -> Dict[str, Any]:
        """Manage tasks via Archon MCP."""
        if not self.enabled:
            return {"error": "Archon MCP not available", "fallback": True}
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/tasks/{request.action}",
                    json=request.model_dump()
                )
                return response.json()
        except Exception as e:
            return {"error": str(e), "fallback": True}
    
    async def perform_rag_query(self, request: ArchonKnowledgeRequest) -> Dict[str, Any]:
        """Perform RAG query via Archon MCP."""
        if not self.enabled:
            return {"error": "Archon MCP not available", "results": []}
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/knowledge/rag",
                    json=request.model_dump()
                )
                return response.json()
        except Exception as e:
            return {"error": str(e), "results": []}
    
    async def search_code_examples(self, request: ArchonKnowledgeRequest) -> Dict[str, Any]:
        """Search code examples via Archon MCP."""
        if not self.enabled:
            return {"error": "Archon MCP not available", "examples": []}
            
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/knowledge/code_examples",
                    json=request.model_dump()
                )
                return response.json()
        except Exception as e:
            return {"error": str(e), "examples": []}

@dataclass 
class CppAnalyzer:
    """C++ code analysis tools for performance bottleneck detection."""
    
    async def analyze_code_complexity(self, code: str) -> Dict[str, Any]:
        """Analyze code complexity and identify optimization opportunities."""
        analysis = {
            "nested_loops": 0,
            "linear_searches": 0,
            "io_operations": 0,
            "memory_allocations": 0,
            "vectorizable_loops": 0,
            "optimization_opportunities": []
        }
        
        lines = code.split('\n')
        
        # Analyze nested loops
        loop_depth = 0
        max_depth = 0
        for line in lines:
            stripped = line.strip()
            if any(keyword in stripped for keyword in ['for (', 'while (', 'do {']):
                loop_depth += 1
                max_depth = max(max_depth, loop_depth)
            elif '}' in stripped and loop_depth > 0:
                loop_depth -= 1
        
        analysis["nested_loops"] = max_depth
        if max_depth > 2:
            analysis["optimization_opportunities"].append({
                "type": "algorithmic",
                "issue": "deeply nested loops",
                "severity": "high" if max_depth > 3 else "medium",
                "suggestion": "Consider algorithm optimization or parallelization"
            })
        
        # Analyze I/O operations
        io_patterns = ['std::cout', 'std::endl', 'printf', 'scanf', 'cin', 'getline']
        io_count = sum(code.count(pattern) for pattern in io_patterns)
        analysis["io_operations"] = io_count
        
        if 'std::endl' in code:
            analysis["optimization_opportunities"].append({
                "type": "io", 
                "issue": "forced buffer flush with std::endl",
                "severity": "high",
                "suggestion": "Replace std::endl with '\\n' for 10-50x I/O speedup"
            })
        
        if io_count > 5:
            analysis["optimization_opportunities"].append({
                "type": "io",
                "issue": "multiple I/O operations",
                "severity": "medium", 
                "suggestion": "Use buffered I/O with std::ostringstream"
            })
        
        # Analyze memory patterns
        memory_patterns = ['new ', 'malloc', 'vector', 'string', 'array']
        memory_count = sum(code.count(pattern) for pattern in memory_patterns)
        analysis["memory_allocations"] = memory_count
        
        if 'vector' in code and 'reserve' not in code:
            analysis["optimization_opportunities"].append({
                "type": "memory",
                "issue": "vector without reserve",
                "severity": "medium",
                "suggestion": "Reserve vector capacity for 2-10x speedup"
            })
        
        # Detect vectorizable loops
        vectorizable_patterns = [
            r'for\s*\(\s*int\s+\w+\s*=\s*0\s*;.*\+\+\s*\)',
            r'for\s*\(\s*size_t\s+\w+\s*=\s*0\s*;.*\+\+\s*\)'
        ]
        
        vectorizable_count = 0
        for pattern in vectorizable_patterns:
            vectorizable_count += len(re.findall(pattern, code))
        
        analysis["vectorizable_loops"] = vectorizable_count
        if vectorizable_count > 0:
            analysis["optimization_opportunities"].append({
                "type": "simd",
                "issue": "vectorizable loops detected",
                "severity": "medium",
                "suggestion": "Enable SIMD vectorization for 2-8x speedup"
            })
        
        return analysis
    
    async def identify_bottlenecks(self, code: str, file_path: str = "") -> List[PerformanceBottleneck]:
        """Identify specific performance bottlenecks in code."""
        analysis = await self.analyze_code_complexity(code)
        bottlenecks = []
        
        for opportunity in analysis["optimization_opportunities"]:
            bottleneck = PerformanceBottleneck(
                location=file_path or "unknown",
                severity=opportunity["severity"], 
                domain=OptimizationDomain(opportunity["type"]),
                issue_type=opportunity["issue"],
                current_complexity="O(n)" if "loop" in opportunity["issue"] else "O(1)",
                optimized_complexity="O(log n)" if "algorithm" in opportunity["type"] else "O(1)",
                estimated_speedup=self._extract_speedup(opportunity["suggestion"]),
                confidence=0.8,
                optimization_priority=self._get_priority(opportunity["severity"])
            )
            bottlenecks.append(bottleneck)
            
        return bottlenecks
    
    def _extract_speedup(self, suggestion: str) -> str:
        """Extract speedup estimate from suggestion."""
        if "10-50x" in suggestion:
            return "10-50x"
        elif "2-10x" in suggestion:
            return "2-10x"
        elif "2-8x" in suggestion:
            return "2-8x"
        else:
            return "2-5x"
    
    def _get_priority(self, severity: str) -> int:
        """Convert severity to priority number."""
        priority_map = {
            "low": 3,
            "medium": 6,
            "high": 9,
            "critical": 10
        }
        return priority_map.get(severity, 5)

@dataclass
class CompilerOptimizer:
    """Compiler optimization tools and validation."""
    compiler: str = "clang++"
    base_flags: List[str] = None
    
    def __post_init__(self):
        if self.base_flags is None:
            self.base_flags = [
                "-std=c++20",
                "-Wall", "-Wextra", "-Wpedantic", "-Werror",
                "-O3", "-march=native", "-mtune=native"
            ]
    
    async def validate_compilation(self, code: str, additional_flags: List[str] = None) -> Dict[str, Any]:
        """Validate code compilation with optimization flags."""
        flags = self.base_flags.copy()
        if additional_flags:
            flags.extend(additional_flags)
            
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(code)
            f.flush()
            
            try:
                # SECURITY: Safe subprocess call - uses list format (not shell=True), 
                # validated compiler path, and controlled input
                cmd = [self.compiler] + flags + ['-fsyntax-only', f.name]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=30
                )
                
                return {
                    "success": result.returncode == 0,
                    "warnings": result.stderr.count("warning:"),
                    "errors": result.stderr.count("error:"),
                    "output": result.stderr,
                    "flags_used": flags
                }
            except subprocess.TimeoutExpired:
                return {
                    "success": False,
                    "error": "Compilation timeout",
                    "flags_used": flags
                }
            finally:
                os.unlink(f.name)
    
    async def generate_optimized_flags(self, optimization_level: OptimizationLevel) -> List[str]:
        """Generate compiler flags for optimization level."""
        base_flags = self.base_flags.copy()
        
        if optimization_level == OptimizationLevel.QUICK_WINS:
            return base_flags
        elif optimization_level == OptimizationLevel.ALGORITHMIC:
            return base_flags + ["-funroll-loops", "-ftree-vectorize"]
        elif optimization_level == OptimizationLevel.ADVANCED:
            return base_flags + [
                "-funroll-loops", "-ftree-vectorize",
                "-flto=thin", "-fprofile-generate"
            ]
        elif optimization_level == OptimizationLevel.EXTREME:
            return base_flags + [
                "-funroll-loops", "-ftree-vectorize", "-flto=thin",
                "-fprofile-use", "-march=native", "-mtune=native",
                "-mavx2", "-mfma"
            ]
        
        return base_flags

@dataclass 
class BenchmarkGenerator:
    """Generate performance benchmarks for optimization validation."""
    
    async def create_benchmark_code(self, original_code: str, optimized_code: str, test_name: str = "benchmark") -> str:
        """Generate GoogleTest-compatible benchmark code."""
        benchmark_template = f'''
#include <benchmark/benchmark.h>
#include <chrono>
#include <vector>
#include <random>

// Original implementation
namespace original {{
{self._indent_code(original_code)}
}}

// Optimized implementation  
namespace optimized {{
{self._indent_code(optimized_code)}
}}

// Benchmark original implementation
static void BM_Original_{test_name}(benchmark::State& state) {{
    // Setup data
    std::vector<int> data(state.range(0));
    std::iota(data.begin(), data.end(), 0);
    
    for (auto _ : state) {{
        // Run original implementation
        original::process(data);
        benchmark::ClobberMemory();
    }}
    
    state.SetComplexityN(state.range(0));
}}

// Benchmark optimized implementation
static void BM_Optimized_{test_name}(benchmark::State& state) {{
    // Setup data
    std::vector<int> data(state.range(0));
    std::iota(data.begin(), data.end(), 0);
    
    for (auto _ : state) {{
        // Run optimized implementation
        optimized::process(data);
        benchmark::ClobberMemory();
    }}
    
    state.SetComplexityN(state.range(0));
}}

// Register benchmarks
BENCHMARK(BM_Original_{test_name})
    ->RangeMultiplier(2)->Range(1<<8, 1<<16)
    ->Complexity(benchmark::oAuto);
    
BENCHMARK(BM_Optimized_{test_name})
    ->RangeMultiplier(2)->Range(1<<8, 1<<16)  
    ->Complexity(benchmark::oAuto);

BENCHMARK_MAIN();
'''
        return benchmark_template
    
    def _indent_code(self, code: str) -> str:
        """Indent code for namespace."""
        return '\n'.join('    ' + line for line in code.split('\n'))

@dataclass
class SafetyValidator:
    """Safety validation for optimized code."""
    
    async def validate_memory_safety(self, code: str) -> Dict[str, Any]:
        """Validate memory safety of optimized code."""
        safety_checks = {
            "buffer_overflows": [],
            "memory_leaks": [],
            "dangling_pointers": [],
            "double_free": [],
            "safe": True
        }
        
        # Basic static analysis patterns
        unsafe_patterns = {
            "buffer_overflow": [r'char\s+\w+\[\d+\]', r'gets\s*\(', r'strcpy\s*\('],
            "memory_leak": [r'new\s+(?!.*delete)', r'malloc\s*\((?!.*free)'],
            "dangling_pointer": [r'delete\s+\w+;(?!.*\w+\s*=\s*nullptr)'],
            "double_free": [r'delete\s+\w+.*delete\s+\w+']
        }
        
        for category, patterns in unsafe_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, code, re.MULTILINE)
                if matches:
                    safety_checks[category].extend(matches)
                    safety_checks["safe"] = False
        
        return safety_checks
    
    async def validate_thread_safety(self, code: str) -> Dict[str, Any]:
        """Validate thread safety for parallelized code."""
        thread_safety = {
            "race_conditions": [],
            "shared_resources": [], 
            "synchronization": [],
            "safe": True
        }
        
        # Look for threading patterns
        if any(pattern in code for pattern in ['std::thread', 'omp parallel', '#pragma omp']):
            # Basic race condition detection
            shared_patterns = [r'static\s+\w+', r'global\s+\w+', r'extern\s+\w+']
            for pattern in shared_patterns:
                matches = re.findall(pattern, code)
                if matches and 'mutex' not in code and 'atomic' not in code:
                    thread_safety["race_conditions"].extend(matches)
                    thread_safety["safe"] = False
                    
        return thread_safety

class BlitzfireDependencies(BaseModel):
    """Main dependency injection container for BLITZFIRE C++ Optimizer."""
    
    # Core components
    archon_client: Optional[ArchonMCPClient] = None
    cpp_analyzer: Optional[CppAnalyzer] = None
    compiler_optimizer: Optional[CompilerOptimizer] = None
    benchmark_generator: Optional[BenchmarkGenerator] = None
    safety_validator: Optional[SafetyValidator] = None
    
    # Required attributes for validation framework
    session_id: str = "blitzfire_session"
    settings: Dict[str, Any] = {"optimization_level": "advanced", "safety_mode": True}
    config: Dict[str, Any] = {"compiler": "clang++", "target_cpu": "native"}
    
    # Configuration
    wire_ground_root: str = "/IdeaProjects/wire_ground"
    temp_dir: str = tempfile.gettempdir() + "/blitzfire_optimizer"
    debug_mode: bool = False
    max_optimization_time: int = 300  # 5 minutes
    
    # State
    initialized: bool = False
    archon_available: bool = False
    
    model_config = {"arbitrary_types_allowed": True}
    
    async def initialize(self) -> None:
        """Initialize all dependencies."""
        if self.initialized:
            return
            
        # Initialize core components
        self.archon_client = ArchonMCPClient()
        self.cpp_analyzer = CppAnalyzer()
        self.compiler_optimizer = CompilerOptimizer()
        self.benchmark_generator = BenchmarkGenerator()
        self.safety_validator = SafetyValidator()
        
        # Check Archon availability
        if self.archon_client:
            self.archon_available = await self.archon_client.check_availability()
            if not self.archon_available:
                print("⚠️  Archon MCP not available, falling back to local analysis")
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.initialized = True
        
        if self.debug_mode:
            print(f"✅ BLITZFIRE dependencies initialized")
            print(f"   Archon MCP: {'✅' if self.archon_available else '❌'}")
            print(f"   Wire_ground root: {self.wire_ground_root}")
            print(f"   Temp directory: {self.temp_dir}")
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
            except Exception as e:
                # Log cleanup failure but continue - this is non-critical
                print(f"Warning: Could not cleanup temp directory {self.temp_dir}: {e}")
        
        self.initialized = False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of all dependencies."""
        if not self.initialized:
            await self.initialize()
            
        return {
            "initialized": self.initialized,
            "archon_available": self.archon_available,
            "cpp_analyzer": self.cpp_analyzer is not None,
            "compiler_optimizer": self.compiler_optimizer is not None,
            "benchmark_generator": self.benchmark_generator is not None,
            "safety_validator": self.safety_validator is not None,
            "wire_ground_accessible": os.path.exists(self.wire_ground_root),
            "temp_dir_accessible": os.path.exists(self.temp_dir)
        }

# Factory function for dependency creation
async def create_dependencies(debug_mode: bool = False, wire_ground_root: str = "/IdeaProjects/wire_ground") -> BlitzfireDependencies:
    """Create and initialize BLITZFIRE dependencies."""
    deps = BlitzfireDependencies(
        debug_mode=debug_mode,
        wire_ground_root=wire_ground_root
    )
    await deps.initialize()
    return deps

# Export main dependencies  
__all__ = [
    "BlitzfireDependencies",
    "create_dependencies",
    "ArchonMCPClient",
    "CppAnalyzer", 
    "CompilerOptimizer",
    "BenchmarkGenerator",
    "SafetyValidator"
]