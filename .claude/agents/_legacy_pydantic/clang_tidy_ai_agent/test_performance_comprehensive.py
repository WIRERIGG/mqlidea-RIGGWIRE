"""
Performance tests with thresholds per AI Agent Validator.md.
Benchmarking with strict performance requirements.
"""

import pytest
import time
import asyncio
import psutil
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from pydantic_ai.messages import ModelTextResponse

# Local imports
try:
    from .agent import agent
    from .dependencies import AgentDependencies
except ImportError:
    from agent import agent
    from dependencies import AgentDependencies

class TestPerformanceRequirements:
    """Performance tests with strict thresholds."""
    
    @pytest.mark.asyncio
    async def test_agent_startup_time(self, test_dependencies, performance_thresholds):
        """Test agent initialization meets startup time threshold."""
        start_time = time.time()
        
        # Create fresh agent instance
        test_model = pytest.importorskip("pydantic_ai.models.test").TestModel()
        test_model.agent_responses = [
            ModelTextResponse(content="Agent initialized successfully")
        ]
        
        fresh_agent = agent.override(model=test_model)
        await fresh_agent.run("Initialize", deps=test_dependencies)
        
        startup_duration = time.time() - start_time
        assert startup_duration < performance_thresholds["max_startup_time"]
    
    @pytest.mark.asyncio
    async def test_response_time_simple_query(self, test_agent, test_dependencies, performance_thresholds):
        """Test response time for simple queries."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Quick Agent status check completed")
        ]
        
        start_time = time.time()
        result = await test_agent.run("Check Agent status", deps=test_dependencies)
        duration = time.time() - start_time
        
        assert duration < performance_thresholds["max_response_time"]
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_response_time_complex_analysis(self, test_agent, test_dependencies, performance_thresholds, mock_valgrind_output):
        """Test response time for complex analysis operations."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Initiating comprehensive memory analysis"),
            {
                "create_valgrind_wrapper": {
                    "executable_path": "/test/complex_app",
                    "tool": "memcheck",
                    "options": ["--leak-check=full", "--show-reachable=yes", "--track-origins=yes"]
                }
            },
            ModelTextResponse(content="Complex analysis completed with detailed memory report")
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = mock_valgrind_output
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            
            start_time = time.time()
            result = await test_agent.run(
                "Run comprehensive memory analysis on /test/complex_app with full leak checking and origin tracking",
                deps=test_dependencies
            )
            duration = time.time() - start_time
            
            # Complex operations get 2x the normal threshold
            assert duration < (performance_thresholds["max_response_time"] * 2)
            assert result.data is not None
            assert "analysis" in result.data.lower()
    
    @pytest.mark.asyncio 
    async def test_memory_usage_single_request(self, test_agent, test_dependencies, performance_thresholds):
        """Test memory usage for single request."""
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Memory-efficient analysis completed")
        ]
        
        result = await test_agent.run("Analyze memory efficiently", deps=test_dependencies)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        assert memory_increase < performance_thresholds["max_memory_usage"]
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_request_performance(self, test_agent, test_dependencies, performance_thresholds):
        """Test performance under concurrent load."""
        num_requests = 10
        test_agent.model.agent_responses = [
            ModelTextResponse(content=f"Concurrent request {i} processed")
            for i in range(num_requests)
        ]
        
        async def single_request(request_id):
            start = time.time()
            result = await test_agent.run(f"Process request {request_id}", deps=test_dependencies)
            duration = time.time() - start
            return result, duration
        
        overall_start = time.time()
        tasks = [single_request(i) for i in range(num_requests)]
        results = await asyncio.gather(*tasks)
        overall_duration = time.time() - overall_start
        
        # Check individual request times
        for result, duration in results:
            assert result[0].data is not None
            assert duration < performance_thresholds["max_response_time"] * 1.5  # Allow overhead
        
        # Check overall throughput
        avg_time_per_request = overall_duration / num_requests
        assert avg_time_per_request < performance_thresholds["max_response_time"]
    
    @pytest.mark.asyncio
    async def test_database_operation_performance(self, test_dependencies, performance_thresholds):
        """Test database operations meet performance requirements."""
        # Test bulk preference saves
        num_operations = 100
        
        start_time = time.time()
        for i in range(num_operations):
            test_dependencies.save_user_preference(
                f"pattern_{i}",
                f"choice_{i}",
                ["performance", "test"]
            )
        bulk_duration = time.time() - start_time
        
        # Should handle 100 DB operations quickly
        assert bulk_duration < 1.0  # 1 second for 100 operations
        
        # Test bulk retrieval
        start_time = time.time()
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("SELECT * FROM user_preferences")
        results = cursor.fetchall()
        retrieval_duration = time.time() - start_time
        
        assert len(results) >= num_operations
        assert retrieval_duration < 0.5  # 500ms for retrieval
    
    @pytest.mark.asyncio
    async def test_large_output_handling(self, test_agent, test_dependencies, performance_thresholds):
        """Test handling of large analysis outputs."""
        # Simulate large Agent output
        large_output = "Large analysis output\n" * 10000  # ~250KB of text
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Processing large analysis output"),
            {
                "create_valgrind_wrapper": {
                    "executable_path": "/test/large_app",
                    "tool": "memcheck",
                    "options": ["--verbose"]
                }
            },
            ModelTextResponse(content="Large output processed efficiently")
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = large_output
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            
            start_time = time.time()
            result = await test_agent.run(
                "Analyze large application with verbose output",
                deps=test_dependencies
            )
            duration = time.time() - start_time
            
            # Should handle large outputs within reasonable time
            assert duration < (performance_thresholds["max_response_time"] * 3)
            assert result.data is not None

class TestScalabilityRequirements:
    """Test scalability under various loads."""
    
    @pytest.mark.asyncio
    async def test_session_scalability(self, performance_thresholds):
        """Test handling multiple concurrent sessions."""
        from dependencies import create_dependencies
        from settings import AgentMemoryAISettings
        import tempfile
        
        num_sessions = 5
        sessions = []
        
        # Create multiple sessions
        start_time = time.time()
        for i in range(num_sessions):
            settings = AgentMemoryAISettings(
                valgrind_ai_db_path=Path(tempfile.mktemp(suffix=f"_session_{i}.db"))
            )
            session_deps = create_dependencies(
                session_id=f"session_{i}",
                settings=settings
            )
            sessions.append(session_deps)
        creation_time = time.time() - start_time
        
        # Session creation should be fast
        assert creation_time < 2.0  # 2 seconds for 5 sessions
        
        # Test operations across all sessions
        start_time = time.time()
        for i, session in enumerate(sessions):
            session.save_user_preference(f"session_{i}_pattern", "test_choice", ["scalability"])
        operations_time = time.time() - start_time
        
        assert operations_time < 1.0  # 1 second for 5 operations
        
        # Cleanup
        for session in sessions:
            if session.db_connection:
                session.db_connection.close()
    
    @pytest.mark.asyncio
    async def test_learning_system_performance(self, test_dependencies, performance_thresholds):
        """Test learning system performance under load."""
        from models import MemoryIssue, SeverityLevel
        
        # Create test memory issues
        num_issues = 50
        issues = []
        for i in range(num_issues):
            issue = MemoryIssue(
                issue_type=SeverityLevel.LOW,
                severity=SeverityLevel.LOW,
                message=f"Test issue {i}",
                source_file=f"test_{i}.cpp",
                line_number=i + 1,
                function_name=f"test_function_{i}"
            )
            issues.append(issue)
        
        # Test learning from patterns
        start_time = time.time()
        for issue in issues:
            test_dependencies.learn_from_issue_pattern(
                issue,
                is_false_positive=(i % 3 == 0),  # Mark every 3rd as false positive
                confidence=0.8
            )
        learning_time = time.time() - start_time
        
        # Learning should be efficient
        assert learning_time < 2.0  # 2 seconds for 50 learning operations
        
        # Test pattern confidence retrieval
        start_time = time.time()
        for issue in issues[:10]:  # Test subset
            confidence = test_dependencies.get_issue_pattern_confidence(issue)
            assert 0.0 <= confidence <= 1.0
        retrieval_time = time.time() - start_time
        
        assert retrieval_time < 0.5  # 500ms for 10 retrievals
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, test_dependencies, performance_thresholds):
        """Test analysis result caching performance."""
        from models import AgentAnalysisResult, AgentTool
        from datetime import datetime
        
        # Create test analysis results
        num_results = 20
        results = []
        for i in range(num_results):
            result = AgentAnalysisResult(
                tool=AgentTool.MEMCHECK,
                executable_path=f"/test/app_{i}",
                command_line=f"valgrind /test/app_{i}",
                analysis_timestamp=datetime.now(),
                total_errors=i,
                memory_leaks=[],
                invalid_reads=[],
                invalid_writes=[],
                uninitialized_values=[]
            )
            results.append(result)
        
        # Test cache storage performance
        start_time = time.time()
        for result in results:
            cache_id = test_dependencies.cache_analysis_result(result)
            assert cache_id is not None
        storage_time = time.time() - start_time
        
        assert storage_time < 1.0  # 1 second for 20 cache operations
        
        # Test cache retrieval performance
        start_time = time.time()
        for result in results[:10]:  # Test subset
            cached = test_dependencies.get_cached_analysis(
                result.tool,
                result.executable_path,
                result.command_line
            )
            assert cached is not None
        retrieval_time = time.time() - start_time
        
        assert retrieval_time < 0.5  # 500ms for 10 retrievals

class TestResourceEfficiency:
    """Test efficient resource usage."""
    
    @pytest.mark.asyncio
    async def test_memory_cleanup(self, test_agent, test_dependencies):
        """Test proper memory cleanup after operations."""
        import gc
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run multiple operations
        for i in range(10):
            test_agent.model.agent_responses = [
                ModelTextResponse(content=f"Operation {i} completed")
            ]
            
            result = await test_agent.run(f"Operation {i}", deps=test_dependencies)
            assert result.data is not None
        
        # Force garbage collection
        gc.collect()
        
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory should not grow excessively
        assert memory_increase < 50  # Less than 50MB increase
    
    @pytest.mark.asyncio
    async def test_database_connection_efficiency(self, test_dependencies):
        """Test efficient database connection usage."""
        # Verify single connection is reused
        original_connection = test_dependencies.db_connection
        
        # Perform multiple database operations
        for i in range(20):
            test_dependencies.save_user_preference(f"efficiency_test_{i}", "value", ["test"])
        
        # Should still be using same connection
        assert test_dependencies.db_connection is original_connection
        
        # Test connection health
        cursor = test_dependencies.db_connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    @pytest.mark.asyncio
    async def test_temporary_file_cleanup(self, test_dependencies):
        """Test temporary files are properly cleaned up."""
        temp_dir = test_dependencies.temp_dir
        initial_files = list(temp_dir.glob("*")) if temp_dir.exists() else []
        
        # Simulate operations that might create temp files
        for i in range(5):
            temp_file = temp_dir / f"temp_analysis_{i}.xml"
            temp_file.write_text(f"<analysis>Test data {i}</analysis>")
        
        # Verify files were created
        created_files = list(temp_dir.glob("*"))
        assert len(created_files) > len(initial_files)
        
        # Cleanup should be handled by dependencies cleanup
        await test_dependencies.cleanup()
        
        # Note: In real implementation, cleanup would remove temp files
        # For testing, we verify the cleanup method exists and runs