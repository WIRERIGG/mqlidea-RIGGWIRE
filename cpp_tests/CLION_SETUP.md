# CLion Setup Guide for safe_test

## Project Configuration

CLion is now configured to build and run the `safe_test` project.

### CMake Profiles

Two CMake profiles have been configured:

1. **Debug** (Default)
   - Build directory: `build/`
   - Options: `-DENABLE_POWER_MODE=ON -DENABLE_SANITIZERS=OFF`
   - Compiler flags: `-Wall -Wextra -Wpedantic -Werror` (strict mode)
   - Optimization: `-O0 -g` (debug symbols, no optimization)

2. **Release**
   - Build directory: `build-release/`
   - Options: `-DENABLE_POWER_MODE=ON -DENABLE_SANITIZERS=OFF`
   - Optimization: `-O3 -march=native -mtune=native -funroll-loops`

### Run Configurations

Three run configurations are available in CLion:

1. **safe_test** - Run all tests without filters
2. **safe_test (BufferOverflow)** - Run only BufferOverflow test (example filter)
3. **Run All Tests** - Run all tests with timing and colored output

### How to Use in CLion

#### Opening the Project
1. Open CLion
2. Go to **File → Open**
3. Navigate to: `/home/RIGG_dev/CLionProjects/RIGGWIRE-EA/cpp_tests`
4. Click **OK**
5. CLion will automatically detect CMakeLists.txt and configure the project

#### Building
- **Build Project**: `Ctrl+F9` or **Build → Build Project**
- **Rebuild**: **Build → Rebuild Project**
- **Clean**: **Build → Clean**

#### Running Tests
- **Run**: `Shift+F10` or click the green ▶ button
- **Debug**: `Shift+F9` or click the debug 🐞 button
- **Select configuration**: Use dropdown at top-right

#### Switching CMake Profiles
1. Go to **File → Settings → Build, Execution, Deployment → CMake**
2. Select desired profile (Debug or Release)
3. Click **OK**
4. CLion will reconfigure automatically

#### Running Specific Tests
To run a specific test or test suite:
1. Click dropdown at top-right
2. Select **safe_test (BufferOverflow)** for example
3. Or create a new configuration:
   - **Run → Edit Configurations**
   - Click **+** → **CMake Application**
   - Set **Target**: `safe_test`
   - Set **Program arguments**: `--gtest_filter=SafetyTestSuite.YourTestName`
   - Click **OK**

### GoogleTest Integration

CLion has built-in GoogleTest support:
- Tests appear in the **Test Explorer** window
- Right-click any test to run individually
- View results with pass/fail indicators
- Navigate to test source by clicking test names

### Useful GoogleTest Flags

Add these to **Program arguments** in run configurations:

```
--gtest_filter=SafetyTestSuite.*          # Run all tests in SafetyTestSuite
--gtest_filter=*BufferOverflow*           # Run tests matching pattern
--gtest_print_time=1                      # Show test execution time
--gtest_color=yes                         # Colored output
--gtest_repeat=10                         # Run tests 10 times
--gtest_shuffle                           # Randomize test order
--gtest_list_tests                        # List all available tests
```

### Troubleshooting

#### CMake Errors
If CLion shows CMake errors:
1. Go to **File → Invalidate Caches → Invalidate and Restart**
2. Or delete `build/` directory and reload CMake

#### Missing Dependencies
Dependencies are fetched automatically via CMake FetchContent:
- GoogleTest v1.17.0
- Google Benchmark v1.9.4
- Microsoft GSL v4.2.0

#### Sanitizer Issues
AddressSanitizer is currently disabled due to missing runtime libraries.
To enable (if available):
1. Edit `CMakeLists.txt`
2. Change `-DENABLE_SANITIZERS=OFF` to `ON`
3. Reload CMake

### Project Structure

```
cpp_tests/
├── CMakeLists.txt          # Build configuration
├── README.md               # Project documentation
├── CLION_SETUP.md         # This file
├── include/                # Header files
├── tests/
│   └── safe_test.cpp      # Test suite (198KB, comprehensive)
├── build/                  # Debug build directory
│   └── safe_test          # Test executable (6.4MB)
└── .idea/                  # CLion configuration
    ├── workspace.xml       # CMake profiles
    ├── misc.xml           # Project settings
    └── runConfigurations/ # Run/debug configs
```

### Quick Commands (Terminal)

If you prefer terminal commands:

```bash
# Configure
cmake -DCMAKE_BUILD_TYPE=Debug -DENABLE_POWER_MODE=ON -DENABLE_SANITIZERS=OFF -B build

# Build
cmake --build build --parallel $(nproc)

# Run all tests
./build/safe_test

# Run specific test
./build/safe_test --gtest_filter=SafetyTestSuite.BufferOverflow

# List tests
./build/safe_test --gtest_list_tests
```

### Configuration Summary

- **C++ Standard**: C++23
- **Compiler**: Clang 20.1.8
- **Build System**: CMake 3.20+
- **Test Framework**: GoogleTest
- **Benchmark Framework**: Google Benchmark
- **Safety Library**: Microsoft GSL (Guidelines Support Library)

---

**Ready to use!** Open the project in CLion and start coding/testing.
