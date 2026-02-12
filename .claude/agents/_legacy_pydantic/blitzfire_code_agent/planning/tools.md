# Blitzfire Code Agent - Tool Specifications

## Core Analysis Tools

### 1. analyze_code
**Purpose**: Perform static analysis of C++ source code to identify performance bottlenecks and optimization opportunities

**Parameters**:
- `code_content: str` - The C++ source code to analyze
- `architecture: str = "x86_64"` - Target architecture (x86_64, arm64, etc.)
- `domain: str = "general"` - Optimization domain (general, hft, embedded, game)
- `focus_areas: List[str] = []` - Specific areas to analyze (loops, memory, concurrency, etc.)

**Functionality**:
- Regex-based pattern detection for common performance bottlenecks
- Complexity analysis (Big-O estimation for loops and algorithms)
- Hotspot identification (nested loops, memory allocations, string operations)
- Safety checks (potential undefined behavior, race conditions in HFT mode)
- Architecture-specific optimization opportunities (SIMD candidates, cache patterns)

**Returns**: Analysis results with identified issues, complexity estimates, and optimization candidates

### 2. generate_optimizations
**Purpose**: Create multi-tier optimization strategies with performance estimates and implementation guidance

**Parameters**:
- `analysis_results: dict` - Results from analyze_code tool
- `performance_target: float = 2.0` - Target performance multiplier
- `safety_level: str = "high"` - Safety constraints (low, medium, high)
- `include_advanced: bool = True` - Include SIMD/threading optimizations

**Functionality**:
- Generate 4-6 optimization tiers from simple to advanced
- Provide performance estimates for each tier (e.g., 1.2x, 3x, 10x speedup)
- Create code snippets showing before/after implementations
- Include rationale and educational explanations for each optimization
- Consider safety tradeoffs and implementation complexity

**Returns**: Structured optimization strategy with tiers, estimates, and code examples

### 3. validate_assembly
**Purpose**: Compare assembly output between baseline and optimized code using Godbolt integration

**Parameters**:
- `original_code: str` - Baseline C++ code
- `optimized_code: str` - Optimized C++ code
- `compiler: str = "clang_trunk"` - Compiler version to use
- `optimization_level: str = "-O3"` - Compiler optimization flags
- `architecture: str = "x86_64"` - Target architecture

**Functionality**:
- Submit code to Godbolt Compiler Explorer API
- Generate assembly for both versions with identical compiler settings
- Perform assembly diff analysis to highlight key differences
- Identify optimization artifacts (vectorization, loop unrolling, inlining)
- Extract performance-relevant metrics (instruction count, register usage)

**Returns**: Assembly comparison with highlighted differences and optimization validation

### 4. benchmark_performance
**Purpose**: Execute empirical performance testing using Docker + Google Benchmark

**Parameters**:
- `test_functions: List[str]` - Function implementations to benchmark
- `test_sizes: List[int] = [100, 1000, 10000]` - Input size parameters
- `iterations: int = 1000` - Benchmark iterations
- `architecture: str = "x86_64"` - Target architecture for Docker container

**Functionality**:
- Generate Google Benchmark test harness code
- Create Dockerized environment with appropriate compiler and flags
- Execute benchmarks and capture timing results
- Parse benchmark output for mean, standard deviation, and throughput
- Compare multiple implementations and calculate speedup ratios

**Returns**: Empirical performance measurements with statistical analysis

### 5. hft_audit
**Purpose**: Specialized analysis for high-frequency trading code quality and safety

**Parameters**:
- `code_content: str` - C++ source code to audit
- `audit_level: str = "comprehensive"` - Audit depth (basic, standard, comprehensive)
- `check_categories: List[str] = ["overflow", "races", "determinism"]` - Specific checks to run

**Functionality**:
- Integer overflow detection for financial calculations
- Race condition analysis in concurrent code paths
- Lock-free algorithm correctness validation
- Memory ordering and atomic operation auditing
- Determinism checks for reproducible behavior
- Regulatory compliance patterns (audit trails, error handling)

**Returns**: HFT-specific code quality assessment with safety recommendations

### 6. interactive_chat
**Purpose**: Conversational interface for optimization guidance and educational interaction

**Parameters**:
- `user_message: str` - User question or request
- `context: dict = {}` - Previous analysis results for context
- `educational_mode: bool = True` - Include teaching explanations

**Functionality**:
- Answer optimization questions with engaging personality
- Provide educational explanations using analogies and examples
- Reference previous analysis results for contextual guidance
- Suggest follow-up experiments and learning opportunities
- Maintain conversation state for multi-turn interactions

**Returns**: Conversational response with optimization guidance and educational content

## Tool Integration Patterns

### Sequential Analysis Flow
```
analyze_code → generate_optimizations → validate_assembly → benchmark_performance
```

### Educational Flow
```
analyze_code → interactive_chat → generate_optimizations → interactive_chat
```

### HFT Specialized Flow
```
analyze_code → hft_audit → generate_optimizations → validate_assembly
```

## Error Handling Strategy
- **Godbolt API failures**: Fallback to local compiler analysis
- **Docker unavailable**: Skip benchmarking with notification
- **Network issues**: Use cached results when possible
- **Compilation errors**: Provide diagnostic information and correction suggestions
- **Resource limits**: Scale down benchmark complexity automatically

## Performance Targets
- **Analysis**: Complete static analysis within 5-10 seconds
- **Assembly validation**: Godbolt response within 15 seconds
- **Benchmarking**: Complete test suite within 30-60 seconds
- **Conversational response**: Generate replies within 2-3 seconds