"""Tests for Blitzfire code analysis tools."""

import pytest
from blitzfire_code_agent.tools import (
    analyze_code, generate_optimizations, validate_assembly,
    benchmark_performance, hft_audit, interactive_chat
)
from blitzfire_code_agent.models import Architecture, OptimizationMode


class TestAnalyzeCode:
    """Tests for code analysis functionality."""

    def test_analyze_simple_code(self, sample_cpp_code):
        """Test basic code analysis."""
        result = analyze_code(sample_cpp_code)

        assert result.lines_analyzed > 0
        assert result.code_hash is not None
        assert result.architecture == Architecture.X86_64
        assert result.optimization_mode == OptimizationMode.GENERAL

    def test_analyze_complexity_detection(self, optimization_test_cases, expected_analysis_results):
        """Test complexity analysis accuracy."""
        for test_case, code in optimization_test_cases.items():
            result = analyze_code(code)
            expected = expected_analysis_results[test_case]

            assert result.complexity.time_complexity == expected["complexity"]

    def test_analyze_issue_detection(self, optimization_test_cases, expected_analysis_results):
        """Test issue detection accuracy."""
        for test_case, code in optimization_test_cases.items():
            result = analyze_code(code)
            expected = expected_analysis_results[test_case]

            assert len(result.issues) >= expected["issues_expected"]

    def test_analyze_optimization_candidates(self, optimization_test_cases, expected_analysis_results):
        """Test optimization candidate detection."""
        for test_case, code in optimization_test_cases.items():
            result = analyze_code(code)
            expected = expected_analysis_results[test_case]

            # Check if any expected candidates are found
            found_candidates = any(
                any(expected_candidate in candidate for expected_candidate in expected["optimization_candidates"])
                for candidate in result.optimization_candidates
            )
            assert found_candidates, f"No expected candidates found for {test_case}"

    def test_analyze_different_architectures(self, sample_cpp_code):
        """Test analysis with different target architectures."""
        for arch in ["x86_64", "arm64"]:
            result = analyze_code(sample_cpp_code, architecture=arch)
            assert result.architecture.value == arch

    def test_analyze_different_modes(self, sample_cpp_code):
        """Test analysis with different optimization modes."""
        for mode in ["general", "hft", "embedded", "game"]:
            result = analyze_code(sample_cpp_code, optimization_mode=mode)
            assert result.optimization_mode.value == mode

    def test_analyze_empty_code(self):
        """Test analysis with empty code."""
        result = analyze_code("")
        assert result.lines_analyzed == 0
        assert len(result.issues) == 0
        assert result.baseline_score > 0

    def test_analyze_focus_areas(self, sample_cpp_code):
        """Test analysis with specific focus areas."""
        result = analyze_code(
            sample_cpp_code,
            focus_areas=["loops", "memory"]
        )
        assert result is not None


class TestGenerateOptimizations:
    """Tests for optimization strategy generation."""

    def test_generate_basic_strategy(self, sample_cpp_code):
        """Test basic optimization strategy generation."""
        analysis = analyze_code(sample_cpp_code)
        strategy = generate_optimizations(analysis)

        assert len(strategy.tiers) > 0
        assert strategy.total_estimated_speedup >= 1.0
        assert len(strategy.recommended_order) == len(strategy.tiers)

    def test_generate_with_performance_target(self, sample_cpp_code):
        """Test strategy generation with performance target."""
        analysis = analyze_code(sample_cpp_code)
        strategy = generate_optimizations(analysis, performance_target=5.0)

        assert strategy.total_estimated_speedup > 1.0
        assert len(strategy.tiers) > 0

    def test_generate_with_safety_levels(self, sample_cpp_code):
        """Test strategy generation with different safety levels."""
        analysis = analyze_code(sample_cpp_code)

        for safety_level in ["low", "medium", "high"]:
            strategy = generate_optimizations(analysis, safety_level=safety_level)
            assert len(strategy.warnings) >= 0

            if safety_level == "high":
                # High safety should have more warnings
                assert len(strategy.warnings) >= 2

    def test_generate_without_advanced_optimizations(self, sample_cpp_code):
        """Test strategy generation excluding advanced optimizations."""
        analysis = analyze_code(sample_cpp_code)
        strategy = generate_optimizations(analysis, include_advanced=False)

        # Should not include SIMD or threading tiers
        advanced_tiers = [t for t in strategy.tiers if "SIMD" in t.name or "Threading" in t.name]
        assert len(advanced_tiers) == 0

    def test_tier_properties(self, sample_cpp_code):
        """Test that all tiers have required properties."""
        analysis = analyze_code(sample_cpp_code)
        strategy = generate_optimizations(analysis)

        for tier in strategy.tiers:
            assert tier.tier_number > 0
            assert len(tier.name) > 0
            assert len(tier.description) > 0
            assert tier.estimated_speedup >= 1.0
            assert tier.difficulty in ["easy", "medium", "hard"]
            assert tier.safety_impact in ["none", "low", "medium", "high"]
            assert len(tier.code_before) > 0
            assert len(tier.code_after) > 0
            assert len(tier.explanation) > 0

    def test_complexity_based_optimization(self):
        """Test optimization based on code complexity."""
        # O(n²) code should get algorithmic optimization suggestions
        nested_loop_code = '''
        for (int i = 0; i < n; i++) {
            for (int j = 0; j < n; j++) {
                result += i * j;
            }
        }
        '''

        analysis = analyze_code(nested_loop_code)
        strategy = generate_optimizations(analysis)

        # Should suggest algorithmic improvements for O(n²) code
        algorithmic_tiers = [t for t in strategy.tiers if "Algorithm" in t.name]
        assert len(algorithmic_tiers) > 0


class TestValidateAssembly:
    """Tests for assembly validation (mock implementation)."""

    def test_validate_assembly_basic(self):
        """Test basic assembly validation."""
        original_code = "int add(int a, int b) { return a + b; }"
        optimized_code = "int add(int a, int b) { return a + b; }"

        result = validate_assembly(original_code, optimized_code)

        assert result is not None
        assert result.original_instructions > 0
        assert result.optimized_instructions > 0
        assert isinstance(result.vectorization_detected, bool)
        assert isinstance(result.loop_unrolling_detected, bool)
        assert isinstance(result.key_differences, list)
        assert isinstance(result.optimization_artifacts, list)

    def test_validate_assembly_with_simd(self):
        """Test assembly validation with SIMD code."""
        original_code = "for (int i = 0; i < n; i++) result[i] = a[i] + b[i];"
        optimized_code = "// SIMD vectorized version\nfor (int i = 0; i < n; i += 8) { /* vector ops */ }"

        result = validate_assembly(original_code, optimized_code)

        # Mock should detect SIMD keywords
        assert result.vectorization_detected == True

    def test_validate_assembly_different_compilers(self):
        """Test assembly validation with different compilers."""
        code = "int multiply(int a, int b) { return a * b; }"

        for compiler in ["clang_trunk", "gcc_trunk"]:
            result = validate_assembly(code, code, compiler=compiler)
            assert result is not None


class TestBenchmarkPerformance:
    """Tests for performance benchmarking (mock implementation)."""

    def test_benchmark_basic(self):
        """Test basic benchmarking functionality."""
        test_functions = ["baseline_function", "optimized_function"]
        results = benchmark_performance(test_functions)

        assert len(results) > 0
        for result in results:
            assert result.function_name in test_functions
            assert result.input_size > 0
            assert result.mean_time_ns > 0
            assert result.std_dev_ns >= 0
            assert result.iterations > 0

    def test_benchmark_with_test_sizes(self):
        """Test benchmarking with specific test sizes."""
        test_functions = ["test_function"]
        test_sizes = [100, 1000, 10000]

        results = benchmark_performance(test_functions, test_sizes=test_sizes)

        # Should have results for each test size
        found_sizes = {result.input_size for result in results}
        assert all(size in found_sizes for size in test_sizes)

    def test_benchmark_speedup_calculation(self):
        """Test speedup ratio calculation."""
        test_functions = ["baseline_function", "optimized_function"]
        results = benchmark_performance(test_functions)

        optimized_results = [r for r in results if "optimized" in r.function_name]
        if optimized_results:
            # Some optimized results should have speedup ratios
            assert any(r.speedup_ratio is not None for r in optimized_results)


class TestHFTAudit:
    """Tests for HFT-specific code auditing."""

    def test_hft_audit_basic(self, hft_sample_code):
        """Test basic HFT audit functionality."""
        result = hft_audit(hft_sample_code)

        assert "overflow_risks" in result
        assert "race_conditions" in result
        assert "determinism_issues" in result
        assert "safety_score" in result
        assert "recommendations" in result

        # Should find issues in the HFT sample code
        assert len(result["overflow_risks"]) > 0
        assert len(result["race_conditions"]) > 0
        assert len(result["determinism_issues"]) > 0

    def test_hft_audit_levels(self, hft_sample_code):
        """Test different HFT audit levels."""
        for level in ["basic", "standard", "comprehensive"]:
            result = hft_audit(hft_sample_code, audit_level=level)
            assert "safety_score" in result

    def test_hft_audit_categories(self, hft_sample_code):
        """Test HFT audit with specific categories."""
        for category in ["overflow", "races", "determinism"]:
            result = hft_audit(
                hft_sample_code,
                check_categories=[category]
            )
            assert "safety_score" in result

    def test_hft_audit_safe_code(self):
        """Test HFT audit with safe code."""
        safe_code = '''
        #include <atomic>

        std::atomic<double> current_price{100.50};

        void update_price(double new_price) {
            current_price.store(new_price, std::memory_order_release);
        }

        bool compare_prices(double a, double b, double epsilon = 1e-9) {
            return std::abs(a - b) < epsilon;
        }
        '''

        result = hft_audit(safe_code)
        assert result["safety_score"] >= 8  # Should be high for safe code


class TestInteractiveChat:
    """Tests for interactive chat functionality."""

    def test_chat_greeting(self):
        """Test chat greeting responses."""
        for greeting in ["hello", "hi", "Hello there"]:
            response = interactive_chat(greeting)
            assert "Welcome" in response or "excited" in response

    def test_chat_simd_question(self):
        """Test SIMD-related questions."""
        response = interactive_chat("What is SIMD?")
        assert "SIMD" in response
        assert "vector" in response or "parallel" in response

    def test_chat_cache_question(self):
        """Test cache-related questions."""
        response = interactive_chat("How does CPU cache work?")
        assert "cache" in response
        assert "L1" in response or "memory" in response

    def test_chat_optimization_question(self):
        """Test optimization strategy questions."""
        response = interactive_chat("What is multi-tier optimization?")
        assert "tier" in response or "optimization" in response

    def test_chat_with_context(self):
        """Test chat with analysis context."""
        context = {
            "previous_analysis": {
                "complexity": "O(n²)",
                "issues": 3
            }
        }

        response = interactive_chat("How can I optimize this?", context=context)
        assert len(response) > 0

    def test_chat_educational_mode(self):
        """Test chat with educational mode enabled/disabled."""
        question = "What is vectorization?"

        edu_response = interactive_chat(question, educational_mode=True)
        basic_response = interactive_chat(question, educational_mode=False)

        # Educational mode should provide more detailed responses
        assert len(edu_response) >= len(basic_response)