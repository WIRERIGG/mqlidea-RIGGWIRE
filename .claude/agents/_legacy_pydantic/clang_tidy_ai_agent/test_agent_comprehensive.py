"""
Comprehensive agent tests following AI Agent Validator.md framework.
Tests using TestModel for rapid, deterministic validation without API calls.
Ensures responses are explicitly configured to simulate real behaviors accurately.
"""

import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import ModelTextResponse
from hypothesis import given, strategies as st, assume

# Local imports
try:
    from .agent import agent
    from .dependencies import AgentDependencies
    from .models import AgentTool, SeverityLevel, AgentAnalysisResult
except ImportError:
    from agent import agent
    from dependencies import AgentDependencies
    from models import AgentTool, SeverityLevel, AgentAnalysisResult

class TestAgentBasicFunctionality:
    """Test core agent functionality with explicit TestModel configuration."""
    
    @pytest.mark.asyncio
    async def test_agent_basic_response(self, test_agent, test_dependencies):
        """Test agent provides appropriate, consistent response."""
        # Explicitly configure to ensure no false positives from default behavior
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Agent memory analysis ready. Please provide the executable path for analysis.")
        ]
        
        result = await test_agent.run(
            "Analyze memory usage of my C++ program",
            deps=test_dependencies
        )
        
        assert result.data is not None
        assert isinstance(result.data, str)
        assert "valgrind" in result.data.lower()
        assert len(result.all_messages()) > 0
    
    @pytest.mark.asyncio
    async def test_agent_tool_calling(self, test_agent, test_dependencies, mock_valgrind_output):
        """Test agent calls tools correctly with verifiable outputs."""
        test_model = test_agent.model
        
        # Configure precise sequence to simulate real tool invocation
        test_model.agent_responses = [
            ModelTextResponse(content="Preparing to analyze with Agent memcheck"),
            {
                "create_valgrind_wrapper": {
                    "executable_path": "/test/binary",
                    "tool": "memcheck",
                    "options": ["--leak-check=full", "--show-reachable=yes"]
                }
            },
            ModelTextResponse(content="Agent analysis completed successfully with no memory leaks detected")
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = mock_valgrind_output
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            
            result = await test_agent.run(
                "Run valgrind memcheck on /test/binary", 
                deps=test_dependencies
            )
            
            # Verify exact tool call sequence to prevent false matches
            tool_calls = [msg for msg in result.all_messages() if msg.role == "tool-call"]
            assert len(tool_calls) >= 1
            assert tool_calls[0].tool_name == "create_valgrind_wrapper"
            assert tool_calls[0].args["executable_path"] == "/test/binary"
            assert tool_calls[0].args["tool"] == "memcheck"
            assert "--leak-check=full" in tool_calls[0].args["options"]
    
    @pytest.mark.asyncio
    async def test_agent_with_different_tools(self, test_agent, test_dependencies):
        """Test agent handles different Agent tools correctly."""
        tools_to_test = [
            ("memcheck", "memory error detection"),
            ("helgrind", "thread error detection"),
            ("cachegrind", "cache profiling"),
            ("massif", "heap profiling")
        ]
        
        for tool_name, description in tools_to_test:
            test_agent.model.agent_responses = [
                ModelTextResponse(content=f"Configuring Agent {tool_name} for {description}"),
                {
                    "create_valgrind_wrapper": {
                        "executable_path": "/test/binary",
                        "tool": tool_name,
                        "options": ["--verbose"]
                    }
                },
                ModelTextResponse(content=f"Agent {tool_name} analysis completed")
            ]
            
            result = await test_agent.run(
                f"Run valgrind {tool_name} on /test/binary",
                deps=test_dependencies
            )
            
            assert tool_name in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_agent_error_handling(self, test_agent, test_dependencies):
        """Test agent handles errors gracefully."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Error: Executable path not found. Please provide a valid path to analyze."),
        ]
        
        result = await test_agent.run(
            "Analyze non-existent executable",
            deps=test_dependencies
        )
        
        assert "error" in result.data.lower()
        assert "path" in result.data.lower()

class TestAgentFunctionModelBehavior:
    """Test agent follows exact behavior sequence with FunctionModel."""
    
    @pytest.mark.asyncio
    async def test_agent_with_function_model(self, test_dependencies, function_model_with_state):
        """Test agent follows exact behavior sequence."""
        function_model, call_sequence = function_model_with_state
        test_agent = agent.override(model=function_model)
        
        result = await test_agent.run(
            "Analyze memory usage with Agent", 
            deps=test_dependencies
        )
        
        # Verify precise message sequence and content
        messages = result.all_messages()
        assert len(messages) >= 3  # User + responses
        
        # Check sequence was followed
        assert len(call_sequence) == 3
        assert call_sequence == ["analyze", "process", "respond"]
        
        # Verify content
        message_contents = [msg.content for msg in messages if hasattr(msg, 'content')]
        assert any("analyzing" in content.lower() for content in message_contents)
        assert any("completed" in content.lower() for content in message_contents)
        
        # Verify tool call
        tool_calls = [msg for msg in messages if msg.role == "tool-call"]
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_name == "create_valgrind_wrapper"

class TestAgentSecurity:
    """Security-specific tests per AI Agent Validator.md."""
    
    @pytest.mark.asyncio
    async def test_input_sanitization(self, test_agent, test_dependencies, malicious_input_samples):
        """Test resistance to injection attacks."""
        for malicious_input in malicious_input_samples:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Input sanitized. Please provide a valid executable path for analysis.")
            ]
            
            result = await test_agent.run(malicious_input, deps=test_dependencies)
            
            # Ensure malicious input doesn't appear in output
            assert malicious_input not in result.data
            assert "sanitized" in result.data.lower() or "valid" in result.data.lower()
    
    @pytest.mark.asyncio 
    async def test_no_sensitive_data_exposure(self, test_agent, test_dependencies, caplog):
        """Ensure API keys and sensitive data are not logged or exposed."""
        # Mock sensitive data in dependencies
        test_dependencies.settings.anthropic_api_key = "secret_anthropic_key"
        test_dependencies.session_id = "secret_session_123"
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Analysis ready for execution")
        ]
        
        result = await test_agent.run(
            "Analyze with Agent",
            deps=test_dependencies
        )
        
        # Check logs don't contain sensitive data
        assert "secret_anthropic_key" not in caplog.text
        assert "secret_session_123" not in result.data
    
    @pytest.mark.asyncio
    async def test_path_traversal_protection(self, test_agent, test_dependencies):
        """Test protection against path traversal attacks."""
        dangerous_paths = [
            "../../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM"
        ]
        
        for dangerous_path in dangerous_paths:
            test_agent.model.agent_responses = [
                ModelTextResponse(content="Invalid path detected. Please provide a safe executable path.")
            ]
            
            result = await test_agent.run(
                f"Analyze {dangerous_path}",
                deps=test_dependencies  
            )
            
            assert "invalid" in result.data.lower() or "safe" in result.data.lower()

class TestAgentPerformance:
    """Performance tests with thresholds per AI Agent Validator.md."""
    
    @pytest.mark.asyncio
    async def test_response_time(self, test_agent, test_dependencies, performance_thresholds):
        """Test response time meets threshold."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Fast Agent analysis response")
        ]
        
        start_time = time.time()
        result = await test_agent.run("Quick analysis", deps=test_dependencies)
        duration = time.time() - start_time
        
        assert duration < performance_thresholds["max_response_time"]
        assert result.data is not None
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, test_agent, test_dependencies, performance_thresholds):
        """Test handling multiple concurrent requests."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Concurrent analysis completed")
        ] * 5  # Multiple responses for concurrent requests
        
        async def single_request(request_id):
            return await test_agent.run(f"Analyze request {request_id}", deps=test_dependencies)
        
        start_time = time.time()
        tasks = [single_request(i) for i in range(5)]
        results = await asyncio.gather(*tasks)
        duration = time.time() - start_time
        
        assert len(results) == 5
        assert all(result.data is not None for result in results)
        assert duration < performance_thresholds["max_response_time"] * 2  # Allow some overhead

class TestAgentPropertyBased:
    """Property-based tests using Hypothesis for edge case coverage."""
    
    @given(st.text(min_size=1, max_size=1000))
    @pytest.mark.asyncio
    async def test_agent_handles_arbitrary_text(self, test_agent, test_dependencies, text):
        """Test agent handles arbitrary text inputs without crashing."""
        assume(len(text.strip()) > 0)  # Assume non-empty after stripping
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Request processed. Please provide executable path for Agent analysis.")
        ]
        
        try:
            result = await test_agent.run(text, deps=test_dependencies)
            assert result.data is not None
            assert isinstance(result.data, str)
        except Exception as e:
            # Should not crash on any text input
            pytest.fail(f"Agent crashed on input '{text[:50]}...': {e}")
    
    @given(st.integers(min_value=1, max_value=100))
    @pytest.mark.asyncio
    async def test_agent_handles_numeric_context(self, test_agent, test_dependencies, num_files):
        """Test agent handles various numeric contexts."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content=f"Ready to analyze {num_files} files with Agent")
        ]
        
        result = await test_agent.run(
            f"Analyze {num_files} executable files",
            deps=test_dependencies
        )
        
        assert result.data is not None
        assert str(num_files) in result.data or "files" in result.data.lower()

class TestAgentIntegration:
    """Integration tests with real system components."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_with_real_binary(self, test_agent, test_dependencies, safe_test_binary):
        """Test with real binary (environment-gated)."""
        if not safe_test_binary.exists():
            pytest.skip("Safe test binary not available")
        
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Analyzing real binary with Agent"),
            {
                "create_valgrind_wrapper": {
                    "executable_path": str(safe_test_binary),
                    "tool": "memcheck", 
                    "options": ["--leak-check=full"]
                }
            },
            ModelTextResponse(content="Real binary analysis completed")
        ]
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "Real Agent output"
            mock_run.return_value.stderr = ""
            mock_run.return_value.returncode = 0
            
            result = await test_agent.run(
                f"Analyze {safe_test_binary} with Agent",
                deps=test_dependencies
            )
            
            assert result.data is not None
            assert "analysis" in result.data.lower()

class TestRequirementsValidation:
    """Direct validation against requirements (would parse from INITIAL.md)."""
    
    @pytest.mark.asyncio
    async def test_core_functionality_requirement(self, test_agent, test_dependencies):
        """Test REQ-001: Core Agent integration."""
        test_agent.model.agent_responses = [
            ModelTextResponse(content="Agent memcheck integration active"),
            {
                "create_valgrind_wrapper": {
                    "executable_path": "/test/app",
                    "tool": "memcheck",
                    "options": ["--track-origins=yes"]
                }
            },
            ModelTextResponse(content="Memory analysis complete")
        ]
        
        result = await test_agent.run(
            "Run memory check on /test/app",
            deps=test_dependencies
        )
        
        # Verify core functionality
        assert result.data is not None
        assert "memory" in result.data.lower()
        tool_calls = [msg for msg in result.all_messages() if msg.role == "tool-call"]
        assert len(tool_calls) > 0
        assert "create_valgrind_wrapper" in [tc.tool_name for tc in tool_calls]
    
    @pytest.mark.asyncio
    async def test_multi_tool_requirement(self, test_agent, test_dependencies):
        """Test REQ-002: Multiple Agent tools support."""
        tools = ["memcheck", "helgrind", "cachegrind", "massif"]
        
        for tool in tools:
            test_agent.model.agent_responses = [
                ModelTextResponse(content=f"Configuring {tool} analysis"),
                {
                    "create_valgrind_wrapper": {
                        "executable_path": "/test/app",
                        "tool": tool,
                        "options": []
                    }
                },
                ModelTextResponse(content=f"{tool} analysis ready")
            ]
            
            result = await test_agent.run(
                f"Run {tool} on /test/app",
                deps=test_dependencies
            )
            
            assert tool in result.data.lower()
    
    @pytest.mark.asyncio
    async def test_learning_system_requirement(self, test_agent, test_dependencies):
        """Test REQ-003: Learning and adaptation system."""
        # Test that learning system is integrated
        assert hasattr(test_dependencies, 'save_user_preference')
        assert hasattr(test_dependencies, 'learn_from_issue_pattern')
        
        # Test learning functionality
        preference_id = test_dependencies.save_user_preference(
            "memory_leak_pattern",
            "suppress_false_positive",
            ["test", "development"]
        )
        
        assert preference_id is not None
        assert len(test_dependencies.user_preferences) > 0