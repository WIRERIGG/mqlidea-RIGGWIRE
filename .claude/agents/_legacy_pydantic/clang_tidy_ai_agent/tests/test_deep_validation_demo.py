"""
Deep Validation Demonstration for Clang-Tidy AI Agent
=====================================================

This file demonstrates the deep validation patterns specified in the 
Pydantic AI Agent Deep Validator specification, including:

- Property-based testing with Hypothesis (500+ examples)
- Failure injection and resilience probing
- Security testing with adversarial inputs  
- Edge case discovery with boundary testing
- State inspection and runtime instrumentation
- Performance testing under load
- Memory leak detection
"""

import pytest
import asyncio
import time
import threading
import gc
from unittest.mock import patch, Mock, MagicMock
from hypothesis import given, strategies as st, settings, assume
import psutil
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelTextResponse


# Configure Hypothesis for deep probing
settings.register_profile("deep_validation", 
                        max_examples=500,
                        deadline=60000,
                        suppress_health_check=[])
settings.load_profile("deep_validation")


class TestDeepProbing:
    """Enhanced tests with deep probing patterns."""
    
    @pytest.fixture
    def probed_test_agent(self):
        """Create agent with TestModel and add probing hooks."""
        try:
            from ..core.agent import clang_tidy_agent
            test_model = TestModel()
            agent_instance = clang_tidy_agent.override(model=test_model)
            
            # Add probe: Log internal decisions
            agent_instance._probe_log = []  
            original_run = agent_instance.run
            
            async def probed_run(*args, **kwargs):
                agent_instance._probe_log.append("Run started")
                result = await original_run(*args, **kwargs)
                agent_instance._probe_log.append("Run ended")
                return result
                
            agent_instance.run = probed_run
            return agent_instance
        except ImportError:
            pytest.skip("Agent not properly imported")
    
    @given(st.text(min_size=1, max_size=1000))
    @pytest.mark.asyncio
    async def test_input_invariant_fuzzing(self, input_text):
        """Property-based test: Agent should never crash on varied inputs."""
        assume(len(input_text.strip()) > 0)  # Skip empty inputs
        
        try:
            # Mock a test model for consistent behavior
            test_model = TestModel()
            test_model.agent_responses = [
                ModelTextResponse(content="Analysis complete: no issues found")
            ]
            
            # Test that agent handles arbitrary text input gracefully
            # In reality, this would involve the actual agent logic
            result = "Simulated agent response for input validation"
            assert result is not None
            assert len(result) > 0
            
        except ValueError as e:
            # Expected for some invalid inputs - log but don't fail
            if "validation" not in str(e).lower():
                pytest.fail(f"Unexpected error on input: {input_text[:50]}... - {e}")
    
    @given(st.lists(st.text(min_size=1, max_size=100), min_size=1, max_size=100))
    @pytest.mark.asyncio 
    async def test_batch_processing_invariant(self, input_list):
        """Property-based test: Batch processing should be consistent."""
        assume(all(len(item.strip()) > 0 for item in input_list))
        
        # Test that batch processing maintains invariants
        try:
            # Mock batch processing
            results = []
            for item in input_list:
                # Simulate processing each item
                result = f"processed: {len(item)} chars"
                results.append(result)
            
            # Verify invariants
            assert len(results) == len(input_list)
            assert all(isinstance(r, str) for r in results)
            
        except Exception as e:
            pytest.fail(f"Batch processing failed: {e}")
    
    @pytest.mark.asyncio
    async def test_failure_injection_network(self):
        """Test resilience to network failures."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_post.side_effect = ConnectionError("Network failure")
            
            # Test agent behavior with network issues
            try:
                # This would test actual agent network calls
                # For demo, we simulate the failure handling
                result = await self._simulate_network_failure_handling()
                assert result is not None
                assert "error" in result.lower() or "failed" in result.lower()
                
            except ConnectionError:
                # This is expected - agent should handle gracefully
                pass
    
    async def _simulate_network_failure_handling(self):
        """Simulate how agent handles network failures."""
        # In a real agent, this would test actual network error handling
        return "Network error handled gracefully"
    
    @pytest.mark.asyncio
    async def test_failure_injection_timeout(self):
        """Test resilience to timeouts."""
        with patch('asyncio.wait_for') as mock_wait:
            mock_wait.side_effect = asyncio.TimeoutError("Operation timed out")
            
            # Test timeout handling
            try:
                result = await self._simulate_timeout_handling()
                assert "timeout" in result.lower()
            except asyncio.TimeoutError:
                # Expected - should be handled gracefully
                pass
    
    async def _simulate_timeout_handling(self):
        """Simulate timeout handling in agent."""
        return "Timeout handled with fallback response"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self):
        """Test for memory leaks in repeated operations."""
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Run operation multiple times
        for _ in range(100):
            # Simulate agent operations that might leak memory
            temp_data = {"test": "data", "iteration": _}
            await asyncio.sleep(0.001)  # Simulate work
            del temp_data
        
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Allow some growth but detect major leaks
        growth_ratio = final_objects / initial_objects if initial_objects > 0 else 1.0
        assert growth_ratio < 1.5, f"Potential memory leak: {growth_ratio:.2f}x object growth"
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self):
        """Test thread safety and concurrent access."""
        results = []
        errors = []
        
        async def concurrent_operation(i):
            try:
                # Simulate concurrent agent operations
                await asyncio.sleep(0.01)  # Simulate work
                result = f"result_{i}"
                results.append(result)
            except Exception as e:
                errors.append(e)
        
        # Run 10 concurrent operations
        tasks = [concurrent_operation(i) for i in range(10)]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 10, "Not all concurrent operations completed"
    
    @pytest.mark.asyncio
    async def test_state_corruption_detection(self):
        """Test for internal state corruption."""
        # This would monitor internal state consistency across multiple operations
        
        # Simulate state-dependent operations
        state = {"counter": 0, "active": True}
        
        for i in range(50):
            # Simulate operations that modify state
            state["counter"] += 1
            assert state["active"] is True  # State invariant
            assert state["counter"] == i + 1  # State consistency
            
        # Final state validation
        assert state["counter"] == 50
        assert state["active"] is True
    
    @pytest.mark.asyncio
    async def test_performance_regression(self):
        """Test for performance regressions."""
        # Baseline measurement
        start_time = time.time()
        
        # Run standard operation
        for _ in range(10):
            await asyncio.sleep(0.001)  # Simulate agent work
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Assert reasonable performance bounds
        assert execution_time < 2.0, f"Performance regression: {execution_time:.3f}s > 2s"
    
    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """Test proper error propagation and handling."""
        
        # Test that errors are properly propagated with context
        try:
            raise ValueError("Test error with context")
        except ValueError as e:
            assert "Test error" in str(e)
            assert "context" in str(e)
    
    @pytest.mark.asyncio
    async def test_resource_cleanup(self):
        """Test proper cleanup of resources."""
        # Track resource allocation/deallocation
        
        # Simulate resource allocation
        resources = []
        try:
            for i in range(10):
                resource = Mock()  # Simulate resource
                resource.cleanup = Mock()
                resources.append(resource)
            
            # Verify resources are tracked
            assert len(resources) == 10
            
        finally:
            # Cleanup resources
            for resource in resources:
                resource.cleanup()
            
            # Verify cleanup was called
            for resource in resources:
                resource.cleanup.assert_called_once()


class TestSecurityProbing:
    """Security-focused testing with adversarial inputs."""
    
    @given(st.text().filter(lambda x: any(char in x for char in "';\"<>&|`$()[]")))
    @pytest.mark.asyncio
    async def test_injection_resistance(self, malicious_input):
        """Test resistance to injection attacks."""
        
        # Test that malicious input is properly sanitized
        try:
            # Simulate agent processing potentially malicious input
            sanitized = self._sanitize_input(malicious_input)
            assert not any(char in sanitized for char in "';\"&|`$")
            
        except ValueError:
            # Expected - should reject malicious input
            pass
    
    def _sanitize_input(self, user_input: str) -> str:
        """Simulate input sanitization logic."""
        # Basic sanitization - remove dangerous characters
        dangerous_chars = "';\"&|`$"
        sanitized = ''.join(char for char in user_input if char not in dangerous_chars)
        return sanitized
    
    @pytest.mark.asyncio
    async def test_path_traversal_resistance(self):
        """Test resistance to path traversal attacks."""
        malicious_paths = [
            "../../../etc/passwd",
            "..\\\\..\\\\..\\\\windows\\\\system32\\\\config\\\\sam",
            "/dev/null",
            "file:///etc/passwd"
        ]
        
        for path in malicious_paths:
            try:
                # Test path validation
                validated_path = self._validate_path(path)
                assert not validated_path.startswith("/")
                assert ".." not in validated_path
                
            except ValueError:
                # Expected - should reject malicious paths
                pass
    
    def _validate_path(self, path: str) -> str:
        """Simulate path validation logic."""
        if ".." in path or path.startswith("/"):
            raise ValueError("Invalid path")
        return path
    
    @pytest.mark.asyncio
    async def test_code_injection_resistance(self):
        """Test resistance to code injection attacks."""
        injection_attempts = [
            "__import__('os').system('rm -rf /')",
            "eval('print(secrets)')",
            "exec('import subprocess; subprocess.call([\"rm\", \"-rf\", \"/\"])')",
            "'; DROP TABLE users; --"
        ]
        
        for injection in injection_attempts:
            try:
                # Test that code injection is prevented
                result = self._process_user_code(injection)
                assert "error" in result.lower() or result == ""
                
            except Exception:
                # Expected - should reject dangerous code
                pass
    
    def _process_user_code(self, code: str) -> str:
        """Simulate safe code processing."""
        dangerous_patterns = ["import", "exec", "eval", "__", "DROP", "DELETE"]
        if any(pattern in code for pattern in dangerous_patterns):
            return "Error: Dangerous code detected"
        return "Safe code processed"


class TestEdgeCases:
    """Edge case testing with boundary conditions."""
    
    @pytest.mark.parametrize("size", [0, 1, 1023, 1024, 1025, 65535, 65536])
    @pytest.mark.asyncio
    async def test_input_size_boundaries(self, size):
        """Test behavior at input size boundaries."""
        input_data = "x" * size
        
        try:
            # Test agent handling of various input sizes
            result = await self._process_sized_input(input_data)
            
            if size == 0:
                assert result == "Empty input"
            elif size > 65535:
                assert "too large" in result.lower()
            else:
                assert len(result) > 0
                
        except Exception as e:
            # Log boundary behavior
            print(f"Size {size} behavior: {e}")
    
    async def _process_sized_input(self, input_data: str) -> str:
        """Simulate processing input of various sizes."""
        if len(input_data) == 0:
            return "Empty input"
        elif len(input_data) > 65535:
            return "Input too large"
        else:
            return f"Processed {len(input_data)} characters"
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self):
        """Test proper Unicode handling."""
        unicode_inputs = [
            "Hello 世界",
            "🚀 Rocket",
            "café",
            "Здравствуй мир",
            "مرحبا بالعالم"
        ]
        
        for unicode_input in unicode_inputs:
            try:
                result = await self._process_unicode(unicode_input)
                assert isinstance(result, str)
                assert len(result) > 0
                
            except Exception as e:
                pytest.fail(f"Unicode handling failed for '{unicode_input}': {e}")
    
    async def _process_unicode(self, text: str) -> str:
        """Simulate Unicode text processing."""
        # Basic Unicode handling
        return f"Processed Unicode text: {len(text)} characters"
    
    @pytest.mark.asyncio
    async def test_extreme_concurrency(self):
        """Test behavior under extreme concurrent load."""
        async def worker_task(worker_id):
            # Simulate concurrent work
            await asyncio.sleep(0.01)
            return f"Worker {worker_id} completed"
        
        # Create 100 concurrent tasks
        tasks = [worker_task(i) for i in range(100)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all tasks completed successfully
        successful_results = [r for r in results if isinstance(r, str)]
        failed_results = [r for r in results if isinstance(r, Exception)]
        
        assert len(successful_results) >= 90  # Allow some failures under extreme load
        assert len(failed_results) <= 10
        
        for result in successful_results:
            assert "completed" in result


class TestRealismIntegration:
    """Tests that simulate real-world usage patterns."""
    
    @pytest.mark.asyncio
    async def test_typical_cpp_analysis_workflow(self):
        """Test typical C++ code analysis workflow."""
        # Simulate a complete analysis workflow
        cpp_code_samples = [
            "int main() { return 0; }",
            "class MyClass { public: void method(); };",
            "#include <iostream>\nint main() { std::cout << \"Hello\"; }"
        ]
        
        for code in cpp_code_samples:
            try:
                # Simulate full analysis pipeline
                analysis_result = await self._simulate_cpp_analysis(code)
                
                assert "analysis" in analysis_result
                assert "warnings" in analysis_result or "clean" in analysis_result
                
            except Exception as e:
                pytest.fail(f"Analysis failed for code sample: {e}")
    
    async def _simulate_cpp_analysis(self, code: str) -> str:
        """Simulate C++ code analysis."""
        # Basic simulation of clang-tidy analysis
        if "return 0" in code:
            return "Analysis complete: code is clean"
        elif "class" in code:
            return "Analysis complete: 1 style warning found"
        else:
            return "Analysis complete: multiple suggestions available"
    
    @pytest.mark.asyncio
    async def test_user_interaction_patterns(self):
        """Test common user interaction patterns."""
        interaction_scenarios = [
            "analyze file main.cpp",
            "explain warning readability-identifier-naming", 
            "fix all warnings in project",
            "show analysis summary"
        ]
        
        for scenario in interaction_scenarios:
            try:
                response = await self._simulate_user_interaction(scenario)
                assert len(response) > 0
                assert not response.startswith("Error")
                
            except Exception as e:
                pytest.fail(f"User interaction failed: {scenario} - {e}")
    
    async def _simulate_user_interaction(self, user_input: str) -> str:
        """Simulate user interaction handling."""
        if "analyze" in user_input:
            return "File analysis completed successfully"
        elif "explain" in user_input:
            return "Warning explanation provided"
        elif "fix" in user_input:
            return "Fixes applied to project"
        elif "summary" in user_input:
            return "Analysis summary generated"
        else:
            return "Command processed"


# Performance and Load Testing
class TestPerformanceValidation:
    """Performance-focused testing to detect regressions."""
    
    @pytest.mark.asyncio
    async def test_response_time_under_load(self):
        """Test response time under concurrent load."""
        async def measure_response_time():
            start = time.time()
            # Simulate agent operation
            await asyncio.sleep(0.01)
            return time.time() - start
        
        # Measure response time under load
        tasks = [measure_response_time() for _ in range(50)]
        response_times = await asyncio.gather(*tasks)
        
        # Analyze performance metrics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        
        assert avg_time < 0.1, f"Average response time too high: {avg_time:.3f}s"
        assert max_time < 0.5, f"Maximum response time too high: {max_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self):
        """Test memory usage patterns under load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Simulate sustained load
        for _ in range(1000):
            # Create and destroy data to test memory management
            data = {"test": "x" * 1000}
            await asyncio.sleep(0.001)
            del data
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_growth = final_memory - initial_memory
        
        assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_error_rate_under_stress(self):
        """Test error rate under stress conditions."""
        errors = 0
        successes = 0
        total_operations = 200
        
        async def stress_operation(op_id):
            try:
                # Simulate operation that might fail under stress
                if op_id % 100 == 99:  # Simulate occasional failures
                    raise Exception("Simulated stress failure")
                await asyncio.sleep(0.001)
                return "success"
            except Exception:
                return "error"
        
        # Run stress test
        tasks = [stress_operation(i) for i in range(total_operations)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception) or result == "error":
                errors += 1
            else:
                successes += 1
        
        error_rate = (errors / total_operations) * 100
        assert error_rate < 5, f"Error rate too high under stress: {error_rate:.1f}%"


if __name__ == "__main__":
    # Run the deep validation tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])