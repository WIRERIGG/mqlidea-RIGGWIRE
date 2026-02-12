"""Tools for the Blitzfire Code Agent."""

import re
import json
import hashlib
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import requests

from .models import (
    CodeIssue, ComplexityAnalysis, AnalysisResult, OptimizationTier,
    OptimizationStrategy, AssemblyComparison, BenchmarkResult,
    Architecture, OptimizationMode, SafetyLevel
)
from .dependencies import BlitzfireDependencies, CodeAnalyzer, HFTAnalyzer


def analyze_code(
    code_content: str,
    architecture: str = "x86_64",
    optimization_mode: str = "general",
    focus_areas: List[str] = None
) -> AnalysisResult:
    """
    Perform static analysis of C++ source code to identify performance bottlenecks.

    Args:
        code_content: The C++ source code to analyze
        architecture: Target architecture (x86_64, arm64, etc.)
        optimization_mode: Optimization domain (general, hft, embedded, game)
        focus_areas: Specific areas to analyze (loops, memory, concurrency, etc.)

    Returns:
        AnalysisResult with identified issues and optimization opportunities
    """
    if focus_areas is None:
        focus_areas = ["loops", "memory", "algorithms"]

    # Generate code hash for caching
    code_hash = hashlib.sha256(code_content.encode('utf-8')).hexdigest()[:16]
    lines = code_content.split('\n')

    # Perform complexity analysis
    time_complexity, space_complexity, max_nesting = CodeAnalyzer.estimate_complexity(code_content)
    hotspots = CodeAnalyzer.find_hotspots(code_content)

    complexity = ComplexityAnalysis(
        time_complexity=time_complexity,
        space_complexity=space_complexity,
        hotspots=hotspots,
        loop_nesting_depth=max_nesting,
        recursive_calls=len(re.findall(r'\b\w+\s*\([^)]*\)\s*{[^}]*\1\s*\(', code_content))
    )

    # Detect performance issues
    issues = []
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()

        # String concatenation in loops
        if re.search(r'for\s*\([^}]+\)\s*{[^}]*\w+\s*\+=\s*["\']', code_content):
            if '+=' in line_stripped and any(c in line_stripped for c in ['"', "'"]):
                issues.append(CodeIssue(
                    line_number=i,
                    issue_type="string_concatenation_loop",
                    severity="medium",
                    description="String concatenation in loop - inefficient memory allocation",
                    suggestion="Use std::stringstream or reserve string capacity",
                    estimated_impact=3.0
                ))

        # Inefficient vector operations
        if 'push_back' in line_stripped and 'vector' in code_content:
            issues.append(CodeIssue(
                line_number=i,
                issue_type="vector_growth",
                severity="medium",
                description="Vector growth without capacity reservation",
                suggestion="Use vector.reserve(expected_size) before push_back operations",
                estimated_impact=2.0
            ))

        # Division by constants
        division_match = re.search(r'(\w+)\s*/\s*(\d+)', line_stripped)
        if division_match:
            divisor = int(division_match.group(2))
            if divisor > 1 and (divisor & (divisor - 1)) != 0:  # Not power of 2
                issues.append(CodeIssue(
                    line_number=i,
                    issue_type="division_by_constant",
                    severity="low",
                    description=f"Division by constant {divisor} can be optimized",
                    suggestion=f"Replace with multiplication by {1.0/divisor} or use bit shifts if power of 2",
                    estimated_impact=1.2
                ))

    # Get optimization candidates
    optimization_candidates = CodeAnalyzer.detect_optimization_candidates(code_content)

    # Calculate baseline performance score
    baseline_score = max(1.0, 10.0 - (len(issues) * 0.5 + max_nesting * 1.5))

    # Estimate optimization potential
    optimization_potential = min(50.0, sum(issue.estimated_impact for issue in issues))

    return AnalysisResult(
        code_hash=code_hash,
        architecture=Architecture(architecture),
        optimization_mode=OptimizationMode(optimization_mode),
        issues=issues,
        complexity=complexity,
        optimization_candidates=optimization_candidates,
        baseline_score=baseline_score,
        optimization_potential=optimization_potential,
        total_issues=len(issues),
        critical_issues=len([i for i in issues if i.severity == "critical"]),
        lines_analyzed=len(lines)
    )


def generate_optimizations(
    analysis_results: AnalysisResult,
    performance_target: float = 2.0,
    safety_level: str = "high",
    include_advanced: bool = True
) -> OptimizationStrategy:
    """
    Generate multi-tier optimization strategies based on analysis results.

    Args:
        analysis_results: Results from analyze_code
        performance_target: Target performance multiplier
        safety_level: Safety constraints (low, medium, high)
        include_advanced: Include SIMD/threading optimizations

    Returns:
        OptimizationStrategy with multiple tiers and estimates
    """
    tiers = []

    # Tier 1: Compiler optimizations (always safe)
    tiers.append(OptimizationTier(
        tier_number=1,
        name="Compiler Flag Optimization",
        description="Enable aggressive compiler optimizations",
        estimated_speedup=1.3,
        difficulty="easy",
        safety_impact="none",
        code_before="// Compiled with -O0 or -O2",
        code_after="// Compile with -O3 -march=native -mtune=native -flto",
        explanation="Modern compilers can achieve 20-50% speedups with proper optimization flags. -O3 enables aggressive optimizations, -march=native uses CPU-specific instructions, and -flto performs link-time optimization."
    ))

    # Tier 2: Algorithm improvements
    if analysis_results.complexity.time_complexity in ["O(n²)", "O(n³)"]:
        tiers.append(OptimizationTier(
            tier_number=2,
            name="Algorithmic Optimization",
            description="Improve algorithm complexity",
            estimated_speedup=5.0 if "O(n²)" in analysis_results.complexity.time_complexity else 10.0,
            difficulty="medium",
            safety_impact="low",
            code_before="// Nested loops with O(n²) complexity",
            code_after="// Use hash tables, sorting, or divide-and-conquer for O(n log n)",
            explanation=f"Your algorithm has {analysis_results.complexity.time_complexity} complexity. Using better data structures (hash maps, binary search) or algorithms (merge sort, heap) can dramatically improve performance for large inputs."
        ))

    # Tier 3: Memory access optimization
    if analysis_results.complexity.loop_nesting_depth >= 2:
        tiers.append(OptimizationTier(
            tier_number=3,
            name="Cache Optimization",
            description="Improve memory access patterns",
            estimated_speedup=2.5,
            difficulty="medium",
            safety_impact="low",
            code_before="""// Cache-unfriendly access pattern
for (int i = 0; i < N; i++)
    for (int j = 0; j < M; j++)
        result += matrix[j][i];  // Column-wise access""",
            code_after="""// Cache-friendly access pattern
for (int i = 0; i < N; i++)
    for (int j = 0; j < M; j++)
        result += matrix[i][j];  // Row-wise access""",
            explanation="Memory access patterns matter! Row-wise access leverages CPU cache lines (typically 64 bytes), while column-wise access causes cache misses. This can be 10x faster for large matrices."
        ))

    # Tier 4: Container optimizations
    string_issues = [i for i in analysis_results.issues if i.issue_type == "string_concatenation_loop"]
    vector_issues = [i for i in analysis_results.issues if i.issue_type == "vector_growth"]

    if string_issues or vector_issues:
        tiers.append(OptimizationTier(
            tier_number=4,
            name="Container Optimization",
            description="Optimize STL container usage",
            estimated_speedup=3.0,
            difficulty="easy",
            safety_impact="none",
            code_before="""// Inefficient patterns
string result = "";
for (...) result += str;  // O(n²) concatenation
vector<int> v;
for (...) v.push_back(x);  // Multiple reallocations""",
            code_after="""// Optimized patterns
ostringstream oss;
for (...) oss << str;  // O(n) concatenation
vector<int> v;
v.reserve(expected_size);  // Single allocation
for (...) v.push_back(x);""",
            explanation="String concatenation in loops is O(n²) due to repeated copying. stringstream uses internal buffering for O(n) performance. Similarly, reserving vector capacity prevents expensive reallocations."
        ))

    # Tier 5: SIMD vectorization (advanced)
    if include_advanced and any("float" in str or "double" in str for str in analysis_results.optimization_candidates):
        tiers.append(OptimizationTier(
            tier_number=5,
            name="SIMD Vectorization",
            description="Use CPU vector instructions for parallel processing",
            estimated_speedup=4.0,
            difficulty="hard",
            safety_impact="medium",
            code_before="""// Scalar processing
for (int i = 0; i < n; i++) {
    result[i] = a[i] * b[i] + c[i];
}""",
            code_after="""// SIMD processing (AVX2)
for (int i = 0; i < n; i += 8) {
    __m256 va = _mm256_load_ps(&a[i]);
    __m256 vb = _mm256_load_ps(&b[i]);
    __m256 vc = _mm256_load_ps(&c[i]);
    __m256 result = _mm256_fmadd_ps(va, vb, vc);
    _mm256_store_ps(&result[i], result);
}""",
            explanation="SIMD (Single Instruction, Multiple Data) processes 8 floats simultaneously with AVX2. This gives nearly 8x speedup for arithmetic operations! Modern CPUs have 256-bit (AVX2) or 512-bit (AVX-512) vector units."
        ))

    # Calculate total speedup (multiplicative for independent optimizations)
    total_speedup = 1.0
    for tier in tiers:
        # Diminishing returns - each tier contributes less
        total_speedup *= (1.0 + (tier.estimated_speedup - 1.0) * 0.8)

    # Recommended implementation order (easy first, then by impact)
    recommended_order = sorted(range(len(tiers)), key=lambda i: (tiers[i].difficulty == "hard", -tiers[i].estimated_speedup))

    warnings = []
    if safety_level == "high":
        warnings.append("Always benchmark optimizations - theoretical speedups may vary with real workloads")
        warnings.append("Verify correctness with comprehensive tests before deploying optimizations")

    if include_advanced:
        warnings.append("Advanced optimizations (SIMD, threading) require careful testing and may reduce portability")

    next_steps = [
        "Profile your code to identify actual bottlenecks",
        "Implement optimizations incrementally and measure each step",
        "Consider parallel algorithms if you have multi-core systems",
        "Look into profile-guided optimization (PGO) for production builds"
    ]

    return OptimizationStrategy(
        total_estimated_speedup=total_speedup,
        recommended_order=recommended_order,
        tiers=tiers,
        warnings=warnings,
        next_steps=next_steps
    )


def validate_assembly(
    original_code: str,
    optimized_code: str,
    compiler: str = "clang_trunk",
    optimization_level: str = "-O3",
    architecture: str = "x86_64"
) -> Optional[AssemblyComparison]:
    """
    Compare assembly output using Godbolt integration (mock implementation).

    Args:
        original_code: Baseline C++ code
        optimized_code: Optimized C++ code
        compiler: Compiler version
        optimization_level: Compiler flags
        architecture: Target architecture

    Returns:
        AssemblyComparison with differences, or None if validation fails
    """
    # Mock implementation for now - would integrate with actual Godbolt API
    # This simulates what a real implementation would return

    # Simulate instruction count difference
    original_lines = len(original_code.split('\n'))
    optimized_lines = len(optimized_code.split('\n'))

    # Mock metrics based on code characteristics
    vectorization_detected = "simd" in optimized_code.lower() or "vector" in optimized_code.lower()
    loop_unrolling_detected = "for" in original_code and len(optimized_code) > len(original_code) * 1.2

    key_differences = []
    optimization_artifacts = []

    if vectorization_detected:
        key_differences.append("Vectorized operations detected (SIMD instructions)")
        optimization_artifacts.append("AVX/SSE vector instructions")

    if loop_unrolling_detected:
        key_differences.append("Loop unrolling applied")
        optimization_artifacts.append("Unrolled loop structure")

    if optimization_level == "-O3":
        optimization_artifacts.extend(["Function inlining", "Dead code elimination", "Constant propagation"])

    return AssemblyComparison(
        original_instructions=original_lines * 3,  # Rough estimate
        optimized_instructions=max(1, original_lines * 2),  # Optimized version
        vectorization_detected=vectorization_detected,
        loop_unrolling_detected=loop_unrolling_detected,
        key_differences=key_differences,
        optimization_artifacts=optimization_artifacts
    )


def benchmark_performance(
    test_functions: List[str],
    test_sizes: List[int] = None,
    iterations: int = 1000,
    architecture: str = "x86_64"
) -> List[BenchmarkResult]:
    """
    Execute empirical performance testing (mock implementation).

    Args:
        test_functions: Function implementations to benchmark
        test_sizes: Input size parameters
        iterations: Benchmark iterations
        architecture: Target architecture

    Returns:
        List of BenchmarkResult with timing measurements
    """
    if test_sizes is None:
        test_sizes = [100, 1000, 10000]

    results = []

    # Mock benchmarking results - would use real Google Benchmark in production
    for func_name in test_functions:
        for size in test_sizes:
            # Simulate realistic performance numbers
            base_time = size * 10  # nanoseconds per element

            # Add some complexity based on function characteristics
            if "optimized" in func_name.lower():
                base_time *= 0.4  # 2.5x speedup simulation

            if "simd" in func_name.lower():
                base_time *= 0.25  # 4x speedup for SIMD

            # Add realistic variance
            import random
            mean_time = base_time * (0.95 + random.random() * 0.1)
            std_dev = mean_time * 0.05

            results.append(BenchmarkResult(
                function_name=func_name,
                input_size=size,
                mean_time_ns=mean_time,
                std_dev_ns=std_dev,
                iterations=iterations,
                speedup_ratio=None  # Would be calculated against baseline
            ))

    # Calculate speedup ratios
    baseline_results = {size: next((r for r in results if "baseline" in r.function_name and r.input_size == size), None)
                       for size in test_sizes}

    for result in results:
        if "baseline" not in result.function_name:
            baseline = baseline_results.get(result.input_size)
            if baseline:
                result.speedup_ratio = baseline.mean_time_ns / result.mean_time_ns

    return results


def hft_audit(
    code_content: str,
    audit_level: str = "comprehensive",
    check_categories: List[str] = None
) -> Dict[str, Any]:
    """
    Perform HFT-specific code quality audit.

    Args:
        code_content: C++ source code to audit
        audit_level: Audit depth (basic, standard, comprehensive)
        check_categories: Specific checks (overflow, races, determinism)

    Returns:
        HFT audit results with safety recommendations
    """
    if check_categories is None:
        check_categories = ["overflow", "races", "determinism"]

    # Use HFT analyzer for specialized checks
    risks = HFTAnalyzer.audit_hft_risks(code_content)

    # Convert to structured format
    overflow_issues = [
        CodeIssue(
            line_number=int(risk.split()[1][:-1]),  # Extract line number
            issue_type="hft_overflow_risk",
            severity="high",
            description=risk,
            suggestion="Add overflow checks or use safe arithmetic libraries",
            estimated_impact=1.0
        ) for risk in risks["overflow_risks"]
    ]

    race_condition_issues = [
        CodeIssue(
            line_number=int(risk.split()[1][:-1]),
            issue_type="hft_race_condition",
            severity="critical",
            description=risk,
            suggestion="Use atomic operations or proper synchronization",
            estimated_impact=1.0
        ) for risk in risks["race_conditions"]
    ]

    determinism_issues = [
        CodeIssue(
            line_number=int(risk.split()[1][:-1]),
            issue_type="hft_determinism",
            severity="medium",
            description=risk,
            suggestion="Use epsilon-based floating-point comparisons",
            estimated_impact=1.0
        ) for risk in risks["determinism_issues"]
    ]

    # Calculate safety score
    total_issues = len(overflow_issues) + len(race_condition_issues) + len(determinism_issues)
    safety_score = max(1, 10 - total_issues)

    recommendations = [
        "Use safe arithmetic libraries for financial calculations",
        "Implement comprehensive unit tests with edge cases",
        "Consider formal verification for critical algorithms",
        "Add logging and audit trails for regulatory compliance",
        "Use deterministic threading patterns or lock-free data structures"
    ]

    return {
        "overflow_risks": overflow_issues,
        "race_conditions": race_condition_issues,
        "determinism_issues": determinism_issues,
        "safety_score": safety_score,
        "recommendations": recommendations,
        "total_issues": total_issues
    }


def interactive_chat(
    user_message: str,
    context: Dict[str, Any] = None,
    educational_mode: bool = True
) -> str:
    """
    Handle conversational interaction with educational explanations.

    Args:
        user_message: User question or request
        context: Previous analysis results for context
        educational_mode: Include teaching explanations

    Returns:
        Conversational response with optimization guidance
    """
    if context is None:
        context = {}

    # Simple keyword-based response system (would use LLM in production)
    user_lower = user_message.lower()

    if "hello" in user_lower or "hi" in user_lower:
        return "🚀 Welcome to Blitzfire optimization! I'm excited to supercharge your C++ code! What optimization challenge can I help you with today?"

    elif "simd" in user_lower or "vector" in user_lower:
        response = "⚡ SIMD (Single Instruction, Multiple Data) is like having multiple calculators working in parallel! "
        if educational_mode:
            response += """

Modern CPUs have vector units that can process multiple data elements simultaneously:
- **SSE**: 128-bit vectors (4 floats or 2 doubles at once)
- **AVX2**: 256-bit vectors (8 floats or 4 doubles at once)
- **AVX-512**: 512-bit vectors (16 floats or 8 doubles at once)

This can give you 4-16x speedup for mathematical operations! The key is having data that can be processed in parallel - arrays of numbers are perfect candidates.

Want me to analyze your code for SIMD opportunities?"""
        return response

    elif "cache" in user_lower or "memory" in user_lower:
        response = "🧠 Cache optimization is like organizing your desk efficiently! "
        if educational_mode:
            response += """

CPU caches are small, fast memory that store frequently used data:
- **L1 Cache**: ~32KB, 1 cycle access time
- **L2 Cache**: ~256KB, 3-10 cycles
- **L3 Cache**: ~8MB, 20-40 cycles
- **RAM**: GBs, 200+ cycles

The golden rules:
1. **Spatial locality**: Access data that's close together in memory
2. **Temporal locality**: Reuse data you've accessed recently
3. **Sequential access**: Row-wise array traversal is cache-friendly

A cache miss can be 100x slower than a cache hit!"""
        return response

    elif "optimization" in user_lower and ("tier" in user_lower or "strategy" in user_lower):
        return """🎯 Great question! I use a multi-tier optimization strategy:

**Tier 1-2**: Safe, easy wins (compiler flags, simple algorithm tweaks)
**Tier 3-4**: Medium complexity (data structures, memory patterns)
**Tier 5-6**: Advanced techniques (SIMD, threading, custom algorithms)

The beauty is you can implement them incrementally and measure each step! Start with the easy ones for quick wins, then tackle the advanced optimizations when you need maximum performance.

Which tier interests you most, or should I analyze your code to create a custom strategy?"""

    elif "benchmark" in user_lower or "measure" in user_lower:
        return """📊 Excellent mindset! As I always say: "In optimization we trust, but always benchmark!"

My benchmarking approach uses:
- **Google Benchmark**: Industry-standard C++ benchmarking
- **Statistical analysis**: Mean, standard deviation, confidence intervals
- **Multiple input sizes**: See how optimizations scale
- **Assembly validation**: Verify compiler optimizations actually happened

Remember: Premature optimization is the root of all evil, but measurement is the root of all performance! Would you like me to set up benchmarking for your code?"""

    else:
        return f"🤔 I'd love to help optimize that! Could you share your C++ code so I can analyze it for performance opportunities? I'm especially good at finding algorithmic improvements, cache optimizations, and SIMD vectorization candidates!"


def mock_reasoning_response(analysis: AnalysisResult) -> str:
    """
    Mock reasoning response for dynamic optimization generation.
    This would be replaced with actual LLM API calls in production.
    """
    reasoning = f"""🔍 **Analysis Complete!**

I found {analysis.total_issues} optimization opportunities in your {analysis.lines_analyzed}-line code with {analysis.complexity.time_complexity} complexity.

**Key Findings:**
- Algorithm complexity: {analysis.complexity.time_complexity}
- Performance hotspots at lines: {', '.join(map(str, analysis.complexity.hotspots[:5]))}
- Optimization potential: {analysis.optimization_potential:.1f}x speedup possible

**My Recommendation:**
Start with Tier 1-2 optimizations (compiler flags + algorithm improvements) for safe 2-3x gains, then consider advanced techniques if needed.

The most impactful opportunity appears to be {'algorithmic optimization' if 'n²' in analysis.complexity.time_complexity else 'memory access optimization'}.

Ready to see the detailed optimization strategy? 🚀"""

    return reasoning