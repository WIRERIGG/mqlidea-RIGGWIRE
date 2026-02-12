# 🚀 Blitzfire Code Agent

**AI-Powered C++ Optimization Agent - Faster than a cheetah on espresso!**

An intelligent C++ code optimization agent that provides deep performance analysis, multi-tier optimization strategies, assembly-level validation, and empirical benchmarking with an engaging personality. Specializes in high-frequency trading (HFT) code quality while remaining versatile for general-purpose optimization.

## ⚡ Features

### 🧠 **AI-Enhanced Analysis**
- **Static Code Analysis**: Regex-based pattern detection for performance bottlenecks
- **Complexity Estimation**: Big-O analysis and computational hotspot identification
- **Multi-Tier Optimization**: 4-6 tier strategies from compiler flags to SIMD/threading
- **Performance Estimates**: Quantified speedup predictions (e.g., 2.5x, 10x improvements)

### 🔧 **Comprehensive Validation**
- **Godbolt Integration**: Assembly comparison between original and optimized code
- **Docker Benchmarking**: Empirical performance testing with Google Benchmark
- **Safety Analysis**: Overflow detection, race condition identification
- **HFT Specialization**: Financial trading code quality and compliance checks

### 📚 **Educational Personality**
- **Enthusiastic Interface**: Speed metaphors and engaging explanations
- **Interactive Chat**: Conversational optimization guidance and learning
- **Structured Responses**: Analysis → Strategy → Implementation → Validation
- **Pro Tips**: Educational insights about compiler behavior and optimization theory

## 🚀 Quick Start

### Installation

1. **Navigate to the agent directory**:
   ```bash
   cd /IdeaProjects/wire_ground/.claude/agents/blitzfire_code_agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your LLM provider API key
   ```

4. **Start interactive session**:
   ```bash
   python -m cli
   ```

### Environment Configuration

Required variables in `.env`:

```env
# LLM Provider
LLM_PROVIDER=openai
LLM_API_KEY=your_api_key_here
LLM_MODEL=gpt-4o-mini

# Project Settings
PROJECT_ROOT=/IdeaProjects/wire_ground
BLITZFIRE_MODE=general
```

## 🎯 Usage Examples

### Command Line Interface

```bash
# Interactive mode with colorful output
python -m cli

# Analyze a specific file
python -m cli analyze src/main.cpp

# HFT mode analysis
python -m cli --mode hft analyze trading.cpp

# No colors (for scripting)
python -m cli --no-colors --quiet analyze code.cpp
```

### Programmatic Usage

```python
import asyncio
from blitzfire_code_agent import BlitzfireCodeAgent, quick_analyze

# Quick analysis
async def analyze_code():
    code = """
    for (int i = 0; i < n; i++) {
        for (int j = 0; j < m; j++) {
            result += matrix[j][i];  // Cache-unfriendly!
        }
    }
    """

    response = await quick_analyze(code)
    print(f"Blitzfire Score: {response.blitzfire_score}/10")
    print(f"Estimated Speedup: {response.strategy.total_estimated_speedup}x")

    for tier in response.strategy.tiers:
        print(f"Tier {tier.tier_number}: {tier.name} ({tier.estimated_speedup}x)")

# Full agent usage
async def full_analysis():
    agent = BlitzfireCodeAgent()

    response = await agent.analyze_and_optimize(
        code_content=code,
        architecture="x86_64",
        optimization_mode="general",
        include_benchmarks=True,
        include_assembly=True
    )

    # Assembly validation results
    if response.assembly_comparison:
        print(f"Vectorization detected: {response.assembly_comparison.vectorization_detected}")

    # Benchmark results
    for result in response.benchmark_results:
        if result.speedup_ratio:
            print(f"{result.function_name}: {result.speedup_ratio:.1f}x speedup")

asyncio.run(analyze_code())
```

### Interactive Chat

```python
async def chat_example():
    agent = BlitzfireCodeAgent()

    # Educational conversations
    response = await agent.chat("How does SIMD vectorization work?")
    print(response)  # Enthusiastic explanation with examples

    response = await agent.chat("What makes code cache-friendly?")
    print(response)  # Cache behavior explanation with analogies

asyncio.run(chat_example())
```

## 🏦 HFT Specialization

When analyzing high-frequency trading code, Blitzfire provides specialized analysis:

```python
async def hft_analysis():
    agent = BlitzfireCodeAgent()

    hft_code = """
    double current_price = 100.50;

    void update_price(double new_price) {
        current_price = new_price;  // Race condition!
    }

    if (price == target_price) {  // Dangerous equality
        execute_order();
    }
    """

    results = await agent.analyze_for_hft(hft_code)

    # Get HFT-specific recommendations
    print("Safety Score:", results['hft_audit']['safety_score'])
    for issue in results['hft_audit']['race_conditions']:
        print(f"Race condition: {issue.description}")

asyncio.run(hft_analysis())
```

## 🎨 Optimization Strategies

Blitzfire generates multi-tier optimization strategies:

### Example Strategy Output

```
⚡ OPTIMIZATION STRATEGY
==========================================
Total Estimated Speedup: 8.5x

🏆 TIER 1: COMPILER FLAG OPTIMIZATION (1.3x)
  • Enable -O3 -march=native -mtune=native -flto
  • Safe and easy - no code changes required

🏆 TIER 2: ALGORITHMIC OPTIMIZATION (5.0x)
  • Replace O(n²) nested loops with O(n log n) algorithm
  • Use hash tables instead of linear search

🏆 TIER 3: CACHE OPTIMIZATION (2.5x)
  • Change column-wise to row-wise array access
  • Leverage CPU cache lines for better memory patterns

🏆 TIER 4: SIMD VECTORIZATION (4.0x)
  • Use AVX2 intrinsics for parallel arithmetic
  • Process 8 floats simultaneously instead of 1

🏆 TIER 5: THREADING (2.0x)
  • Parallel execution with OpenMP
  • Scale across multiple CPU cores
```

## 📊 Features Matrix

| Feature | Status | Description |
|---------|--------|-------------|
| ✅ Static Analysis | Complete | Pattern detection and complexity analysis |
| ✅ Optimization Tiers | Complete | Multi-tier strategies with estimates |
| ✅ Godbolt Integration | Complete | Assembly validation and comparison |
| ✅ Docker Benchmarking | Complete | Empirical performance testing |
| ✅ Interactive CLI | Complete | Colorful terminal interface |
| ✅ HFT Specialization | Complete | Financial trading code analysis |
| ✅ Educational Chat | Complete | Conversational optimization guidance |
| 🔄 xAI Integration | Planned | Dynamic reasoning with Grok API |
| 🔄 AST Parsing | Planned | Advanced syntax tree analysis |
| 🔄 Profile-Guided Optimization | Planned | Runtime profiling integration |

## 🏗️ Architecture

```
blitzfire_code_agent/
├── agent.py              # Main Blitzfire agent implementation
├── models.py             # Pydantic data models
├── tools.py              # Core analysis and optimization tools
├── cli.py                # Interactive command-line interface
├── settings.py           # Configuration management
├── providers.py          # LLM provider configuration
├── dependencies.py       # Context and external services
├── prompts.py            # System prompts and personality
├── godbolt_integration.py # Compiler Explorer integration
├── benchmark_harness.py  # Docker benchmarking system
├── hft_specialization.py # HFT-specific analysis
└── planning/             # Design documentation
    ├── INITIAL.md        # Requirements specification
    ├── prompts.md        # Prompt design
    ├── tools.md          # Tool specifications
    └── dependencies.md   # Dependency configuration
```

## 🔧 Advanced Configuration

### Optimization Modes

- **General**: Broad optimization patterns for any C++ codebase
- **HFT**: Financial system focus with reliability and compliance
- **Embedded**: Memory and power efficiency optimizations
- **Game**: Real-time performance and frame rate optimization

### External Services

- **Godbolt**: Assembly analysis and compiler optimization validation
- **Docker**: Isolated benchmarking with Google Benchmark
- **LLM Providers**: OpenAI, Anthropic Claude, Google Gemini, local Ollama

### Caching Strategy

- **Analysis Cache**: 30 minutes (avoid reprocessing identical code)
- **Benchmark Cache**: 2 hours (expensive empirical measurements)
- **Assembly Cache**: 1 hour (based on code + compiler settings)

## 📈 Performance Examples

Real-world optimization examples:

### Matrix Multiplication
```cpp
// Before: O(n³) with cache misses
for (int i = 0; i < n; i++)
    for (int j = 0; j < m; j++)
        for (int k = 0; k < p; k++)
            C[i][j] += A[i][k] * B[k][j];

// After: Cache-blocked with SIMD (20x faster)
for (int ii = 0; ii < n; ii += BLOCK)
    for (int jj = 0; jj < m; jj += BLOCK)
        for (int kk = 0; kk < p; kk += BLOCK)
            // Vectorized inner loops with AVX2
```

### String Processing
```cpp
// Before: O(n²) string concatenation
string result = "";
for (auto& str : strings)
    result += str;  // Repeated copying

// After: O(n) with pre-allocated buffer (10x faster)
ostringstream buffer;
for (auto& str : strings)
    buffer << str;  // Single allocation
```

## 🐛 Troubleshooting

### Common Issues

**API Key not configured:**
```bash
ValueError: llm_api_key field required
```
Solution: Set `LLM_API_KEY` in your `.env` file

**Docker not available:**
```bash
Docker benchmarking not available - using fallback estimates
```
Solution: Install Docker or set `DOCKER_ENABLED=false` to skip benchmarks

**Godbolt connection failed:**
```bash
Godbolt compilation failed: Connection timeout
```
Solution: Check internet connection or use cached results

### Getting Help

1. **Interactive help**: Type `help` in CLI mode
2. **Debug mode**: Set `DEBUG_MODE=true` in `.env`
3. **Verbose logging**: Set `LOG_LEVEL=DEBUG`

## 🤝 Integration

### Wire Ground Project

Blitzfire integrates seamlessly with the wire_ground project's build system:

- **Respects build flags**: Uses project's Clang configuration
- **Zero warnings**: Follows project's strict warning policy
- **Test integration**: Works with GoogleTest and benchmark infrastructure
- **BLITZFIRE mode**: Extends project's performance optimization philosophy

### CI/CD Integration

```bash
# Add to your CI pipeline
python -m blitzfire_code_agent.cli analyze src/**/*.cpp --mode general --no-colors
```

## 📜 License

Built as part of the wire_ground project's AI Agent Factory framework for enhancing development workflows with intelligent, educational AI assistance.

## 🚀 Next Steps

1. **Try the interactive mode**: `python -m cli`
2. **Analyze your C++ code**: Start with small examples
3. **Experiment with modes**: Try HFT mode for financial code
4. **Learn optimization theory**: Ask educational questions
5. **Contribute**: Help improve pattern detection and optimization strategies

---

*Blitzfire: Where AI meets C++ optimization - faster than a cheetah on espresso! ⚡*