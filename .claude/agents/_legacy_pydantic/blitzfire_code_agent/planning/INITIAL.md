# Blitzfire Code Agent - AI-Powered C++ Optimization Agent

## What This Agent Does
An intelligent C++ code optimization agent that provides deep performance analysis, multi-tier optimization strategies, assembly-level validation, and empirical benchmarking with an engaging personality. Specializes in high-frequency trading (HFT) code quality while remaining versatile for general-purpose optimization.

## Core Features (MVP)
1. **Static Code Analysis**: Analyze C++ code for performance bottlenecks, complexity patterns, and optimization opportunities using regex-based pattern detection and complexity estimation
2. **Multi-Tier Optimization Strategy**: Generate comprehensive optimization recommendations from compiler hints to SIMD/multithreading with quantified performance estimates
3. **Assembly Validation**: Integrate with Godbolt Compiler Explorer to validate optimizations through assembly diff analysis
4. **Empirical Benchmarking**: Use Docker + Google Benchmark to measure actual performance improvements and validate predictions
5. **HFT Specialization**: Optional domain-specific analysis for financial systems (lock-free designs, overflow checks, race condition detection)
6. **Interactive Personality**: Enthusiastic, educational interface with speed metaphors and engaging explanations

## Technical Setup

### Model
- **Provider**: openai
- **Model**: gpt-4o-mini
- **Why**: Balance of performance analysis capability and cost-effectiveness for code optimization tasks

### Required Tools
1. **analyze_code**: Static analysis of C++ source code for hotspots, complexity, and optimization opportunities
2. **generate_optimizations**: Create multi-tier optimization strategies with performance estimates and code snippets
3. **validate_assembly**: Compare baseline vs optimized code assembly using Godbolt API integration
4. **benchmark_performance**: Execute empirical performance testing using Docker + Google Benchmark
5. **hft_audit**: Specialized analysis for high-frequency trading code quality and safety
6. **interactive_chat**: Conversational interface for optimization guidance and education

### External Services
- **Godbolt Compiler Explorer API**: Assembly generation and comparison for optimization validation
- **Docker**: Containerized benchmarking environment with Google Benchmark
- **xAI/Grok API** (future): Dynamic reasoning and optimization strategy generation

## Environment Variables
```bash
LLM_API_KEY=your-openai-api-key
GODBOLT_BASE_URL=https://godbolt.org
DOCKER_ENABLED=true
PROJECT_ROOT=/IdeaProjects/wire_ground
BLITZFIRE_MODE=general  # general, hft, embedded, game
```

## Success Criteria
- [ ] Analyzes C++ code and identifies performance bottlenecks with >90% accuracy
- [ ] Generates multi-tier optimization strategies with quantified performance estimates
- [ ] Successfully integrates with Godbolt API for assembly validation
- [ ] Executes benchmarking and reports empirical speedup measurements
- [ ] Provides engaging, educational explanations with personality
- [ ] Handles HFT-specific analysis when domain flag is set
- [ ] Returns structured analysis with code snippets, estimates, and validation results

## Assumptions Made
- **Target Architecture**: Primarily x86_64 with optional ARM support for broader compatibility
- **C++ Standards**: Focus on modern C++17/20/23 features and optimization patterns
- **Docker Availability**: Docker is available for benchmarking; graceful fallback if not present
- **Build System**: Works with CMake-based projects like wire_ground with clang compilation
- **Network Access**: Can reach Godbolt API; local fallback for assembly analysis if needed
- **Performance Focus**: Emphasizes micro-optimizations, algorithmic improvements, and compiler optimization guidance
- **Educational Goal**: Provides learning-oriented explanations rather than just automated fixes

## Integration Points
- **Existing clang-tidy integration**: Leverages existing static analysis infrastructure
- **wire_ground build system**: Integrates with project's comprehensive build and testing framework
- **BLITZFIRE system**: Extends project's performance optimization philosophy
- **Agent factory framework**: Follows Pydantic AI patterns for consistency and maintainability

---
Generated: 2025-01-15
Note: This is an MVP focused on core optimization analysis. Advanced features like machine learning-based pattern recognition and custom optimization rule engines can be added after the basic agent works.