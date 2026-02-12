"""Performance validation tests for the Clang-Tidy AI Agent."""

import pytest
import pytest_asyncio
import time
import asyncio
import os
import sys
import tempfile
import concurrent.futures
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'core'))

from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel

try:
    from agent import clang_tidy_agent, ClangTidyAI
    from dependencies import ClangTidyDependencies, create_dependencies
    from settings import ClangTidyAISettings
    from models import Warning, ClangTidyAnalysis
    from tools import analyze_code_with_clang_tidy, batch_analyze_project
except ImportError:
    # Fallback for testing without full setup
    clang_tidy_agent = None
    ClangTidyAI = None
    ClangTidyDependencies = None
    create_dependencies = None
    ClangTidyAISettings = None
    Warning = None
    ClangTidyAnalysis = None
    analyze_code_with_clang_tidy = None
    batch_analyze_project = None


class TestResponseTime:
    """Test response time requirements."""
    
    @pytest.mark.asyncio
    async def test_interactive_response_time_single_query(self, test_dependencies):
        """Test that interactive responses complete within 3 seconds."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        start_time = time.time()
        
        result = await test_agent.run(
            "Explain the readability-identifier-naming warning",
            deps=test_dependencies
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Should complete within 3 seconds as per requirements
        assert response_time < 3.0, f"Response time {response_time:.2f}s exceeds 3s limit"
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_file_analysis_response_time(self, test_dependencies, sample_cpp_file):
        """Test file analysis response time."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="test warning", returncode=0)
            
            start_time = time.time()
            
            result = await test_agent.run(
                f"Analyze the file {sample_cpp_file}",
                deps=test_dependencies
            )
            
            end_time = time.time()
            response_time = end_time - start_time
            
            # File analysis should complete within 5 seconds
            assert response_time < 5.0, f"File analysis time {response_time:.2f}s exceeds 5s limit"
            assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, test_dependencies):
        """Test handling of concurrent requests."""
        test_agent = clang_tidy_agent.override(model=TestModel())
        
        async def single_request(request_id):
            start_time = time.time()
            result = await test_agent.run(
                f"Explain warning {request_id}",
                deps=test_dependencies
            )
            end_time = time.time()
            return end_time - start_time, result
        
        # Launch 5 concurrent requests
        start_time = time.time()
        tasks = [single_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All requests should complete
        assert len(results) == 5
        for response_time, result in results:
            assert result.data is not None
            assert response_time < 3.0  # Each individual request under 3s
        
        # Total time should be reasonable (concurrent processing)
        assert total_time < 8.0  # Should not be 5 * 3s due to concurrency
    
    @pytest.mark.asyncio
    async def test_large_file_analysis_timeout(self, test_dependencies):
        """Test that large file analysis respects timeout limits."""
        # Create a large C++ file
        large_content = """
#include <iostream>
#include <vector>
#include <string>

class LargeClass {
public:
""" + "\n".join([f"    int member{i};" for i in range(1000)]) + """
    
    void processData() {
""" + "\n".join([f"        member{i} = {i};" for i in range(1000)]) + """
    }
};

int main() {
    LargeClass obj;
    obj.processData();
    return 0;
}
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write(large_content)
            large_file_path = f.name
        
        try:
            class MockContext:
                def __init__(self, deps):
                    self.deps = deps
            
            context = MockContext(test_dependencies)
            
            with patch('subprocess.run') as mock_run:
                # Simulate slow clang-tidy execution
                def slow_run(*args, **kwargs):
                    time.sleep(1)  # Simulate some processing time
                    return Mock(stdout="", stderr="large file warnings", returncode=0)
                
                mock_run.side_effect = slow_run
                
                start_time = time.time()
                result = await analyze_code_with_clang_tidy(context, large_file_path)
                end_time = time.time()
                
                # Should complete within timeout
                processing_time = end_time - start_time
                assert processing_time < test_dependencies.settings.max_analysis_time_seconds
                assert isinstance(result, ClangTidyAnalysis)
                
        finally:
            os.unlink(large_file_path)


class TestThroughput:
    """Test throughput requirements."""
    
    @pytest.mark.asyncio
    async def test_batch_analysis_throughput(self, integration_test_project, test_dependencies):
        """Test batch analysis of 100+ files."""
        # Create 100 small C++ files
        src_dir = integration_test_project / "src" / "batch_test"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        file_paths = []
        for i in range(100):
            cpp_file = src_dir / f"test_{i:03d}.cpp"
            cpp_file.write_text(f"""
#include <iostream>
int main() {{
    int var{i} = {i};  // naming issue
    std::cout << var{i} << std::endl;  // performance issue
    return 0;
}}
""")
            file_paths.append(cpp_file)
        
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="batch warnings", returncode=0)
            
            start_time = time.time()
            result = await batch_analyze_project(context, str(src_dir) + "/**/*.cpp")
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Should process 100 files in reasonable time (< 30 seconds)
            assert processing_time < 30.0, f"Batch processing took {processing_time:.2f}s, exceeds 30s limit"
            assert result.total_files_analyzed >= 100
            
            # Calculate throughput
            throughput = result.total_files_analyzed / processing_time
            assert throughput >= 3.0  # At least 3 files per second
    
    @pytest.mark.asyncio
    async def test_concurrent_session_handling(self, temp_dir):
        """Test handling multiple concurrent user sessions."""
        
        async def simulate_user_session(session_id, query_count=10):
            """Simulate a user session with multiple queries."""
            deps = create_dependencies(f"session-{session_id}")
            try:
                agent = clang_tidy_agent.override(model=TestModel())
                
                results = []
                for i in range(query_count):
                    result = await agent.run(f"Query {i} from session {session_id}", deps=deps)
                    results.append(result)
                
                return len([r for r in results if r.data is not None])
            finally:
                deps.db_connection.close()
        
        # Simulate 10 concurrent user sessions
        start_time = time.time()
        tasks = [simulate_user_session(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # All sessions should complete successfully
        assert len(results) == 10
        for successful_queries in results:
            assert successful_queries == 10  # All queries in each session succeeded
        
        # Should handle concurrent load efficiently
        assert total_time < 15.0  # All sessions complete within 15 seconds
    
    def test_memory_usage_under_load(self, test_dependencies):
        """Test memory usage during high load operations."""
        import psutil
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)  # MB
        
        # Simulate high load scenario
        large_analysis_results = []
        
        for i in range(100):
            # Create large analysis result objects
            warnings = [
                Warning(
                    line_number=j,
                    column_number=10,
                    rule_id=f"rule-{j}",
                    severity="warning",
                    message=f"Test warning {j} in iteration {i}",
                    suggested_fix=f"Fix for warning {j}",
                    context_lines=[f"Line {j+k}" for k in range(-2, 3)]
                )
                for j in range(50)  # 50 warnings per analysis
            ]
            
            analysis = ClangTidyAnalysis(
                file_path=f"test_{i}.cpp",
                warnings=warnings,
                total_warnings=len(warnings),
                clang_tidy_version="test-version"
            )
            
            large_analysis_results.append(analysis)
        
        peak_memory = process.memory_info().rss / (1024 * 1024)  # MB
        memory_increase = peak_memory - initial_memory
        
        # Should not exceed 500MB additional overhead as per requirements
        assert memory_increase < 500, f"Memory increase {memory_increase:.1f}MB exceeds 500MB limit"
        
        # Cleanup
        del large_analysis_results


class TestCachingPerformance:
    """Test caching system performance."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, test_dependencies, sample_cpp_file):
        """Test that cache hits provide significant performance improvement."""
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            # First call - cache miss, should call clang-tidy
            mock_run.return_value = Mock(stdout="", stderr="cached warnings", returncode=0)
            
            start_time = time.time()
            result1 = await analyze_code_with_clang_tidy(
                context,
                str(sample_cpp_file.relative_to(test_dependencies.settings.project_root))
            )
            first_call_time = time.time() - start_time
            
            # Second call - cache hit, should be much faster
            start_time = time.time()
            result2 = await analyze_code_with_clang_tidy(
                context,
                str(sample_cpp_file.relative_to(test_dependencies.settings.project_root))
            )
            second_call_time = time.time() - start_time
            
            # Both should return valid results
            assert isinstance(result1, ClangTidyAnalysis)
            assert isinstance(result2, ClangTidyAnalysis)
            
            # Cache hit should be significantly faster (at least 5x)
            if first_call_time > 0.01:  # Only test if first call was measurably slow
                assert second_call_time < first_call_time / 5, \
                    f"Cache hit ({second_call_time:.3f}s) not significantly faster than miss ({first_call_time:.3f}s)"
    
    def test_cache_size_limits(self, test_dependencies):
        """Test that cache respects size limits."""
        from tools import _cache_analysis, _get_cache_size, _cleanup_old_cache_entries
        
        # Fill cache with many entries
        for i in range(1000):
            analysis = ClangTidyAnalysis(
                file_path=f"test_{i}.cpp",
                warnings=[],
                total_warnings=0,
                clang_tidy_version="test-version"
            )
            
            _cache_analysis(
                test_dependencies.db_connection,
                f"test_{i}.cpp",
                f"hash_{i:04d}",
                analysis
            )
        
        cache_size = _get_cache_size(test_dependencies.db_connection)
        
        # Should respect reasonable cache size limits
        max_cache_entries = 500  # Configurable limit
        if cache_size > max_cache_entries:
            _cleanup_old_cache_entries(test_dependencies.db_connection, max_cache_entries)
            
            new_cache_size = _get_cache_size(test_dependencies.db_connection)
            assert new_cache_size <= max_cache_entries
    
    @pytest.mark.asyncio
    async def test_cache_invalidation_performance(self, test_dependencies, sample_cpp_file):
        """Test performance of cache invalidation."""
        from tools import _invalidate_file_cache
        
        # Cache an analysis result
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
        
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(stdout="", stderr="", returncode=0)
            
            # Cache the result
            await analyze_code_with_clang_tidy(
                context,
                str(sample_cpp_file.relative_to(test_dependencies.settings.project_root))
            )
            
            # Modify file to trigger cache invalidation
            sample_cpp_file.write_text(sample_cpp_file.read_text() + "\n// Modified")
            
            # Invalidation should be fast
            start_time = time.time()
            _invalidate_file_cache(
                test_dependencies.db_connection,
                str(sample_cpp_file.relative_to(test_dependencies.settings.project_root))
            )
            invalidation_time = time.time() - start_time
            
            # Should complete very quickly
            assert invalidation_time < 0.1, f"Cache invalidation took {invalidation_time:.3f}s, too slow"


class TestScalability:
    """Test scalability characteristics."""
    
    @pytest.mark.asyncio
    async def test_large_project_analysis(self, temp_dir, test_dependencies):
        """Test analysis of large project (1000+ files)."""
        # Create a large project structure
        project_root = temp_dir / "large_project"
        
        # Create nested directory structure
        for module in range(10):  # 10 modules
            module_dir = project_root / f"module_{module}" / "src"
            module_dir.mkdir(parents=True, exist_ok=True)
            
            for file_num in range(100):  # 100 files per module = 1000 total
                cpp_file = module_dir / f"file_{file_num:03d}.cpp"
                cpp_file.write_text(f"""
#include <iostream>
#include <vector>

namespace module_{module} {{
    class File{file_num}Class {{
    private:
        int member_var_{file_num};  // naming issue
        std::vector<int> data_vec;
        
    public:
        File{file_num}Class() : member_var_{file_num}(0) {{}}
        
        void process_data() {{
            for (int i = 0; i < 100; ++i) {{
                data_vec.push_back(i);
                std::cout << i << std::endl;  // performance issue
            }}
        }}
    }};
}}

int main() {{
    module_{module}::File{file_num}Class obj;
    obj.process_data();
    return 0;
}}
""")
        
        class MockContext:
            def __init__(self, deps):
                self.deps = deps
                
        context = MockContext(test_dependencies)
        
        with patch('subprocess.run') as mock_run:
            # Simulate fast clang-tidy responses
            mock_run.return_value = Mock(stdout="", stderr="simulated warnings", returncode=0)
            
            start_time = time.time()
            
            # Analyze entire large project
            result = await batch_analyze_project(context, str(project_root / "**" / "*.cpp"))
            
            analysis_time = time.time() - start_time
            
            # Should handle large project within reasonable time
            assert analysis_time < 60.0, f"Large project analysis took {analysis_time:.1f}s, exceeds 60s limit"
            assert result.total_files_analyzed >= 1000
            
            # Calculate scalability metrics
            files_per_second = result.total_files_analyzed / analysis_time
            assert files_per_second >= 10.0, f"Processing rate {files_per_second:.1f} files/s too slow"
    
    def test_database_scalability(self, test_dependencies):
        """Test database performance with large amounts of data."""
        from dependencies import save_user_preference, load_user_preferences
        
        # Insert large number of preferences
        start_time = time.time()
        
        for session in range(100):  # 100 sessions
            for rule in range(20):  # 20 rules per session = 2000 total
                save_user_preference(
                    test_dependencies.db_connection,
                    f"session-{session}",
                    f"rule-{rule}",
                    f"strategy-{rule % 5}",  # 5 different strategies
                    [f"tag-{rule % 3}"]  # 3 different tags
                )
        
        insert_time = time.time() - start_time
        
        # Inserts should complete reasonably quickly
        assert insert_time < 5.0, f"Bulk inserts took {insert_time:.2f}s, too slow"
        
        # Test query performance with large dataset
        start_time = time.time()
        
        for session in range(0, 100, 10):  # Test every 10th session
            preferences = load_user_preferences(test_dependencies.db_connection, f"session-{session}")
            assert len(preferences) == 20  # Should load all preferences for session
        
        query_time = time.time() - start_time
        
        # Queries should remain fast even with large dataset
        assert query_time < 2.0, f"Bulk queries took {query_time:.2f}s, too slow"
    
    def test_concurrent_database_access(self, temp_dir):
        """Test concurrent database access performance."""
        import threading
        import sqlite3
        
        db_path = temp_dir / "concurrent_test.db" 
        
        # Initialize database
        connection = sqlite3.connect(str(db_path))
        connection.executescript("""
            CREATE TABLE test_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        connection.close()
        
        def worker_thread(thread_id, iterations=100):
            """Worker thread that performs database operations."""
            thread_connection = sqlite3.connect(str(db_path))
            
            try:
                for i in range(iterations):
                    # Insert data
                    thread_connection.execute(
                        "INSERT INTO test_preferences (session_id, data) VALUES (?, ?)",
                        (f"thread-{thread_id}", f"data-{i}")
                    )
                    thread_connection.commit()
                    
                    # Read data
                    cursor = thread_connection.execute(
                        "SELECT COUNT(*) FROM test_preferences WHERE session_id = ?",
                        (f"thread-{thread_id}",)
                    )
                    count = cursor.fetchone()[0]
                    assert count == i + 1
                    
            finally:
                thread_connection.close()
        
        # Run multiple threads concurrently
        threads = []
        start_time = time.time()
        
        for thread_id in range(5):  # 5 concurrent threads
            thread = threading.Thread(target=worker_thread, args=(thread_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # Should handle concurrent access efficiently
        assert total_time < 10.0, f"Concurrent database access took {total_time:.2f}s, too slow"
        
        # Verify all data was inserted correctly
        final_connection = sqlite3.connect(str(db_path))
        try:
            cursor = final_connection.execute("SELECT COUNT(*) FROM test_preferences")
            total_records = cursor.fetchone()[0]
            assert total_records == 500  # 5 threads * 100 iterations each
        finally:
            final_connection.close()


class TestResourceUsage:
    """Test resource usage characteristics."""
    
    def test_file_descriptor_management(self, test_dependencies):
        """Test that file descriptors are properly managed."""
        import psutil
        
        process = psutil.Process()
        initial_fds = process.num_fds()
        
        # Perform many file operations
        temp_files = []
        try:
            for i in range(100):
                with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
                    f.write(f"// Test file {i}")
                    temp_files.append(f.name)
                
                # Read the file
                with open(temp_files[-1], 'r') as f:
                    content = f.read()
                    assert f"Test file {i}" in content
            
            # File descriptors should not accumulate
            current_fds = process.num_fds()
            fd_increase = current_fds - initial_fds
            
            # Should not leak file descriptors
            assert fd_increase < 10, f"File descriptor increase {fd_increase} suggests leaks"
            
        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except OSError:
                    pass
    
    def test_database_connection_pooling(self, temp_dir):
        """Test database connection efficiency."""
        from dependencies import create_dependencies
        
        # Create multiple dependencies instances (simulating sessions)
        dependencies_list = []
        
        try:
            start_time = time.time()
            
            for i in range(50):
                deps = create_dependencies(f"pool-test-{i}")
                dependencies_list.append(deps)
                
                # Perform a quick database operation
                cursor = deps.db_connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                assert result[0] == 1
            
            creation_time = time.time() - start_time
            
            # Should create connections efficiently
            assert creation_time < 2.0, f"Creating 50 connections took {creation_time:.2f}s, too slow"
            
        finally:
            # Cleanup all connections
            for deps in dependencies_list:
                deps.db_connection.close()
    
    @pytest.mark.asyncio
    async def test_async_resource_cleanup(self, test_dependencies):
        """Test that async resources are properly cleaned up."""
        import gc
        import weakref
        
        # Create AI agents and track them with weak references
        agent_refs = []
        
        for i in range(10):
            ai = ClangTidyAI(session_id=f"cleanup-test-{i}")
            agent_refs.append(weakref.ref(ai))
            
            # Use the agent briefly
            async with ai:
                result = await ai.chat("test query")
                assert result is not None
        
        # Force garbage collection
        gc.collect()
        
        # All agent references should be cleaned up
        active_refs = [ref for ref in agent_refs if ref() is not None]
        assert len(active_refs) == 0, f"{len(active_refs)} agent references not cleaned up"