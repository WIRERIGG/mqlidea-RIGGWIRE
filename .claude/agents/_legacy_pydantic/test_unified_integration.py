#!/usr/bin/env python3
"""
Integration Tests for Unified Clang-Tidy + BLITZFIRE Pipeline
=============================================================

Tests the permanent integration between agents to ensure they work together correctly.
"""

import asyncio
import tempfile
import os
import sys
from pathlib import Path
import pytest
import json

# Add agent paths
sys.path.append('/IdeaProjects/wire_ground/.claude/agents')

from shared_integration import (
    PipelineConfig,
    PipelineResult,
    IntegratedPipeline,
    optimize_with_quality,
    INTEGRATION_ENABLED
)

# Test C++ code samples
SIMPLE_CPP_CODE = """
#include <iostream>
#include <vector>

int main() {
    std::vector<int> data = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int i = 0; i < data.size(); ++i) {
        sum += data[i];
        std::cout << "Value: " << data[i] << std::endl;
    }
    std::cout << "Sum: " << sum << std::endl;
    return 0;
}
"""

CPP_WITH_WARNINGS = """
#include <iostream>
#include <vector>

int main() {
    std::vector<int> data = {1, 2, 3, 4, 5};
    int sum = 0;
    for (int i = 0; i < data.size(); i++) { // Warning: use size_t
        sum += data[i];
        std::cout << "Value: " << data[i] << std::endl; // Warning: use \n
    }
    std::cout << "Sum: " << sum << std::endl; // Warning: use \n
    return 0;
}
"""

PERFORMANCE_CPP_CODE = """
#include <iostream>
#include <vector>
#include <algorithm>

int main() {
    std::vector<float> data(1000);
    std::fill(data.begin(), data.end(), 1.0f);
    
    // Unoptimized loop - candidate for SIMD vectorization
    float sum = 0.0f;
    for (int i = 0; i < data.size(); ++i) {
        sum += data[i] * 2.0f + 1.0f;
        std::cout << sum << std::endl; // I/O in loop - candidate for buffering
    }
    
    return 0;
}
"""


class TestIntegrationSetup:
    """Test the integration setup and availability."""
    
    def test_integration_enabled(self):
        """Test that integration is properly enabled."""
        assert INTEGRATION_ENABLED is not None, "Integration should be available"
    
    def test_import_shared_module(self):
        """Test that shared integration module can be imported."""
        from shared_integration import PipelineConfig, IntegratedPipeline
        
        config = PipelineConfig(source_file="test.cpp")
        assert config.source_file == "test.cpp"
        assert config.optimization_level == "advanced"
        
        pipeline = IntegratedPipeline(config)
        assert pipeline.config == config
    
    def test_import_agent_integrations(self):
        """Test that both agents can import integration components."""
        try:
            from blitzfire_cpp_optimizer.agent import optimize_with_clang_tidy_check
            from clang_tidy_ai_agent.agent import ClangTidyFactoryOrchestrator
            assert True, "Both agents imported successfully"
        except ImportError as e:
            pytest.skip(f"Agent imports not available: {e}")


class TestPipelineWorkflow:
    """Test the complete pipeline workflow."""
    
    @pytest.mark.asyncio
    async def test_simple_pipeline_execution(self):
        """Test basic pipeline execution with simple C++ code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(SIMPLE_CPP_CODE)
            f.flush()
            
            try:
                config = PipelineConfig(
                    source_file=f.name,
                    optimization_level="quick_wins",
                    strict_mode=False,  # Allow some warnings for test
                    backup_original=True,
                    generate_report=True
                )
                
                pipeline = IntegratedPipeline(config)
                result = await pipeline.run_pipeline()
                
                # Check basic result structure
                assert isinstance(result, PipelineResult)
                assert result.stage_completed is not None
                assert isinstance(result.errors, list)
                
                # Check that backup was created if requested
                if config.backup_original and result.backup_file:
                    assert Path(result.backup_file).exists()
                
            finally:
                os.unlink(f.name)
    
    @pytest.mark.asyncio
    async def test_convenience_function(self):
        """Test the convenience optimize_with_quality function."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(SIMPLE_CPP_CODE)
            f.flush()
            
            try:
                result = await optimize_with_quality(
                    source_file=f.name,
                    optimization_level="quick_wins",
                    strict=False
                )
                
                assert isinstance(result, PipelineResult)
                assert result.stage_completed is not None
                
            finally:
                os.unlink(f.name)


class TestAgentInteraction:
    """Test the interaction between agents."""
    
    @pytest.mark.asyncio
    async def test_blitzfire_with_clang_tidy_check(self):
        """Test BLITZFIRE optimizer with clang-tidy validation."""
        try:
            from blitzfire_cpp_optimizer.agent import optimize_with_clang_tidy_check
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(SIMPLE_CPP_CODE)
                f.flush()
                
                try:
                    result = await optimize_with_clang_tidy_check(
                        ctx=None,
                        code=SIMPLE_CPP_CODE,
                        source_file=f.name,
                        optimization_level="quick_wins",
                        auto_fix_warnings=False
                    )
                    
                    assert isinstance(result, dict)
                    assert "success" in result
                    assert "clang_tidy_status" in result
                    
                finally:
                    os.unlink(f.name)
                    
        except ImportError:
            pytest.skip("BLITZFIRE optimizer not available")
    
    @pytest.mark.asyncio
    async def test_clang_tidy_fix_and_optimize(self):
        """Test clang-tidy agent with BLITZFIRE optimization."""
        try:
            from clang_tidy_ai_agent.agent import ClangTidyFactoryOrchestrator
            from clang_tidy_ai_agent.models import ClangTidyDependencies
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                f.write(SIMPLE_CPP_CODE)
                f.flush()
                
                try:
                    deps = ClangTidyDependencies(
                        source_file=f.name,
                        clang_tidy_checks="readability-*,modernize-*"
                    )
                    
                    orchestrator = ClangTidyFactoryOrchestrator(deps)
                    result = await orchestrator.fix_and_optimize(
                        file_path=f.name,
                        optimization_level="quick_wins"
                    )
                    
                    assert isinstance(result, dict)
                    assert "success" in result
                    assert "clang_tidy_phase" in result
                    assert "blitzfire_phase" in result
                    
                finally:
                    os.unlink(f.name)
                    
        except ImportError:
            pytest.skip("Clang-tidy agent not available")


class TestCLIInterface:
    """Test the CLI interface."""
    
    def test_cli_import(self):
        """Test that CLI module can be imported."""
        from unified_pipeline import UnifiedPipelineCLI
        
        cli = UnifiedPipelineCLI()
        assert cli.parser is not None
        
        # Test help doesn't crash
        help_output = cli.parser.format_help()
        assert "fix-and-optimize" in help_output
        assert "analyze" in help_output
    
    @pytest.mark.asyncio
    async def test_cli_status_command(self):
        """Test CLI status command."""
        from unified_pipeline import UnifiedPipelineCLI
        
        cli = UnifiedPipelineCLI()
        
        # Test status command
        result = await cli.cmd_status(None)
        assert result == 0  # Success exit code


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """Test handling of nonexistent files."""
        config = PipelineConfig(
            source_file="nonexistent_file.cpp",
            strict_mode=False
        )
        
        pipeline = IntegratedPipeline(config)
        result = await pipeline.run_pipeline()
        
        # Should fail gracefully
        assert not result.success
        assert len(result.errors) > 0
    
    @pytest.mark.asyncio
    async def test_invalid_cpp_code(self):
        """Test handling of invalid C++ code."""
        invalid_code = """
        #include <iostream>
        
        int main() {
            // Missing semicolon and brace
            std::cout << "Hello"
            return 0
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(invalid_code)
            f.flush()
            
            try:
                result = await optimize_with_quality(
                    source_file=f.name,
                    optimization_level="quick_wins",
                    strict=False
                )
                
                # Should complete but may report errors
                assert isinstance(result, PipelineResult)
                
            finally:
                os.unlink(f.name)


class TestPerformanceIntegration:
    """Test performance-focused integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_performance_optimization_pipeline(self):
        """Test pipeline with performance-heavy code."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(PERFORMANCE_CPP_CODE)
            f.flush()
            
            try:
                config = PipelineConfig(
                    source_file=f.name,
                    optimization_level="advanced",
                    enable_simd=True,
                    enable_parallel=True,
                    enable_cache_opt=True,
                    strict_mode=False
                )
                
                pipeline = IntegratedPipeline(config)
                result = await pipeline.run_pipeline()
                
                # Should identify optimization opportunities
                assert isinstance(result, PipelineResult)
                
                # Check if optimization report exists
                if result.success and result.optimization_report:
                    opt_report = result.optimization_report
                    assert isinstance(opt_report, dict)
                
            finally:
                os.unlink(f.name)


def run_integration_tests():
    """Run all integration tests."""
    print("🧪 Running Unified Pipeline Integration Tests")
    print("=" * 50)
    
    # Import pytest
    try:
        import pytest
    except ImportError:
        print("❌ pytest not available, running basic tests...")
        
        # Run basic tests manually
        setup_test = TestIntegrationSetup()
        setup_test.test_integration_enabled()
        setup_test.test_import_shared_module()
        
        print("✅ Basic integration tests passed")
        return True
    
    # Run with pytest
    test_file = __file__
    exit_code = pytest.main([
        test_file,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])
    
    return exit_code == 0


if __name__ == "__main__":
    success = run_integration_tests()
    if success:
        print("\n✅ All integration tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)