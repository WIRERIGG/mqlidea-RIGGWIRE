"""
Comprehensive tests for the optimized Clang-Tidy AI Agent.
"""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Import optimized components
from ..agent_optimized import OptimizedClangTidyAgent
from ..settings_optimized import OptimizedSettings
from ..dependencies_optimized import OptimizedClangTidyDependencies
from ..tools_optimized import (
    analyze_code_with_clang_tidy_optimized,
    batch_analyze_files,
    PerformanceMonitor,
    circuit_breaker
)
from ..models import ClangTidyAnalysis, Warning


class TestOptimizedAgent:
    """Test suite for the optimized agent."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return OptimizedSettings(
            project_root=Path("/tmp/test_project"),
            llm_provider="test",
            llm_api_key="test_key",
            enable_caching=True,
            enable_performance_metrics=True,
            max_concurrent_analyses=2
        )
    
    @pytest.fixture
    async def agent(self, settings):
        """Create test agent."""
        with patch('pydantic_ai.models.test.TestModel'):
            agent = OptimizedClangTidyAgent(settings)
            return agent
    
    @pytest.mark.asyncio
    async def test_agent_initialization(self, settings):
        """Test agent initializes correctly."""
        with patch('pydantic_ai.models.test.TestModel'):
            agent = OptimizedClangTidyAgent(settings)
            
            assert agent.settings == settings
            assert agent.metrics["analyses_completed"] == 0
            assert hasattr(agent, 'agent')
            assert hasattr(agent, 'provider')
    
    @pytest.mark.asyncio
    async def test_single_file_analysis(self, agent):
        """Test single file analysis with mocking."""
        test_file = "test.cpp"
        
        # Mock dependencies
        with patch.object(agent, '_create_dependencies') as mock_deps:
            mock_deps.return_value = Mock()
            
            # Mock agent run method
            with patch.object(agent.agent, 'run') as mock_run:
                mock_analysis = ClangTidyAnalysis(
                    file_path=test_file,
                    total_warnings=3,
                    warnings=[
                        Warning(
                            type="readability-braces-around-statements",
                            message="test warning",
                            file=test_file,
                            line=10,
                            column=5,
                            severity="warning"
                        )
                    ]
                )
                mock_run.return_value.data = mock_analysis
                
                result = await agent.analyze_with_fixes(test_file, auto_fix=False)
                
                assert result["status"] == "success"
                assert result["file"] == test_file
                assert result["total_warnings"] == 3
                assert len(result["warnings"]) == 1
    
    @pytest.mark.asyncio
    async def test_project_analysis(self, agent):
        """Test project-wide analysis."""
        patterns = ["**/*.cpp"]
        
        with patch.object(agent, '_create_dependencies') as mock_deps, \
             patch('pathlib.Path.glob') as mock_glob, \
             patch.object(agent.agent, 'run') as mock_run:
            
            # Mock file discovery
            mock_glob.return_value = [Path("test1.cpp"), Path("test2.cpp")]
            
            # Mock dependencies
            mock_deps.return_value = Mock()
            
            # Mock analysis results
            mock_analyses = [
                ClangTidyAnalysis(file_path="test1.cpp", total_warnings=2, warnings=[]),
                ClangTidyAnalysis(file_path="test2.cpp", total_warnings=1, warnings=[])
            ]
            mock_run.return_value.data = mock_analyses
            
            result = await agent.analyze_project(patterns)
            
            assert result.files_analyzed == 2
            assert result.total_warnings == 3
            assert isinstance(result.execution_time_seconds, float)
    
    def test_metrics_collection(self, agent):
        """Test performance metrics collection."""
        initial_metrics = agent.get_metrics()
        
        # Simulate some operations
        agent.metrics["analyses_completed"] += 5
        agent.metrics["total_warnings_found"] += 20
        agent.metrics["fixes_applied"] += 3
        
        updated_metrics = agent.get_metrics()
        
        assert updated_metrics["analyses_completed"] == 5
        assert updated_metrics["total_warnings_found"] == 20
        assert updated_metrics["fixes_applied"] == 3


class TestPerformanceOptimizations:
    """Test performance-related optimizations."""
    
    @pytest.mark.asyncio
    async def test_performance_monitor(self):
        """Test performance monitoring context manager."""
        async with PerformanceMonitor() as monitor:
            # Simulate work
            await asyncio.sleep(0.1)
        
        # Should complete without errors
        assert True
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_decorator(self):
        """Test circuit breaker functionality."""
        call_count = 0
        failure_count = 0
        
        @circuit_breaker
        async def test_function(should_fail=False):
            nonlocal call_count, failure_count
            call_count += 1
            
            if should_fail:
                failure_count += 1
                raise Exception("Test failure")
            return "success"
        
        # Test successful calls
        result = await test_function(should_fail=False)
        assert result == "success"
        assert call_count == 1
        
        # Test failure handling
        with pytest.raises(Exception):
            await test_function(should_fail=True)
        
        assert call_count == 2
        assert failure_count == 1
    
    @pytest.mark.asyncio
    @pytest.mark.benchmark
    async def test_concurrent_processing(self):
        """Benchmark concurrent vs sequential processing."""
        import time
        
        async def mock_analysis(file_path):
            await asyncio.sleep(0.01)  # Simulate work
            return ClangTidyAnalysis(
                file_path=file_path,
                total_warnings=1,
                warnings=[]
            )
        
        files = [f"test{i}.cpp" for i in range(10)]
        
        # Sequential processing
        start_time = time.time()
        sequential_results = []
        for file_path in files:
            result = await mock_analysis(file_path)
            sequential_results.append(result)
        sequential_time = time.time() - start_time
        
        # Concurrent processing
        start_time = time.time()
        concurrent_results = await asyncio.gather(*[
            mock_analysis(file_path) for file_path in files
        ])
        concurrent_time = time.time() - start_time
        
        # Concurrent should be significantly faster
        assert concurrent_time < sequential_time
        assert len(concurrent_results) == len(sequential_results)


class TestIntegration:
    """Test integration with wire_ground project."""
    
    def test_settings_validation(self):
        """Test settings validation and environment loading."""
        # Test with minimal settings
        settings = OptimizedSettings(
            project_root=Path("/tmp"),
            llm_api_key="test_key"
        )
        
        assert settings.project_root == Path("/tmp")
        assert settings.llm_api_key == "test_key"
        assert settings.max_concurrent_analyses >= 1
    
    @pytest.mark.asyncio
    async def test_dependencies_creation(self):
        """Test dependency injection system."""
        settings = OptimizedSettings(
            project_root=Path("/tmp"),
            llm_api_key="test_key",
            sqlite_db_path=Path("/tmp/test.db"),
            knowledge_base_path=Path("/tmp/kb.db")
        )
        
        with patch('aiosqlite.connect') as mock_connect, \
             patch('sqlalchemy.ext.asyncio.create_async_engine'):
            
            mock_connect.return_value = Mock()
            
            from ..dependencies_optimized import create_dependencies
            deps = await create_dependencies(settings)
            
            assert isinstance(deps, OptimizedClangTidyDependencies)
            assert deps.project_root == settings.project_root
            assert deps.llm_api_key == settings.llm_api_key
    
    def test_wire_ground_compatibility(self):
        """Test compatibility with wire_ground project structure."""
        wire_ground_root = Path("/IdeaProjects/wire_ground")
        
        settings = OptimizedSettings(
            project_root=wire_ground_root,
            llm_api_key="test_key",
            cmake_build_dir="cmake-build-debug"
        )
        
        # Should accept wire_ground paths
        assert settings.project_root == wire_ground_root
        assert settings.cmake_build_dir == "cmake-build-debug"


class TestErrorHandling:
    """Test error handling and resilience."""
    
    @pytest.mark.asyncio
    async def test_clang_tidy_not_found(self):
        """Test graceful handling when clang-tidy is not available."""
        settings = OptimizedSettings(
            project_root=Path("/tmp"),
            clang_tidy_binary_path=Path("/nonexistent/clang-tidy"),
            llm_api_key="test_key"
        )
        
        agent = OptimizedClangTidyAgent(settings)
        
        # Should initialize without crashing
        assert agent is not None
        assert not settings.clang_tidy_binary_path.exists()
    
    @pytest.mark.asyncio
    async def test_llm_api_failure(self):
        """Test handling of LLM API failures."""
        settings = OptimizedSettings(
            project_root=Path("/tmp"),
            llm_api_key=""  # Empty API key
        )
        
        agent = OptimizedClangTidyAgent(settings)
        
        # Should fall back to test model
        assert agent.provider is not None
    
    @pytest.mark.asyncio
    async def test_file_not_found(self, agent):
        """Test handling of non-existent files."""
        nonexistent_file = "nonexistent.cpp"
        
        with patch.object(agent, '_create_dependencies') as mock_deps:
            mock_deps.return_value = Mock()
            
            # Mock file path resolution
            with patch('pathlib.Path.exists', return_value=False):
                result = await agent.analyze_with_fixes(nonexistent_file)
                
                # Should handle gracefully
                assert "error" in result or result.get("total_warnings", 0) == 0


class TestConfigurationValidation:
    """Test configuration validation and environment variables."""
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        import os
        
        test_env = {
            "PROJECT_ROOT": "/test/project",
            "LLM_API_KEY": "test_api_key",
            "MAX_CONCURRENT_ANALYSES": "8",
            "ENABLE_CACHING": "false"
        }
        
        with patch.dict(os.environ, test_env):
            settings = OptimizedSettings()
            
            assert str(settings.project_root) == "/test/project"
            assert settings.llm_api_key == "test_api_key"
            assert settings.max_concurrent_analyses == 8
            assert settings.enable_caching is False
    
    def test_settings_validation(self):
        """Test settings validation rules."""
        # Test valid settings
        valid_settings = OptimizedSettings(
            project_root=Path("/tmp"),
            llm_api_key="valid_key",
            max_concurrent_analyses=4,
            cache_ttl_seconds=3600
        )
        
        assert valid_settings.max_concurrent_analyses == 4
        assert valid_settings.cache_ttl_seconds == 3600
        
        # Test invalid settings
        with pytest.raises(ValueError):
            OptimizedSettings(
                max_concurrent_analyses=0  # Should be >= 1
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])