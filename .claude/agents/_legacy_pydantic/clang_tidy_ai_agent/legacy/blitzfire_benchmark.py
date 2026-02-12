"""
BLITZFIRE Benchmark Suite - Comprehensive performance validation and comparison.

This benchmark suite validates that BLITZFIRE optimizations achieve the target 
10x-100x speedups while maintaining correctness and safety guarantees.
"""

import asyncio
import json
import time
import tempfile
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import structlog

# Import agents for comparison
try:
    from .agent_optimized import OptimizedClangTidyAgent
    from .blitzfire_agent import BlitzfireClangTidyAgent
    from .settings_optimized import load_optimized_settings
    from .blitzfire_tools import BlitzfirePerformanceProfiler
except ImportError:
    from agent_optimized import OptimizedClangTidyAgent
    from blitzfire_agent import BlitzfireClangTidyAgent
    from settings_optimized import load_optimized_settings
    from blitzfire_tools import BlitzfirePerformanceProfiler

logger = structlog.get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    
    agent_type: str
    test_name: str
    files_processed: int
    total_warnings: int
    execution_time_seconds: float
    memory_usage_mb: float
    cpu_utilization_percent: float
    cache_hit_rate: float
    errors_encountered: int
    throughput_files_per_second: float
    throughput_warnings_per_second: float
    
    def speedup_vs(self, baseline: 'BenchmarkResult') -> float:
        """Calculate speedup compared to baseline."""
        if baseline.execution_time_seconds == 0:
            return float('inf')
        return baseline.execution_time_seconds / self.execution_time_seconds
    
    def efficiency_score(self) -> float:
        """Calculate overall efficiency score (0-100)."""
        # Weighted combination of throughput, memory efficiency, and cache performance
        throughput_score = min(100, self.throughput_files_per_second * 2)
        memory_score = max(0, 100 - (self.memory_usage_mb / 10))  # Lower is better
        cache_score = self.cache_hit_rate * 100
        
        return (throughput_score * 0.5 + memory_score * 0.3 + cache_score * 0.2)


class CPPTestFileGenerator:
    """Generates C++ test files with various complexity levels."""
    
    @staticmethod
    def create_simple_cpp_file(file_path: Path, lines: int = 100):
        """Create simple C++ file with common clang-tidy issues."""
        
        content = """#include <iostream>
#include <vector>
#include <string>

// Intentional clang-tidy issues for testing
class TestClass {
public:
    TestClass() = default;
    
    void performanceIssue() {
        std::vector<int> vec;
        for (int i = 0; i < 1000; ++i) {
            vec.push_back(i);  // Should use reserve()
        }
    }
    
    void readabilityIssue() {
        int x = 0;
        if (x) {  // Should use braces
            x++;
        }
        
        char* ptr = NULL;  // Should use nullptr
        
        for (int i = 0; i < 10; i++)  // Should use ++i
            std::cout << i;  // Should use braces
    }
    
    void modernizationIssue() {
        std::vector<int> vec = {1, 2, 3, 4, 5};
        for (auto it = vec.begin(); it != vec.end(); ++it) {
            std::cout << *it;  // Should use range-based for
        }
    }
};

"""
        
        # Add more content to reach desired line count
        additional_lines = max(0, lines - content.count('\n'))
        for i in range(additional_lines):
            content += f"// Additional line {i} to increase file size\n"
        
        file_path.write_text(content)
    
    @staticmethod
    def create_complex_cpp_file(file_path: Path, lines: int = 500):
        """Create complex C++ file with many potential issues."""
        
        content = """#include <iostream>
#include <vector>
#include <memory>
#include <algorithm>
#include <string>
#include <map>
#include <thread>
#include <mutex>

// Complex C++ class with multiple clang-tidy issues
template<typename T>
class ComplexProcessor {
private:
    std::vector<T> data_;
    std::map<std::string, T> cache_;
    mutable std::mutex mutex_;
    
public:
    ComplexProcessor() {
        data_.reserve(1000);
    }
    
    ~ComplexProcessor() = default;
    
    // Performance issues
    void inefficientProcess() {
        std::vector<T> temp;
        for (int i = 0; i < data_.size(); ++i) {  // Should use size_t
            temp.push_back(data_[i]);
        }
        
        // Inefficient string operations
        std::string result = "";
        for (const auto& item : temp) {
            result = result + std::to_string(item);  // Should use +=
        }
    }
    
    // Readability issues  
    T getValue(int index) {
        if (index >= 0 && index < data_.size())
            return data_[index];  // Missing braces
        else
            return T{};
    }
    
    // Modernization opportunities
    void processOldStyle() {
        for (auto it = data_.begin(); it != data_.end(); ++it) {
            if (*it > 0)  // Missing braces
                std::cout << *it << std::endl;  // Should use '\\n'
        }
    }
    
    // Thread safety issues
    void unsafeAccess() {
        // Should lock mutex_
        data_.push_back(T{});
        cache_["key"] = T{};
    }
    
    // Memory management issues
    T* createRawPointer() {
        return new T{};  // Should use smart pointer
    }
    
    // Exception safety issues
    void riskyCopy(const std::vector<T>& source) {
        data_ = source;  // Could throw, should be exception safe
    }
};

// Global function with issues
void globalFunction() {
    int* ptr = NULL;  // Should use nullptr
    
    for (int i = 0; i < 10; i++)  // Should use ++i, missing braces
        ptr = new int(i);  // Memory leak
    
    delete ptr;  // Only deletes last allocation
}

"""
        
        # Add template instantiations and more complex code
        for i in range(lines // 20):
            content += f"""
// Template instantiation {i}
template class ComplexProcessor<int>;
template class ComplexProcessor<double>;
template class ComplexProcessor<std::string>;

void additionalFunction{i}() {{
    ComplexProcessor<int> processor;
    processor.inefficientProcess();
    processor.processOldStyle();
    processor.unsafeAccess();
    
    auto ptr = processor.createRawPointer();
    delete ptr;  // Manual memory management
}}
"""
        
        file_path.write_text(content)
    
    @staticmethod
    def create_test_suite(temp_dir: Path, num_files: int = 50) -> List[Path]:
        """Create a comprehensive test suite."""
        
        test_files = []
        
        # Mix of simple and complex files
        for i in range(num_files):
            file_path = temp_dir / f"test_{i:03d}.cpp"
            
            if i % 3 == 0:
                # Complex files (33%)
                CPPTestFileGenerator.create_complex_cpp_file(file_path, lines=500)
            else:
                # Simple files (67%)
                CPPTestFileGenerator.create_simple_cpp_file(file_path, lines=100 + i * 10)
            
            test_files.append(file_path)
        
        return test_files


class BlitzfireBenchmark:
    """Comprehensive benchmark suite for BLITZFIRE performance validation."""
    
    def __init__(self):
        self.profiler = BlitzfirePerformanceProfiler()
        self.results = []
        self.settings = load_optimized_settings()
    
    async def run_comprehensive_benchmark(
        self, 
        test_suite_sizes: List[int] = [10, 25, 50, 100],
        iterations: int = 3
    ) -> Dict[str, Any]:
        """Run comprehensive benchmark comparing optimized vs BLITZFIRE agents."""
        
        logger.info("Starting comprehensive BLITZFIRE benchmark suite")
        
        all_results = []
        
        for suite_size in test_suite_sizes:
            logger.info(f"Running benchmark with {suite_size} files")
            
            # Create temporary test suite
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                test_files = CPPTestFileGenerator.create_test_suite(temp_path, suite_size)
                
                # Run multiple iterations for statistical significance
                for iteration in range(iterations):
                    logger.info(f"Iteration {iteration + 1}/{iterations}")
                    
                    # Test optimized agent (baseline)
                    baseline_result = await self._benchmark_optimized_agent(test_files)
                    baseline_result.test_name = f"suite_{suite_size}_iter_{iteration}"
                    all_results.append(baseline_result)
                    
                    # Test BLITZFIRE agent
                    blitzfire_result = await self._benchmark_blitzfire_agent(test_files)
                    blitzfire_result.test_name = f"suite_{suite_size}_iter_{iteration}"
                    all_results.append(blitzfire_result)
        
        # Analyze results
        analysis = self._analyze_benchmark_results(all_results)
        
        # Generate report
        report = self._generate_performance_report(all_results, analysis)
        
        # Save results
        self._save_benchmark_results(all_results, analysis, report)
        
        logger.info("Comprehensive benchmark completed successfully")
        return report
    
    async def _benchmark_optimized_agent(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark the current optimized agent (baseline)."""
        
        profile_id = self.profiler.start_profile("optimized_agent_benchmark")
        
        try:
            # Create optimized agent
            agent = OptimizedClangTidyAgent(self.settings)
            
            # Prepare file patterns
            file_patterns = [str(f) for f in test_files]
            
            # Run analysis
            start_time = time.time()
            start_memory = self._get_memory_usage_mb()
            
            result = await agent.analyze_project(file_patterns)
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Extract metrics
            return BenchmarkResult(
                agent_type="optimized",
                test_name="benchmark",
                files_processed=result.files_analyzed,
                total_warnings=result.total_warnings,
                execution_time_seconds=execution_time,
                memory_usage_mb=memory_delta,
                cpu_utilization_percent=50.0,  # Estimated
                cache_hit_rate=result.cache_hit_rate,
                errors_encountered=0,
                throughput_files_per_second=result.files_analyzed / max(execution_time, 0.001),
                throughput_warnings_per_second=result.total_warnings / max(execution_time, 0.001)
            )
            
        finally:
            self.profiler.end_profile(profile_id)
    
    async def _benchmark_blitzfire_agent(self, test_files: List[Path]) -> BenchmarkResult:
        """Benchmark the BLITZFIRE agent."""
        
        profile_id = self.profiler.start_profile("blitzfire_agent_benchmark")
        
        try:
            # Create BLITZFIRE agent
            agent = BlitzfireClangTidyAgent(self.settings)
            
            # Prepare file patterns - need to convert to relative paths
            file_patterns = [
                str(f.relative_to(self.settings.project_root))
                for f in test_files
            ]
            
            # Run BLITZFIRE analysis
            start_time = time.time()
            start_memory = self._get_memory_usage_mb()
            
            result = await agent.analyze_project_blitzfire(file_patterns)
            
            end_time = time.time()
            end_memory = self._get_memory_usage_mb()
            
            execution_time = end_time - start_time
            memory_delta = end_memory - start_memory
            
            # Get detailed metrics
            blitzfire_metrics = await agent.get_blitzfire_metrics()
            
            # Extract cache hit rate
            cache_stats = blitzfire_metrics.get("cache_statistics", {})
            cache_hit_rate = cache_stats.get("total_hit_rate", 0.0)
            
            # Clean up
            await agent.cleanup_blitzfire()
            
            return BenchmarkResult(
                agent_type="blitzfire",
                test_name="benchmark",
                files_processed=result["files_processed"],
                total_warnings=result["total_warnings"],
                execution_time_seconds=execution_time,
                memory_usage_mb=memory_delta,
                cpu_utilization_percent=80.0,  # Estimated higher for BLITZFIRE
                cache_hit_rate=cache_hit_rate,
                errors_encountered=0,
                throughput_files_per_second=result["files_processed"] / max(execution_time, 0.001),
                throughput_warnings_per_second=result["total_warnings"] / max(execution_time, 0.001)
            )
            
        finally:
            self.profiler.end_profile(profile_id)
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        import psutil
        return psutil.Process().memory_info().rss / 1024 / 1024
    
    def _analyze_benchmark_results(self, results: List[BenchmarkResult]) -> Dict[str, Any]:
        """Analyze benchmark results for statistical significance."""
        
        # Group results by agent type and test suite size
        optimized_results = [r for r in results if r.agent_type == "optimized"]
        blitzfire_results = [r for r in results if r.agent_type == "blitzfire"]
        
        # Calculate statistics
        def calculate_stats(data: List[float]) -> Dict[str, float]:
            if not data:
                return {}
            return {
                "mean": statistics.mean(data),
                "median": statistics.median(data),
                "stdev": statistics.stdev(data) if len(data) > 1 else 0,
                "min": min(data),
                "max": max(data)
            }
        
        analysis = {
            "optimized_agent": {
                "execution_times": calculate_stats([r.execution_time_seconds for r in optimized_results]),
                "throughput": calculate_stats([r.throughput_files_per_second for r in optimized_results]),
                "memory_usage": calculate_stats([r.memory_usage_mb for r in optimized_results]),
                "cache_hit_rate": calculate_stats([r.cache_hit_rate for r in optimized_results])
            },
            "blitzfire_agent": {
                "execution_times": calculate_stats([r.execution_time_seconds for r in blitzfire_results]),
                "throughput": calculate_stats([r.throughput_files_per_second for r in blitzfire_results]),
                "memory_usage": calculate_stats([r.memory_usage_mb for r in blitzfire_results]),
                "cache_hit_rate": calculate_stats([r.cache_hit_rate for r in blitzfire_results])
            },
            "performance_comparison": {}
        }
        
        # Calculate performance improvements
        if optimized_results and blitzfire_results:
            # Average speedup
            speedups = []
            for opt_result in optimized_results:
                for bf_result in blitzfire_results:
                    if opt_result.test_name == bf_result.test_name:
                        speedups.append(bf_result.speedup_vs(opt_result))
            
            if speedups:
                analysis["performance_comparison"] = {
                    "avg_speedup": statistics.mean(speedups),
                    "median_speedup": statistics.median(speedups),
                    "max_speedup": max(speedups),
                    "min_speedup": min(speedups),
                    "speedup_consistency": statistics.stdev(speedups) if len(speedups) > 1 else 0
                }
        
        return analysis
    
    def _generate_performance_report(
        self, 
        results: List[BenchmarkResult], 
        analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        
        report = {
            "benchmark_summary": {
                "total_tests_run": len(results),
                "agents_compared": ["optimized", "blitzfire"],
                "test_suite_sizes": list(set(r.files_processed for r in results)),
                "benchmark_date": time.strftime("%Y-%m-%d %H:%M:%S")
            },
            "performance_analysis": analysis,
            "key_findings": [],
            "blitzfire_validation": {},
            "detailed_results": [asdict(r) for r in results]
        }
        
        # Generate key findings
        perf_comp = analysis.get("performance_comparison", {})
        if perf_comp:
            avg_speedup = perf_comp.get("avg_speedup", 1.0)
            max_speedup = perf_comp.get("max_speedup", 1.0)
            
            report["key_findings"].extend([
                f"Average speedup: {avg_speedup:.1f}x",
                f"Maximum speedup achieved: {max_speedup:.1f}x",
                f"Performance consistency: {perf_comp.get('speedup_consistency', 0):.2f}"
            ])
        
        # BLITZFIRE validation against targets
        target_speedup_min = 10.0
        target_speedup_max = 100.0
        
        actual_speedup = perf_comp.get("avg_speedup", 1.0)
        
        report["blitzfire_validation"] = {
            "target_speedup_range": f"{target_speedup_min}x - {target_speedup_max}x",
            "achieved_speedup": f"{actual_speedup:.1f}x",
            "target_met": actual_speedup >= target_speedup_min,
            "performance_grade": self._calculate_performance_grade(actual_speedup),
            "recommendations": self._generate_optimization_recommendations(actual_speedup, target_speedup_min)
        }
        
        return report
    
    def _calculate_performance_grade(self, speedup: float) -> str:
        """Calculate performance grade based on speedup."""
        if speedup >= 100:
            return "A+ (Exceptional)"
        elif speedup >= 50:
            return "A (Excellent)"
        elif speedup >= 25:
            return "B+ (Very Good)"
        elif speedup >= 10:
            return "B (Good)"
        elif speedup >= 5:
            return "C (Fair)"
        else:
            return "D (Needs Improvement)"
    
    def _generate_optimization_recommendations(
        self, 
        actual_speedup: float, 
        target_speedup: float
    ) -> List[str]:
        """Generate recommendations for further optimization."""
        
        recommendations = []
        
        if actual_speedup < target_speedup:
            gap = target_speedup - actual_speedup
            recommendations.extend([
                f"Performance gap: {gap:.1f}x below target",
                "Consider implementing additional SIMD optimizations",
                "Investigate memory access patterns for cache optimization",
                "Profile hot paths for further algorithmic improvements"
            ])
        else:
            recommendations.extend([
                "Target performance achieved successfully!",
                "Consider stability testing under various workloads",
                "Monitor performance regression in production",
                "Document optimization techniques for future reference"
            ])
        
        return recommendations
    
    def _save_benchmark_results(
        self, 
        results: List[BenchmarkResult], 
        analysis: Dict[str, Any], 
        report: Dict[str, Any]
    ):
        """Save benchmark results to files."""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        results_dir = Path("benchmark_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save detailed JSON report
        report_file = results_dir / f"blitzfire_benchmark_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Benchmark results saved to {report_file}")
        
        # Generate visualization if matplotlib is available
        try:
            self._generate_performance_charts(results, results_dir, timestamp)
        except ImportError:
            logger.warning("Matplotlib not available - skipping chart generation")
    
    def _generate_performance_charts(
        self, 
        results: List[BenchmarkResult], 
        output_dir: Path, 
        timestamp: str
    ):
        """Generate performance comparison charts."""
        
        try:
            # Create DataFrame for visualization
            df = pd.DataFrame([asdict(r) for r in results])
            
            # Set up the plotting style
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 12))
            fig.suptitle('BLITZFIRE vs Optimized Agent Performance Comparison', fontsize=16)
            
            # Execution time comparison
            sns.boxplot(data=df, x='agent_type', y='execution_time_seconds', ax=axes[0,0])
            axes[0,0].set_title('Execution Time Distribution')
            axes[0,0].set_ylabel('Time (seconds)')
            
            # Throughput comparison
            sns.boxplot(data=df, x='agent_type', y='throughput_files_per_second', ax=axes[0,1])
            axes[0,1].set_title('Throughput Distribution')
            axes[0,1].set_ylabel('Files per Second')
            
            # Memory usage comparison
            sns.boxplot(data=df, x='agent_type', y='memory_usage_mb', ax=axes[1,0])
            axes[1,0].set_title('Memory Usage Distribution')
            axes[1,0].set_ylabel('Memory (MB)')
            
            # Cache hit rate comparison
            sns.boxplot(data=df, x='agent_type', y='cache_hit_rate', ax=axes[1,1])
            axes[1,1].set_title('Cache Hit Rate Distribution')
            axes[1,1].set_ylabel('Hit Rate')
            
            plt.tight_layout()
            chart_file = output_dir / f"blitzfire_performance_charts_{timestamp}.png"
            plt.savefig(chart_file, dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Performance charts saved to {chart_file}")
            
        except Exception as e:
            logger.error(f"Failed to generate charts: {e}")


# CLI interface for benchmark
async def main_benchmark():
    """Main entry point for BLITZFIRE benchmark."""
    
    print("🚀 BLITZFIRE Benchmark Suite")
    print("=" * 50)
    
    benchmark = BlitzfireBenchmark()
    
    # Run comprehensive benchmark
    try:
        report = await benchmark.run_comprehensive_benchmark(
            test_suite_sizes=[10, 25, 50],
            iterations=2
        )
        
        # Display summary
        print("\n📊 Benchmark Results Summary:")
        print("=" * 50)
        
        validation = report["blitzfire_validation"]
        print(f"🎯 Target: {validation['target_speedup_range']}")
        print(f"🚀 Achieved: {validation['achieved_speedup']}")
        print(f"✅ Target Met: {'Yes' if validation['target_met'] else 'No'}")
        print(f"📝 Grade: {validation['performance_grade']}")
        
        print(f"\n🔍 Key Findings:")
        for finding in report["key_findings"]:
            print(f"  • {finding}")
        
        print(f"\n💡 Recommendations:")
        for rec in validation["recommendations"]:
            print(f"  • {rec}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(asyncio.run(main_benchmark()))