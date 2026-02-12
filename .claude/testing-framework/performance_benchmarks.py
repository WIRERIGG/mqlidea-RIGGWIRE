"""Performance Benchmarking Framework for Pydantic AI Agents

This module provides performance benchmarking utilities for all four agents:
- valgrind_memory_ai_agent
- never_fail_build_resolver
- blitzfire_cpp_optimizer
- clang_tidy_ai_agent

Usage:
    from performance_benchmarks import AgentPerformanceBenchmark, BenchmarkRunner
    
    benchmark = AgentPerformanceBenchmark("my_agent")
    with benchmark.measure("operation_name"):
        # Your code here
        pass
    
    results = benchmark.get_results()
"""

import time
import psutil
import asyncio
import functools
import statistics
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager, asynccontextmanager
from pathlib import Path
import json
import logging
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Single benchmark result."""
    operation_name: str
    execution_time: float
    memory_usage: float  # MB
    cpu_percent: float
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_name': self.operation_name,
            'execution_time': self.execution_time,
            'memory_usage': self.memory_usage,
            'cpu_percent': self.cpu_percent,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class BenchmarkSummary:
    """Summary of multiple benchmark results."""
    operation_name: str
    total_runs: int
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    std_execution_time: float
    avg_memory_usage: float
    max_memory_usage: float
    avg_cpu_percent: float
    max_cpu_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation_name': self.operation_name,
            'total_runs': self.total_runs,
            'avg_execution_time': self.avg_execution_time,
            'min_execution_time': self.min_execution_time,
            'max_execution_time': self.max_execution_time,
            'std_execution_time': self.std_execution_time,
            'avg_memory_usage': self.avg_memory_usage,
            'max_memory_usage': self.max_memory_usage,
            'avg_cpu_percent': self.avg_cpu_percent,
            'max_cpu_percent': self.max_cpu_percent
        }


class SystemMonitor:
    """Monitor system resources during benchmarks."""
    
    def __init__(self, pid: Optional[int] = None):
        self.pid = pid or psutil.Process().pid
        self.process = psutil.Process(self.pid)
        self.initial_memory = self.get_memory_usage()
        self.initial_cpu_percent = self.process.cpu_percent()
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024
    
    def get_cpu_percent(self) -> float:
        """Get current CPU percentage."""
        return self.process.cpu_percent(interval=0.1)
    
    def get_current_stats(self) -> Dict[str, float]:
        """Get current system statistics."""
        return {
            'memory_usage': self.get_memory_usage(),
            'cpu_percent': self.get_cpu_percent()
        }


class AgentPerformanceBenchmark:
    """Performance benchmark tracker for Pydantic AI agents."""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.results: List[BenchmarkResult] = []
        self.monitor = SystemMonitor()
        self.logger = logging.getLogger(f"{__name__}.{agent_name}")
        
        # Performance thresholds
        self.thresholds = {
            'max_execution_time': 5.0,  # seconds
            'max_memory_usage': 500.0,  # MB
            'max_cpu_percent': 90.0     # percentage
        }
    
    def set_threshold(self, metric: str, value: float):
        """Set performance threshold for a metric."""
        if metric in self.thresholds:
            self.thresholds[metric] = value
        else:
            raise ValueError(f"Unknown threshold metric: {metric}")
    
    @contextmanager
    def measure(self, operation_name: str, **metadata):
        """Context manager for measuring operation performance."""
        start_time = time.time()
        start_stats = self.monitor.get_current_stats()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_stats = self.monitor.get_current_stats()
            
            result = BenchmarkResult(
                operation_name=operation_name,
                execution_time=end_time - start_time,
                memory_usage=end_stats['memory_usage'] - start_stats['memory_usage'],
                cpu_percent=end_stats['cpu_percent'],
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self.results.append(result)
            self.logger.info(f"Measured {operation_name}: {result.execution_time:.3f}s")
    
    @asynccontextmanager
    async def measure_async(self, operation_name: str, **metadata):
        """Async context manager for measuring operation performance."""
        start_time = time.time()
        start_stats = self.monitor.get_current_stats()
        
        try:
            yield
        finally:
            end_time = time.time()
            end_stats = self.monitor.get_current_stats()
            
            result = BenchmarkResult(
                operation_name=operation_name,
                execution_time=end_time - start_time,
                memory_usage=end_stats['memory_usage'] - start_stats['memory_usage'],
                cpu_percent=end_stats['cpu_percent'],
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self.results.append(result)
            self.logger.info(f"Measured {operation_name} (async): {result.execution_time:.3f}s")
    
    def measure_function(self, func: Callable, operation_name: str = None, **metadata):
        """Decorator for measuring function performance."""
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self.measure(op_name, **metadata):
                return func(*args, **kwargs)
        return wrapper
    
    def measure_async_function(self, func: Callable, operation_name: str = None, **metadata):
        """Decorator for measuring async function performance."""
        op_name = operation_name or func.__name__
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with self.measure_async(op_name, **metadata):
                return await func(*args, **kwargs)
        return wrapper
    
    def get_results(self, operation_name: Optional[str] = None) -> List[BenchmarkResult]:
        """Get benchmark results, optionally filtered by operation name."""
        if operation_name:
            return [r for r in self.results if r.operation_name == operation_name]
        return self.results.copy()
    
    def get_summary(self, operation_name: Optional[str] = None) -> Dict[str, BenchmarkSummary]:
        """Get summary statistics for operations."""
        results = self.get_results(operation_name)
        
        if not results:
            return {}
        
        # Group by operation name
        operations = {}
        for result in results:
            if result.operation_name not in operations:
                operations[result.operation_name] = []
            operations[result.operation_name].append(result)
        
        # Calculate summaries
        summaries = {}
        for op_name, op_results in operations.items():
            execution_times = [r.execution_time for r in op_results]
            memory_usages = [r.memory_usage for r in op_results]
            cpu_percents = [r.cpu_percent for r in op_results]
            
            summaries[op_name] = BenchmarkSummary(
                operation_name=op_name,
                total_runs=len(op_results),
                avg_execution_time=statistics.mean(execution_times),
                min_execution_time=min(execution_times),
                max_execution_time=max(execution_times),
                std_execution_time=statistics.stdev(execution_times) if len(execution_times) > 1 else 0.0,
                avg_memory_usage=statistics.mean(memory_usages),
                max_memory_usage=max(memory_usages),
                avg_cpu_percent=statistics.mean(cpu_percents),
                max_cpu_percent=max(cpu_percents)
            )
        
        return summaries
    
    def check_thresholds(self) -> Dict[str, List[BenchmarkResult]]:
        """Check results against performance thresholds."""
        violations = {
            'execution_time': [],
            'memory_usage': [],
            'cpu_percent': []
        }
        
        for result in self.results:
            if result.execution_time > self.thresholds['max_execution_time']:
                violations['execution_time'].append(result)
            
            if result.memory_usage > self.thresholds['max_memory_usage']:
                violations['memory_usage'].append(result)
            
            if result.cpu_percent > self.thresholds['max_cpu_percent']:
                violations['cpu_percent'].append(result)
        
        return violations
    
    def save_results(self, file_path: Union[str, Path]):
        """Save benchmark results to JSON file."""
        results_data = {
            'agent_name': self.agent_name,
            'thresholds': self.thresholds,
            'results': [r.to_dict() for r in self.results],
            'summaries': {k: v.to_dict() for k, v in self.get_summary().items()}
        }
        
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(results_data, f, indent=2, default=str)
        
        self.logger.info(f"Saved benchmark results to {path}")
    
    def clear_results(self):
        """Clear all benchmark results."""
        self.results.clear()
        self.logger.info("Cleared all benchmark results")


class BenchmarkRunner:
    """Runner for executing benchmark suites."""
    
    def __init__(self):
        self.benchmarks: Dict[str, AgentPerformanceBenchmark] = {}
        self.logger = logging.getLogger(__name__)
    
    def add_agent(self, agent_name: str) -> AgentPerformanceBenchmark:
        """Add an agent for benchmarking."""
        benchmark = AgentPerformanceBenchmark(agent_name)
        self.benchmarks[agent_name] = benchmark
        return benchmark
    
    def get_agent_benchmark(self, agent_name: str) -> Optional[AgentPerformanceBenchmark]:
        """Get benchmark for an agent."""
        return self.benchmarks.get(agent_name)
    
    def run_benchmark_suite(self, suite_functions: List[Callable]):
        """Run a suite of benchmark functions."""
        self.logger.info(f"Running benchmark suite with {len(suite_functions)} functions")
        
        start_time = time.time()
        
        for benchmark_func in suite_functions:
            try:
                self.logger.info(f"Running benchmark: {benchmark_func.__name__}")
                benchmark_func()
            except Exception as e:
                self.logger.error(f"Benchmark {benchmark_func.__name__} failed: {e}")
        
        total_time = time.time() - start_time
        self.logger.info(f"Completed benchmark suite in {total_time:.3f}s")
    
    async def run_async_benchmark_suite(self, suite_functions: List[Callable]):
        """Run a suite of async benchmark functions."""
        self.logger.info(f"Running async benchmark suite with {len(suite_functions)} functions")
        
        start_time = time.time()
        
        for benchmark_func in suite_functions:
            try:
                self.logger.info(f"Running async benchmark: {benchmark_func.__name__}")
                await benchmark_func()
            except Exception as e:
                self.logger.error(f"Async benchmark {benchmark_func.__name__} failed: {e}")
        
        total_time = time.time() - start_time
        self.logger.info(f"Completed async benchmark suite in {total_time:.3f}s")
    
    def generate_report(self, output_path: Union[str, Path]):
        """Generate comprehensive benchmark report."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'agents': {}
        }
        
        for agent_name, benchmark in self.benchmarks.items():
            agent_data = {
                'thresholds': benchmark.thresholds,
                'results_count': len(benchmark.results),
                'summaries': {k: v.to_dict() for k, v in benchmark.get_summary().items()},
                'threshold_violations': {
                    k: len(v) for k, v in benchmark.check_thresholds().items()
                }
            }
            report_data['agents'][agent_name] = agent_data
        
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        self.logger.info(f"Generated benchmark report: {path}")
    
    def save_all_results(self, output_dir: Union[str, Path]):
        """Save all benchmark results to separate files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for agent_name, benchmark in self.benchmarks.items():
            file_path = output_path / f"{agent_name}_benchmark_results.json"
            benchmark.save_results(file_path)
        
        # Generate combined report
        self.generate_report(output_path / "benchmark_report.json")


# =============================================================================
# PREDEFINED BENCHMARK UTILITIES
# =============================================================================

class StandardBenchmarks:
    """Standard benchmark operations for Pydantic AI agents."""
    
    @staticmethod
    def benchmark_agent_initialization(agent_class, benchmark: AgentPerformanceBenchmark, **init_kwargs):
        """Benchmark agent initialization."""
        with benchmark.measure("agent_initialization"):
            agent = agent_class(**init_kwargs)
        return agent
    
    @staticmethod
    async def benchmark_simple_query(agent, benchmark: AgentPerformanceBenchmark, query: str = "Hello"):
        """Benchmark simple agent query."""
        async with benchmark.measure_async("simple_query"):
            result = await agent.run(query)
        return result
    
    @staticmethod
    async def benchmark_complex_query(agent, benchmark: AgentPerformanceBenchmark, 
                                    query: str = "Analyze this complex problem..."):
        """Benchmark complex agent query."""
        async with benchmark.measure_async("complex_query"):
            result = await agent.run(query)
        return result
    
    @staticmethod
    def benchmark_file_processing(processing_func, benchmark: AgentPerformanceBenchmark, 
                                file_path: Path, **kwargs):
        """Benchmark file processing operations."""
        with benchmark.measure("file_processing", file_size=file_path.stat().st_size):
            result = processing_func(file_path, **kwargs)
        return result
    
    @staticmethod
    def benchmark_batch_processing(processing_func, benchmark: AgentPerformanceBenchmark,
                                 items: List[Any], **kwargs):
        """Benchmark batch processing operations."""
        with benchmark.measure("batch_processing", batch_size=len(items)):
            results = []
            for item in items:
                results.append(processing_func(item, **kwargs))
        return results


# Example usage and configuration
AGENT_PERFORMANCE_THRESHOLDS = {
    'valgrind_memory_ai_agent': {
        'max_execution_time': 10.0,  # Valgrind operations can be slow
        'max_memory_usage': 200.0,
        'max_cpu_percent': 85.0
    },
    'never_fail_build_resolver': {
        'max_execution_time': 15.0,  # Build operations can take time
        'max_memory_usage': 300.0,
        'max_cpu_percent': 90.0
    },
    'blitzfire_cpp_optimizer': {
        'max_execution_time': 8.0,   # Optimization should be reasonably fast
        'max_memory_usage': 400.0,   # May need more memory for complex analysis
        'max_cpu_percent': 95.0
    },
    'clang_tidy_ai_agent': {
        'max_execution_time': 12.0,  # Static analysis can take time
        'max_memory_usage': 250.0,
        'max_cpu_percent': 88.0
    }
}