# Safe Test Suite

This directory contains `safe_test.cpp` from the wire_ground project - a comprehensive C++ safety and performance test suite with 95+ tests.

## Quick Build

```bash
# Standard build
cmake -B build -DCMAKE_BUILD_TYPE=Debug
cmake --build build

# Run tests
./build/safe_test

# Or use CTest
cd build && ctest --output-on-failure
```

## Requirements

- **Compiler**: C++23 capable compiler (GCC 11+, Clang 14+, MSVC 2022+)
- **CMake**: 3.20+
- **Dependencies**: All dependencies are automatically fetched via CMake FetchContent:
  - GoogleTest 1.17.0
  - Google Benchmark 1.9.4
  - Microsoft GSL 4.2.0

## Build Options

| Option | Default | Description |
|--------|---------|-------------|
| `ENABLE_POWER_MODE` | ON | Maximum safety flags + warnings as errors |
| `ENABLE_SANITIZERS` | ON | AddressSanitizer + UBSan |
| `ENABLE_ASAN` | ON | AddressSanitizer |
| `USE_GSL` | ON | Microsoft C++ Core Guidelines Support Library |
| `VALGRIND_COMPAT` | OFF | Disable AVX2 for Valgrind compatibility |

## Build Examples

```bash
# Release build with optimizations
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build

# Build without sanitizers
cmake -B build -DENABLE_SANITIZERS=OFF
cmake --build build

# Valgrind-compatible build
cmake -B build -DVALGRIND_COMPAT=ON -DENABLE_SANITIZERS=OFF
cmake --build build
valgrind --leak-check=full ./build/safe_test
```

## Test Suites

The test file contains:
- `SafetyTestSuite` - Memory safety, buffer overflows, edge cases
- `BlitzfirePerformanceTest` - Performance benchmarks
- `POWERTest` - POWER mode validation
- `BlitzfireComprehensiveBenchmark` - Algorithmic complexity tests

## What's Included

- `tests/safe_test.cpp` - Main test file (63K+ lines, 134 tests)
- `include/training.hpp` - Core utility structures (DataProcessor, ConfigManager, Utility)
- `CMakeLists.txt` - Build configuration with dependency management

## Architecture

The test suite exercises:
- C++20/23 features (ranges, concepts, std::span)
- Memory safety (smart pointers, RAII, bounds checking)
- SIMD optimizations (SSE/AVX on x86, NEON on ARM)
- Modern C++ idioms and best practices
- Zero-warning compilation with `-Werror`

## Notes

- All dependencies are fetched automatically from GitHub
- First build will download dependencies (requires internet)
- Subsequent builds use cached dependencies
- Safe_test.cpp must remain monolithic (do not split)
