"""Integration tests for Blitzfire Code Agent."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

from blitzfire_code_agent.agent import BlitzfireCodeAgent
from blitzfire_code_agent.godbolt_integration import GodboltClient
from blitzfire_code_agent.benchmark_harness import DockerBenchmarkHarness
from blitzfire_code_agent.hft_specialization import HFTSpecializationEngine
from blitzfire_code_agent.settings import BlitzfireSettings


class TestGodboltIntegration:
    """Tests for Godbolt Compiler Explorer integration."""

    def test_godbolt_client_initialization(self, test_settings):
        """Test Godbolt client initialization."""
        client = GodboltClient(test_settings)

        assert client.base_url == test_settings.godbolt_base_url
        assert client.timeout == test_settings.godbolt_timeout
        assert client._cache == {}

    def test_cache_key_generation(self, test_settings):
        """Test cache key generation."""
        client = GodboltClient(test_settings)

        key1 = client._get_cache_key("code1", "clang", "-O3", "x86_64")
        key2 = client._get_cache_key("code1", "clang", "-O3", "x86_64")
        key3 = client._get_cache_key("code2", "clang", "-O3", "x86_64")

        assert key1 == key2  # Same inputs should generate same key
        assert key1 != key3  # Different inputs should generate different keys
        assert len(key1) == 16  # Should be truncated hash

    @pytest.mark.asyncio
    async def test_godbolt_mock_compilation(self, test_settings, mock_godbolt_response):
        """Test Godbolt compilation with mocked response."""
        client = GodboltClient(test_settings)

        # Mock the requests session
        client.session.post = Mock(return_value=Mock(
            status_code=200,
            json=Mock(return_value=mock_godbolt_response)
        ))

        result = client.compile_code("int main() { return 0; }")

        assert result is not None
        assert result.code == 0
        assert len(result.asm) > 0

    def test_assembly_diff_analysis(self, test_settings, mock_godbolt_response):
        """Test assembly difference analysis."""
        client = GodboltClient(test_settings)

        # Create mock assembly results
        original_result = Mock()
        original_result.asm = [{"text": "mov eax, 1"}, {"text": "ret"}]
        original_result.code = 0

        optimized_result = Mock()
        optimized_result.asm = [{"text": "xor eax, eax"}, {"text": "ret"}]  # Different assembly
        optimized_result.code = 0

        comparison = client._analyze_assembly_differences(original_result, optimized_result)

        assert comparison is not None
        assert comparison.original_instructions == 2
        assert comparison.optimized_instructions == 2


class TestBenchmarkHarnessIntegration:
    """Tests for Docker benchmarking harness integration."""

    def test_harness_initialization(self, test_settings):
        """Test benchmark harness initialization."""
        harness = DockerBenchmarkHarness(test_settings)

        assert harness.settings == test_settings
        # Docker should be disabled in test settings
        assert not harness.docker_available

    def test_benchmark_code_generation(self, test_settings):
        """Test benchmark code generation."""
        harness = DockerBenchmarkHarness(test_settings)

        code = harness.generate_benchmark_code(
            function_name="test_function",
            user_code="int add(int a, int b) { return a + b; }",
            test_code="result = add(1, 2);",
            setup_code="int result = 0;",
            test_sizes=[100, 1000]
        )

        assert "test_function" in code
        assert "benchmark::State" in code
        assert "BENCHMARK_MAIN()" in code
        assert "Range(100, 1000)" in code

    def test_benchmark_config_creation(self, test_settings):
        """Test benchmark configuration creation from optimization tiers."""
        harness = DockerBenchmarkHarness(test_settings)

        tiers = [
            {
                "name": "Cache Optimization",
                "code_before": "// Original code",
                "code_after": "// Optimized code"
            }
        ]

        configs = harness.create_benchmark_configs(tiers)

        assert len(configs) == 2  # Before and after versions
        assert "Cache_Optimization_Before" in [c.function_name for c in configs]
        assert "Cache_Optimization_After" in [c.function_name for c in configs]

    def test_fallback_benchmarking(self, test_settings):
        """Test fallback benchmarking when Docker is unavailable."""
        harness = DockerBenchmarkHarness(test_settings)

        config = Mock()
        config.function_name = "test_function"
        config.test_sizes = [100, 1000]
        config.iterations = 100
        config.code_snippet = "simple code"

        results = harness._fallback_benchmark(config)

        assert len(results) == len(config.test_sizes)
        for result in results:
            assert result.function_name == config.function_name
            assert result.mean_time_ns > 0
            assert result.iterations == config.iterations

    def test_execution_time_estimation(self, test_settings):
        """Test execution time estimation logic."""
        harness = DockerBenchmarkHarness(test_settings)

        # Test different code patterns
        simple_code = "int x = 5;"
        loop_code = "for (int i = 0; i < n; i++) { sum += i; }"
        optimized_code = "// optimized version with SIMD"
        nested_code = "// nested loops"

        simple_time = harness._estimate_execution_time(simple_code, 1000)
        loop_time = harness._estimate_execution_time(loop_code, 1000)
        optimized_time = harness._estimate_execution_time(optimized_code, 1000)
        nested_time = harness._estimate_execution_time(nested_code, 1000)

        # Loop code should take longer than simple code
        assert loop_time > simple_time

        # Optimized code should be faster than non-optimized
        assert optimized_time < simple_time

    def test_speedup_ratio_calculation(self, test_settings, mock_benchmark_results):
        """Test speedup ratio calculation between baseline and optimized versions."""
        harness = DockerBenchmarkHarness(test_settings)

        # Mock benchmark results
        results = {
            "Tier1_Before": mock_benchmark_results[:1],  # Baseline
            "Tier1_After": mock_benchmark_results[1:2]   # Optimized
        }

        harness._calculate_speedup_ratios(results)

        # Optimized version should have speedup ratio
        optimized_result = results["Tier1_After"][0]
        assert optimized_result["speedup_ratio"] is not None
        assert optimized_result["speedup_ratio"] > 1.0


class TestHFTSpecializationIntegration:
    """Tests for HFT specialization engine integration."""

    def test_hft_engine_initialization(self):
        """Test HFT specialization engine initialization."""
        engine = HFTSpecializationEngine()

        assert len(engine.risk_patterns) > 0
        assert len(engine.optimization_patterns) > 0
        assert len(engine.regulatory_patterns) > 0

    def test_hft_risk_pattern_detection(self, hft_sample_code):
        """Test HFT risk pattern detection."""
        engine = HFTSpecializationEngine()
        analysis = engine.analyze_hft_code(hft_sample_code)

        # Should find issues in the sample HFT code
        assert len(analysis["risk_issues"]) > 0
        assert analysis["safety_score"] < 10
        assert analysis["reliability_score"] < 10

        # Check specific risk categories
        overflow_issues = [issue for issue in analysis["risk_issues"]
                          if "overflow" in issue.issue_type]
        race_issues = [issue for issue in analysis["risk_issues"]
                      if "race_condition" in issue.issue_type]
        determinism_issues = [issue for issue in analysis["risk_issues"]
                             if "determinism" in issue.issue_type]

        # Should find all types of issues in the sample code
        assert len(overflow_issues) > 0
        assert len(race_issues) > 0
        assert len(determinism_issues) > 0

    def test_hft_optimization_tier_generation(self, hft_sample_code):
        """Test HFT-specific optimization tier generation."""
        engine = HFTSpecializationEngine()
        analysis = engine.analyze_hft_code(hft_sample_code)
        tiers = engine.generate_hft_optimization_tiers(hft_sample_code, analysis)

        assert len(tiers) > 0

        # First tier should be safety fixes if critical issues exist
        if any(issue.severity == "critical" for issue in analysis["risk_issues"]):
            assert "Safety" in tiers[0].name

        # Should include HFT-specific optimizations
        tier_names = [tier.name for tier in tiers]
        hft_specific_tiers = [name for name in tier_names
                             if any(keyword in name for keyword in
                                   ["Lock-Free", "Atomic", "NUMA", "Branch", "Memory Pool"])]
        assert len(hft_specific_tiers) > 0

    def test_hft_recommendations_generation(self):
        """Test HFT recommendation generation."""
        engine = HFTSpecializationEngine()

        # Mock analysis results with various issues
        analysis_results = {
            "safety_score": 6,
            "latency_score": 7,
            "reliability_score": 5,
            "risk_issues": [Mock(severity="critical"), Mock(severity="high")],
            "overflow_risks": [Mock()],
            "race_conditions": [Mock(), Mock()],
            "determinism_issues": []
        }

        recommendations = engine.generate_hft_recommendations(analysis_results)

        assert len(recommendations) > 0

        # Should include safety-focused recommendations for low safety score
        safety_recs = [rec for rec in recommendations if "safety" in rec.lower()]
        assert len(safety_recs) > 0

        # Should include reliability recommendations for low reliability score
        reliability_recs = [rec for rec in recommendations if "atomic" in rec.lower()]
        assert len(reliability_recs) > 0

    def test_hft_report_generation(self, hft_sample_code):
        """Test HFT report generation."""
        engine = HFTSpecializationEngine()
        report = engine.generate_hft_report(hft_sample_code)

        assert "HFT CODE ANALYSIS REPORT" in report
        assert "Safety Score:" in report
        assert "Latency Score:" in report
        assert "Reliability Score:" in report
        assert "RECOMMENDATIONS:" in report

        # Should identify critical issues
        if "CRITICAL ISSUES:" in report:
            assert "Line" in report  # Should show line numbers

    def test_hft_impact_calculation(self):
        """Test HFT impact calculation for different patterns."""
        engine = HFTSpecializationEngine()

        # Test with different risk patterns
        for pattern in engine.risk_patterns:
            impact = engine._calculate_hft_impact(pattern)
            assert impact >= 1.0

            # Critical risks should have higher impact
            if pattern.risk_level.value == "critical":
                assert impact >= 3.0


class TestFullSystemIntegration:
    """Full system integration tests."""

    @pytest.mark.asyncio
    async def test_complete_optimization_workflow(self, sample_cpp_code, test_settings):
        """Test complete optimization workflow from analysis to recommendations."""
        # Use test model to avoid external API calls
        from blitzfire_code_agent.providers import get_test_model

        agent = BlitzfireCodeAgent(
            model=get_test_model(),
            session_id="integration_test"
        )

        # Perform complete analysis
        response = await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            architecture="x86_64",
            optimization_mode="general",
            include_benchmarks=False,  # Disable for integration test
            include_assembly=False     # Disable for integration test
        )

        # Verify complete response structure
        assert response.analysis is not None
        assert response.strategy is not None
        assert response.personality_message is not None
        assert response.educational_insights is not None
        assert response.recommended_next_steps is not None
        assert response.additional_resources is not None

        # Verify analysis completeness
        analysis = response.analysis
        assert analysis.lines_analyzed > 0
        assert analysis.complexity is not None
        assert analysis.baseline_score > 0

        # Verify strategy completeness
        strategy = response.strategy
        assert len(strategy.tiers) > 0
        assert strategy.total_estimated_speedup >= 1.0
        assert len(strategy.recommended_order) == len(strategy.tiers)

        # Verify educational content
        assert len(response.educational_insights) > 0
        assert len(response.recommended_next_steps) > 0

    @pytest.mark.asyncio
    async def test_hft_workflow_integration(self, hft_sample_code, test_settings):
        """Test complete HFT workflow integration."""
        from blitzfire_code_agent.providers import get_test_model

        agent = BlitzfireCodeAgent(
            model=get_test_model(),
            session_id="hft_integration_test"
        )

        # Perform HFT-specific analysis
        hft_results = await agent.analyze_for_hft(hft_sample_code)

        # Verify HFT analysis completeness
        assert "standard_analysis" in hft_results
        assert "hft_audit" in hft_results
        assert "combined_recommendations" in hft_results

        standard_analysis = hft_results["standard_analysis"]
        assert standard_analysis.optimization_mode.value == "hft"

        hft_audit = hft_results["hft_audit"]
        assert "safety_score" in hft_audit
        assert hft_audit["total_issues"] > 0  # Sample code has issues

        recommendations = hft_results["combined_recommendations"]
        assert len(recommendations) > 0

    @pytest.mark.asyncio
    async def test_chat_integration_workflow(self, test_settings):
        """Test chat integration workflow."""
        from blitzfire_code_agent.providers import get_test_model

        agent = BlitzfireCodeAgent(
            model=get_test_model(),
            session_id="chat_integration_test"
        )

        # Test various chat scenarios
        chat_scenarios = [
            "Hello, how can you help me optimize C++ code?",
            "What is SIMD vectorization?",
            "How do I optimize cache performance?",
            "Explain multi-tier optimization strategies"
        ]

        for scenario in chat_scenarios:
            response = await agent.chat(scenario)

            assert isinstance(response, str)
            assert len(response) > 0
            # Should contain relevant keywords based on the question
            if "SIMD" in scenario:
                assert "SIMD" in response or "vector" in response
            elif "cache" in scenario:
                assert "cache" in response or "memory" in response

    def test_configuration_integration(self, temp_project_dir):
        """Test configuration integration with project structure."""
        # Create custom settings for project
        custom_settings = BlitzfireSettings(
            llm_provider="test",
            llm_api_key="test-key",
            llm_model="test-model",
            project_root=str(temp_project_dir),
            blitzfire_mode="general"
        )

        # Test that settings are properly loaded
        assert custom_settings.project_root == str(temp_project_dir)
        assert custom_settings.blitzfire_mode == "general"

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, test_settings):
        """Test system behavior under error conditions."""
        from blitzfire_code_agent.providers import get_test_model

        agent = BlitzfireCodeAgent(
            model=get_test_model(),
            session_id="error_recovery_test"
        )

        # Test with various problematic inputs
        error_scenarios = [
            "",  # Empty code
            "not valid c++ code at all",  # Invalid syntax
            "#" * 100000,  # Very large input (if size limits exist)
            "int main() { return 0; }",  # Minimal valid code
        ]

        for scenario in error_scenarios:
            try:
                response = await agent.analyze_and_optimize(
                    code_content=scenario,
                    include_benchmarks=False,
                    include_assembly=False
                )
                # Should always return a valid response
                assert response is not None
                assert response.blitzfire_score >= 1

            except Exception as e:
                # If exceptions occur, they should be handled gracefully
                assert isinstance(e, (ValueError, TypeError))

    def test_performance_characteristics(self, sample_cpp_code, test_settings):
        """Test performance characteristics of the system."""
        from blitzfire_code_agent.providers import get_test_model
        import time

        agent = BlitzfireCodeAgent(
            model=get_test_model(),
            session_id="performance_test"
        )

        # Measure analysis time
        start_time = time.time()

        # Run synchronously for timing
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        response = loop.run_until_complete(
            agent.analyze_and_optimize(
                code_content=sample_cpp_code,
                include_benchmarks=False,
                include_assembly=False
            )
        )

        end_time = time.time()
        analysis_time = end_time - start_time

        # Analysis should complete reasonably quickly
        assert analysis_time < 30.0  # Should complete within 30 seconds

        # Response should include timing information
        assert response.processing_time_seconds > 0
        assert response.processing_time_seconds < analysis_time