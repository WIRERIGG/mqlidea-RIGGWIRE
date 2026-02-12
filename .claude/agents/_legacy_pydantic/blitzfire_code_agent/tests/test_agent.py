"""Tests for the main Blitzfire agent."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from blitzfire_code_agent.agent import BlitzfireCodeAgent, quick_analyze
from blitzfire_code_agent.models import Architecture, OptimizationMode
from blitzfire_code_agent.providers import get_test_model


class TestBlitzfireCodeAgent:
    """Tests for the main Blitzfire agent class."""

    def test_agent_initialization(self, test_model):
        """Test agent initialization with test model."""
        agent = BlitzfireCodeAgent(model=test_model, session_id="test_session")

        assert agent.session_id == "test_session"
        assert agent.model is not None
        assert agent.agent is not None

    @pytest.mark.asyncio
    async def test_analyze_and_optimize_basic(self, sample_cpp_code, test_model):
        """Test basic analyze and optimize functionality."""
        agent = BlitzfireCodeAgent(model=test_model)

        response = await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            include_benchmarks=False,
            include_assembly=False
        )

        # Verify response structure
        assert response.analysis is not None
        assert response.strategy is not None
        assert response.personality_message is not None
        assert response.educational_insights is not None
        assert response.blitzfire_score >= 1 and response.blitzfire_score <= 10
        assert response.processing_time_seconds > 0

        # Verify analysis results
        assert response.analysis.lines_analyzed > 0
        assert response.analysis.code_hash is not None
        assert len(response.analysis.issues) >= 0

        # Verify strategy results
        assert len(response.strategy.tiers) > 0
        assert response.strategy.total_estimated_speedup >= 1.0

    @pytest.mark.asyncio
    async def test_analyze_different_modes(self, sample_cpp_code, test_model):
        """Test analysis with different optimization modes."""
        agent = BlitzfireCodeAgent(model=test_model)

        for mode in ["general", "hft", "embedded", "game"]:
            response = await agent.analyze_and_optimize(
                code_content=sample_cpp_code,
                optimization_mode=mode,
                include_benchmarks=False,
                include_assembly=False
            )

            assert response.analysis.optimization_mode.value == mode

    @pytest.mark.asyncio
    async def test_analyze_different_architectures(self, sample_cpp_code, test_model):
        """Test analysis with different target architectures."""
        agent = BlitzfireCodeAgent(model=test_model)

        for arch in ["x86_64", "arm64"]:
            response = await agent.analyze_and_optimize(
                code_content=sample_cpp_code,
                architecture=arch,
                include_benchmarks=False,
                include_assembly=False
            )

            assert response.analysis.architecture.value == arch

    @pytest.mark.asyncio
    async def test_analyze_with_assembly_validation(self, sample_cpp_code, test_model):
        """Test analysis with assembly validation enabled."""
        agent = BlitzfireCodeAgent(model=test_model)

        response = await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            include_assembly=True,
            include_benchmarks=False
        )

        # Assembly comparison might be None if validation fails
        # but the response should still be valid
        assert response is not None

    @pytest.mark.asyncio
    async def test_analyze_with_benchmarks(self, sample_cpp_code, test_model):
        """Test analysis with benchmarking enabled."""
        agent = BlitzfireCodeAgent(model=test_model)

        # Mock Docker availability
        with patch('blitzfire_code_agent.dependencies.BlitzfireDependencies.is_docker_available', return_value=True):
            response = await agent.analyze_and_optimize(
                code_content=sample_cpp_code,
                include_benchmarks=True,
                include_assembly=False
            )

            # Should have benchmark results
            assert isinstance(response.benchmark_results, list)

    @pytest.mark.asyncio
    async def test_chat_functionality(self, test_model):
        """Test chat functionality."""
        agent = BlitzfireCodeAgent(model=test_model)

        response = await agent.chat("Hello, how can you help me optimize C++ code?")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_chat_with_context(self, test_model, sample_cpp_code):
        """Test chat with conversation context."""
        agent = BlitzfireCodeAgent(model=test_model)

        # First, analyze some code to create context
        await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            include_benchmarks=False,
            include_assembly=False
        )

        # Then chat about it
        response = await agent.chat("What optimizations would you recommend?")

        assert isinstance(response, str)
        assert len(response) > 0

    @pytest.mark.asyncio
    async def test_analyze_for_hft(self, hft_sample_code, test_model):
        """Test HFT-specific analysis."""
        agent = BlitzfireCodeAgent(model=test_model)

        results = await agent.analyze_for_hft(hft_sample_code)

        assert "standard_analysis" in results
        assert "hft_audit" in results
        assert "combined_recommendations" in results

        # Verify HFT audit results
        hft_audit = results["hft_audit"]
        assert "safety_score" in hft_audit
        assert "total_issues" in hft_audit

        # Should find issues in HFT sample code
        assert hft_audit["total_issues"] > 0

    @pytest.mark.asyncio
    async def test_blitzfire_score_calculation(self, test_model):
        """Test Blitzfire score calculation logic."""
        agent = BlitzfireCodeAgent(model=test_model)

        # Test with different code qualities
        good_code = '''
        #include <vector>
        #include <algorithm>

        void process_data(std::vector<int>& data) {
            data.reserve(1000);
            std::sort(data.begin(), data.end());
        }
        '''

        bad_code = '''
        void inefficient_function() {
            std::string result = "";
            for (int i = 0; i < 10000; i++) {
                for (int j = 0; j < 10000; j++) {
                    result += std::to_string(i * j);
                }
            }
        }
        '''

        good_response = await agent.analyze_and_optimize(
            code_content=good_code,
            include_benchmarks=False,
            include_assembly=False
        )

        bad_response = await agent.analyze_and_optimize(
            code_content=bad_code,
            include_benchmarks=False,
            include_assembly=False
        )

        # Good code should have higher score
        assert good_response.blitzfire_score >= bad_response.blitzfire_score

    def test_hft_recommendations_generation(self, hft_sample_code, test_model):
        """Test HFT-specific recommendations generation."""
        agent = BlitzfireCodeAgent(model=test_model)

        # Test analysis results
        standard_analysis = Mock()
        standard_analysis.complexity.time_complexity = "O(n²)"

        hft_audit_results = {
            "total_issues": 3,
            "overflow_risks": [Mock()],
            "race_conditions": [Mock()],
            "determinism_issues": []
        }

        recommendations = agent._generate_hft_recommendations(standard_analysis, hft_audit_results)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0

        # Should include safety warnings for issues found
        safety_recs = [r for r in recommendations if "safety" in r.lower() or "critical" in r.lower()]
        assert len(safety_recs) > 0


class TestQuickAnalyze:
    """Tests for the quick_analyze convenience function."""

    @pytest.mark.asyncio
    async def test_quick_analyze_basic(self, sample_cpp_code):
        """Test basic quick analyze functionality."""
        with patch('blitzfire_code_agent.agent.BlitzfireCodeAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_response = Mock()
            mock_response.blitzfire_score = 7
            mock_response.analysis = Mock()
            mock_response.strategy = Mock()

            mock_agent.analyze_and_optimize = AsyncMock(return_value=mock_response)
            mock_agent_class.return_value = mock_agent

            response = await quick_analyze(sample_cpp_code)

            # Verify agent was called correctly
            mock_agent.analyze_and_optimize.assert_called_once_with(
                code_content=sample_cpp_code,
                optimization_mode="general",
                include_benchmarks=False,
                include_assembly=False
            )

    @pytest.mark.asyncio
    async def test_quick_analyze_different_modes(self, sample_cpp_code):
        """Test quick analyze with different modes."""
        with patch('blitzfire_code_agent.agent.BlitzfireCodeAgent') as mock_agent_class:
            mock_agent = Mock()
            mock_response = Mock()
            mock_agent.analyze_and_optimize = AsyncMock(return_value=mock_response)
            mock_agent_class.return_value = mock_agent

            for mode in ["general", "hft", "embedded", "game"]:
                await quick_analyze(sample_cpp_code, mode=mode)

                # Check that the mode was passed correctly
                call_args = mock_agent.analyze_and_optimize.call_args
                assert call_args[1]['optimization_mode'] == mode


class TestAgentIntegration:
    """Integration tests for agent functionality."""

    @pytest.mark.asyncio
    async def test_end_to_end_analysis(self, optimization_test_cases, test_model):
        """Test end-to-end analysis for various code patterns."""
        agent = BlitzfireCodeAgent(model=test_model)

        for test_name, code in optimization_test_cases.items():
            response = await agent.analyze_and_optimize(
                code_content=code,
                include_benchmarks=False,
                include_assembly=False
            )

            # Basic validation
            assert response.analysis is not None
            assert response.strategy is not None
            assert response.blitzfire_score >= 1

            # Should find some optimization opportunities
            assert len(response.strategy.tiers) > 0

    @pytest.mark.asyncio
    async def test_personality_consistency(self, sample_cpp_code, test_model):
        """Test that personality messages are consistent with findings."""
        agent = BlitzfireCodeAgent(model=test_model)

        response = await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            include_benchmarks=False,
            include_assembly=False
        )

        # Personality message should mention findings
        personality_msg = response.personality_message.lower()

        if len(response.analysis.issues) > 0:
            # Should mention optimization opportunities
            assert "optimization" in personality_msg or "speedup" in personality_msg

        if response.strategy.total_estimated_speedup > 2.0:
            # Should be enthusiastic about significant improvements
            assert any(word in personality_msg for word in ["excellent", "fantastic", "great"])

    @pytest.mark.asyncio
    async def test_educational_insights_quality(self, sample_cpp_code, test_model):
        """Test quality of educational insights."""
        agent = BlitzfireCodeAgent(model=test_model)

        response = await agent.analyze_and_optimize(
            code_content=sample_cpp_code,
            include_benchmarks=False,
            include_assembly=False
        )

        # Should provide educational insights
        assert len(response.educational_insights) > 0

        # Insights should be informative
        for insight in response.educational_insights:
            assert len(insight) > 20  # Minimum meaningful length
            assert any(keyword in insight.lower() for keyword in [
                "complexity", "performance", "optimization", "cache", "compiler"
            ])

    @pytest.mark.asyncio
    async def test_error_handling(self, test_model):
        """Test agent error handling."""
        agent = BlitzfireCodeAgent(model=test_model)

        # Test with invalid code
        try:
            response = await agent.analyze_and_optimize(
                code_content="This is not valid C++ code at all!",
                include_benchmarks=False,
                include_assembly=False
            )
            # Should still return a response, even for invalid code
            assert response is not None
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            assert isinstance(e, (ValueError, TypeError))

    @pytest.mark.asyncio
    async def test_concurrent_analysis(self, sample_cpp_code, test_model):
        """Test concurrent analysis requests."""
        agent = BlitzfireCodeAgent(model=test_model)

        # Run multiple analyses concurrently
        tasks = [
            agent.analyze_and_optimize(
                code_content=sample_cpp_code,
                include_benchmarks=False,
                include_assembly=False
            )
            for _ in range(3)
        ]

        responses = await asyncio.gather(*tasks)

        # All responses should be valid
        assert len(responses) == 3
        for response in responses:
            assert response is not None
            assert response.blitzfire_score >= 1