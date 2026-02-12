cmake_minimum_required(VERSION 3.20)

project(safe_test VERSION 1.0.0 LANGUAGES CXX)

# C++ Standard
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Export compile commands for IDEs
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Options
option(USE_GSL "Enable C++ Core Guidelines Support" ON)
option(ENABLE_POWER_MODE "Enable POWER-specific optimizations and checks" ON)
option(ENABLE_SANITIZERS "Enable sanitizers" ON)
option(ENABLE_ASAN "Enable AddressSanitizer" ON)
option(VALGRIND_COMPAT "Disable AVX2/newer instructions for Valgrind compatibility" OFF)

# Project directories
set(PROJECT_INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
set(PROJECT_TEST_DIR "${CMAKE_CURRENT_SOURCE_DIR}/tests")

# Dependency Management with FetchContent
include(FetchContent)

# Microsoft GSL
if(USE_GSL)
    FetchContent_Declare(
        gsl
        GIT_REPOSITORY https://github.com/microsoft/GSL.git
        GIT_TAG v4.2.0
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(gsl)
endif()

# GoogleTest
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.17.0
    GIT_SHALLOW TRUE
)
FetchContent_MakeAvailable(googletest)

# Google Benchmark
FetchContent_Declare(
    benchmark
    GIT_REPOSITORY https://github.com/google/benchmark.git
    GIT_TAG v1.9.4
    GIT_SHALLOW TRUE
)
set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "Disable benchmark's own tests" FORCE)
set(BENCHMARK_ENABLE_INSTALL OFF CACHE BOOL "Disable benchmark install" FORCE)
set(BENCHMARK_ENABLE_LTO OFF CACHE BOOL "Disable LTO in benchmark if conflicting" FORCE)
FetchContent_MakeAvailable(benchmark)

# Detect if building for x86
set(IS_X86 FALSE)
if(NOT APPLE)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "(x86_64|AMD64|i386|i686)")
        set(IS_X86 TRUE)
    endif()
elseif(CMAKE_OSX_ARCHITECTURES STREQUAL "x86_64")
    set(IS_X86 TRUE)
endif()

# Create test executable
add_executable(safe_test ${PROJECT_TEST_DIR}/safe_test.cpp)
target_compile_definitions(safe_test PRIVATE USE_GOOGLETEST)
target_include_directories(safe_test PUBLIC "${PROJECT_INCLUDE_DIR}")

# Link libraries
target_link_libraries(safe_test PRIVATE
    gtest
    gtest_main
    benchmark::benchmark
)

if(USE_GSL AND TARGET Microsoft.GSL::GSL)
    target_link_libraries(safe_test PRIVATE Microsoft.GSL::GSL)
endif()

# Link against LeadingExtremaIndicator DLL if available (when built as part of unified workspace)
if(TARGET LeadingExtremaIndicator)
    message(STATUS "Linking safe_test against LeadingExtremaIndicator DLL")
    target_link_libraries(safe_test PRIVATE LeadingExtremaIndicator)
    # Make DLL headers available to safe_test
    target_include_directories(safe_test PRIVATE
        "${CMAKE_CURRENT_SOURCE_DIR}/../LeadingExtremaIndicator_DLL/include"
    )
    target_compile_definitions(safe_test PRIVATE HAS_LEI_DLL)
endif()

# Compiler flags
if(ENABLE_POWER_MODE)
    target_compile_options(safe_test PRIVATE
        $<$<CXX_COMPILER_ID:GNU,Clang>:
        -Wall -Wextra -Wpedantic -Werror
        -Wshadow -Wnon-virtual-dtor -Wold-style-cast -Woverloaded-virtual -Wcast-align
        -Wsign-conversion -Wconversion -Wzero-as-null-pointer-constant -Wextra-semi
        -Wunused -Wuninitialized -Wdouble-promotion -Wformat=2 -Wformat-security
        -Wnull-dereference -Wimplicit-fallthrough -Wfloat-equal -Wcast-qual -Wwrite-strings
        -fstack-protector-strong
        -ftrivial-auto-var-init=zero
        -D_FORTIFY_SOURCE=3
        -fno-strict-aliasing
        -fvisibility=hidden
        -fvisibility-inlines-hidden
        -fcf-protection=full
        -ftrapv
        -D_GLIBCXX_ASSERTIONS
        -fstrict-flex-arrays=3
        -Wstrict-overflow=5
        $<$<CONFIG:Release>:-O3 -march=native -mtune=native -funroll-loops>
        $<$<CONFIG:Debug>:-g -O0>
        >
        $<$<CXX_COMPILER_ID:MSVC>:
        /W4 /WX /sdl /guard:cf
        $<$<CONFIG:Release>:/O2 /Oi>
        $<$<CONFIG:Debug>:/Zi /Od>
        >
    )

    # Sanitizers
    if(ENABLE_SANITIZERS)
        include(CheckCXXCompilerFlag)

        # Check for UBSan support
        check_cxx_compiler_flag("-fsanitize=undefined" SUPPORTS_UBSAN)
        if(SUPPORTS_UBSAN)
            target_compile_options(safe_test PRIVATE -fsanitize=undefined)
            target_link_options(safe_test PRIVATE -fsanitize=undefined)
        endif()

        # Check for ASan support
        if(ENABLE_ASAN)
            check_cxx_compiler_flag("-fsanitize=address" SUPPORTS_ASAN)
            if(SUPPORTS_ASAN)
                target_compile_options(safe_test PRIVATE -fsanitize=address)
                target_link_options(safe_test PRIVATE -fsanitize=address)
            endif()
        endif()
    endif()
else()
    target_compile_options(safe_test PRIVATE
        $<$<CXX_COMPILER_ID:GNU,Clang>:
        -Wall -Wextra -Wpedantic
        $<$<CONFIG:Release>:-O3>
        $<$<CONFIG:Debug>:-g -O0>
        >
        $<$<CXX_COMPILER_ID:MSVC>:
        /W4
        $<$<CONFIG:Release>:/O2>
        $<$<CONFIG:Debug>:/Zi /Od>
        >
    )
endif()

# Enable testing
enable_testing()
include(GoogleTest)
gtest_discover_tests(safe_test
    DISCOVERY_MODE POST_BUILD
    EXTRA_ARGS --gtest_color=yes
    PROPERTIES
        LABELS "unit"
        TIMEOUT 300
)

# Custom targets
add_custom_target(run_tests
    COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure
    DEPENDS safe_test
    COMMENT "Running all test cases"
)

# Clean gcov files before tests
if(WIN32)
    add_custom_target(clean-gcov
        COMMAND powershell -Command "Get-ChildItem -Path '${CMAKE_BINARY_DIR}' -Recurse -Filter '*.gcda' | Remove-Item -Force"
        COMMENT "Removing all .gcda files (Windows)"
    )
else()
    add_custom_target(clean-gcov
        COMMAND find "${CMAKE_BINARY_DIR}" -name "*.gcda" -delete
        COMMENT "Removing all .gcda files (Unix-like)"
    )
endif()
add_dependencies(safe_test clean-gcov)
