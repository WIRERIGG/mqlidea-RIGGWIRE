"""
Tests for the agent factory and validation system.
"""

import asyncio
import pytest
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch, MagicMock

from ..agent_factory import (
    AgentFactory, AgentConfig, AgentType, ValidationLevel,
    ValidationResult, InputValidator, OutputValidator, BackendValidator,
    AgentWrapper, get_factory, create_and_validate_agents
)
from ..dependencies import (
    AgentDependencies, DebuggingContext, AnalysisMode, ToolType,
    ToolResult, create_debugging_context
)
from ..agent import AnalysisRequest, AnalysisResult, MultiAgentDebugger


class TestAgentFactory:
    """Test agent factory functionality."""

    def test_factory_singleton(self):
        """Test factory singleton pattern."""
        factory1 = get_factory()
        factory2 = get_factory()
        assert factory1 is factory2

    def test_agent_config_validation(self):
        """Test agent configuration validation."""
        # Valid config
        config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="test_agent",
            system_prompt="Test system prompt for agent"
        )
        assert config.agent_name == "test_agent"
        assert config.validation_level == ValidationLevel.STRICT

        # Invalid name
        with pytest.raises(ValueError) as exc:
            AgentConfig(
                agent_type=AgentType.LEAD,
                agent_name="test@agent!",  # Invalid characters
                system_prompt="Test prompt"
            )
        assert "alphanumeric" in str(exc.value).lower()

        # Tool agent without config
        with pytest.raises(ValueError) as exc:
            AgentConfig(
                agent_type=AgentType.TOOL,
                agent_name="tool_agent",
                system_prompt="Test prompt"
                # Missing tool_config
            )
        assert "tool_config" in str(exc.value).lower()

    def test_create_agent(self):
        """Test agent creation."""
        factory = AgentFactory()

        config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="lead_test",
            system_prompt="Lead agent for testing",
            validation_level=ValidationLevel.MODERATE
        )

        wrapper = factory.create_agent(config)

        assert isinstance(wrapper, AgentWrapper)
        assert wrapper.config.agent_name == "lead_test"
        assert wrapper.config.validation_level == ValidationLevel.MODERATE
        assert wrapper.input_validator is not None
        assert wrapper.output_validator is not None
        assert wrapper.backend_validator is not None

    def test_create_standard_agents(self):
        """Test creation of standard agent set."""
        factory = AgentFactory()
        agents = factory.create_standard_agents()

        # Check all required agents are created
        assert "lead" in agents
        assert "gdb" in agents
        assert "strace" in agents
        assert "clang-tidy" in agents
        assert "detail" in agents
        assert "plan" in agents

        # Check agent types
        assert agents["lead"].config.agent_type == AgentType.LEAD
        assert agents["gdb"].config.agent_type == AgentType.TOOL
        assert agents["detail"].config.agent_type == AgentType.DETAIL

    def test_factory_statistics(self):
        """Test factory statistics tracking."""
        factory = AgentFactory()

        # Initial state
        stats = factory.get_statistics()
        initial_count = stats["agents_created"]

        # Create agents
        factory.create_standard_agents()

        stats = factory.get_statistics()
        assert stats["agents_created"] > initial_count
        assert len(stats["agent_names"]) > 0
        assert "validation_levels" in stats


class TestValidators:
    """Test validation components."""

    @pytest.mark.asyncio
    async def test_input_validator_file_path(self, tmp_path):
        """Test file path validation."""
        validator = InputValidator(validation_level=ValidationLevel.STRICT)

        # Create a test C++ file
        test_file = tmp_path / "test.cpp"
        test_file.write_text("#include <iostream>\nint main() {}")

        # Valid file
        result = await validator.validate_file_path(str(test_file))
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.metadata["extension"] == ".cpp"

        # Non-existent file
        result = await validator.validate_file_path("/nonexistent/file.cpp")
        assert not result.is_valid
        assert len(result.errors) > 0

        # Directory instead of file
        result = await validator.validate_file_path(str(tmp_path))
        assert not result.is_valid
        assert "not a file" in result.errors[0].lower()

        # Non-C++ file (warning)
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not cpp")
        result = await validator.validate_file_path(str(txt_file))
        assert result.is_valid  # Still valid but with warning
        assert len(result.warnings) > 0

    @pytest.mark.asyncio
    async def test_input_validator_analysis_mode(self):
        """Test analysis mode validation."""
        validator = InputValidator(validation_level=ValidationLevel.STRICT)

        # Valid modes
        for mode in ["static", "dynamic", "comprehensive"]:
            result = await validator.validate_analysis_mode(mode)
            assert result.is_valid
            assert result.metadata["mode"] == mode

        # Invalid mode
        result = await validator.validate_analysis_mode("invalid_mode")
        assert not result.is_valid
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_output_validator_tool_result(self):
        """Test tool result validation."""
        validator = OutputValidator(validation_level=ValidationLevel.STRICT)

        # Valid result
        tool_result = ToolResult(
            tool_name="cppcheck",
            command="cppcheck --enable=all test.cpp",
            exit_code=0,
            stdout="Checking test.cpp...",
            stderr="",
            execution_time=1.5,
            issues_found=[
                {"severity": "warning", "message": "Unused variable"},
                {"severity": "critical", "message": "Memory leak"}
            ],
            success=True
        )

        result = await validator.validate_tool_result(tool_result)
        assert result.is_valid
        assert result.metadata["tool"] == "cppcheck"
        assert result.metadata["issues_count"] == 2

        # Invalid result - missing tool name
        invalid_result = ToolResult(
            tool_name="",
            command="test",
            exit_code=0,
            stdout="",
            stderr="",
            execution_time=0,
            issues_found=[],
            success=True
        )

        result = await validator.validate_tool_result(invalid_result)
        assert not result.is_valid
        assert "Tool name is required" in result.errors[0]

    @pytest.mark.asyncio
    async def test_backend_validator_cache(self):
        """Test cache integrity validation."""
        validator = BackendValidator(validation_level=ValidationLevel.STRICT)

        # Valid cache
        cache = {
            "tool1": {"result": "data", "timestamp": "2024-01-01"},
            "tool2": {"result": "more data", "count": 5}
        }

        result = await validator.validate_cache_integrity(cache)
        assert result.is_valid
        assert result.metadata["cache_size"] == 2

        # Invalid cache - non-string keys
        invalid_cache = {
            123: {"result": "data"},  # Non-string key
            "valid": {"data": "ok"}
        }

        result = await validator.validate_cache_integrity(invalid_cache)
        assert not result.is_valid
        assert "Invalid cache key type" in result.errors[0]


class TestMultiAgentDebugger:
    """Test multi-agent debugger with factory and validation."""

    @pytest.mark.asyncio
    async def test_debugger_initialization(self):
        """Test debugger initialization with factory."""
        debugger = MultiAgentDebugger(validation_level=ValidationLevel.MODERATE)

        assert debugger.validation_level == ValidationLevel.MODERATE
        assert debugger.factory is not None
        assert len(debugger.tool_agents) > 0
        assert ToolType.GDB in debugger.tool_agents
        assert ToolType.CLANG_TIDY in debugger.tool_agents

    @pytest.mark.asyncio
    async def test_request_validation(self, tmp_path):
        """Test analysis request validation."""
        # Create test file
        test_file = tmp_path / "test.cpp"
        test_file.write_text("#include <iostream>\nint main() {}")

        # Valid request
        request = AnalysisRequest(
            target_path=str(test_file),
            analysis_mode="comprehensive",
            output_format="both",
            max_parallel_tools=4,
            timeout=300
        )

        assert request.target_path == str(test_file)
        assert request.validation_level == ValidationLevel.STRICT

        # Invalid path
        with pytest.raises(ValueError) as exc:
            AnalysisRequest(
                target_path="/nonexistent/file.cpp",
                analysis_mode="comprehensive"
            )
        assert "does not exist" in str(exc.value)

        # Invalid output format
        with pytest.raises(ValueError) as exc:
            AnalysisRequest(
                target_path=str(test_file),
                output_format="invalid"
            )
        assert "Invalid output format" in str(exc.value)

    @pytest.mark.asyncio
    async def test_validation_pipeline(self, tmp_path):
        """Test complete validation pipeline."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("""
        #include <iostream>
        int main() {
            std::cout << "Test" << std::endl;
            return 0;
        }
        """)

        debugger = MultiAgentDebugger(validation_level=ValidationLevel.STRICT)

        request = AnalysisRequest(
            target_path=str(test_file),
            analysis_mode="static",
            max_parallel_tools=2
        )

        # Test request validation
        validation_result = await debugger._validate_request(request)
        assert validation_result.is_valid
        assert validation_result.metadata["target_path"] == str(test_file)

        # Test backend state validation
        deps = AgentDependencies(
            context=create_debugging_context(str(test_file)),
            message_queue=[],
            results_cache={}
        )

        backend_validation = await debugger._validate_backend_state(deps)
        assert backend_validation.is_valid

    @pytest.mark.asyncio
    async def test_agent_wrapper_execution(self, tmp_path):
        """Test agent wrapper with validation."""
        factory = AgentFactory()

        config = AgentConfig(
            agent_type=AgentType.TOOL,
            agent_name="test_tool",
            system_prompt="Test tool agent",
            tool_config={"tool_name": "test"},
            validation_level=ValidationLevel.STRICT
        )

        wrapper = factory.create_agent(config)

        # Create test dependencies
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int main() {}")

        context = create_debugging_context(str(test_file))
        deps = AgentDependencies(
            context=context,
            message_queue=[],
            results_cache={}
        )

        # Mock the agent run method
        with patch.object(wrapper.agent, 'run') as mock_run:
            mock_result = Mock()
            mock_result.data = {"test": "result"}
            mock_run.return_value = mock_result

            execution_record = await wrapper.execute_with_validation(
                prompt="Test prompt",
                dependencies=deps
            )

            assert execution_record["success"]
            assert execution_record["agent"] == "test_tool"
            assert "validation_results" in execution_record
            assert len(wrapper.execution_history) == 1


class TestValidationResults:
    """Test validation result handling."""

    def test_validation_result_errors(self):
        """Test validation result error handling."""
        result = ValidationResult(
            is_valid=True,
            validation_type="test"
        )

        assert result.is_valid
        assert len(result.errors) == 0

        # Add error
        result.add_error("Test error")
        assert not result.is_valid
        assert len(result.errors) == 1
        assert "Test error" in result.errors

    def test_validation_result_warnings(self):
        """Test validation result warning handling."""
        result = ValidationResult(
            is_valid=True,
            validation_type="test"
        )

        assert not result.has_warnings

        # Add warning
        result.add_warning("Test warning")
        assert result.is_valid  # Still valid
        assert result.has_warnings
        assert "Test warning" in result.warnings


@pytest.mark.asyncio
async def test_factory_agent_health_check():
    """Test agent health check validation."""
    factory = AgentFactory()
    agents = factory.create_standard_agents()

    # Run health check
    health_results = await factory.validate_all_agents()

    assert len(health_results) == len(agents)

    for name, result in health_results.items():
        assert isinstance(result, ValidationResult)
        assert result.validation_type == "agent_health_check"
        # Should be valid for newly created agents
        assert result.is_valid


if __name__ == "__main__":
    pytest.main([__file__, "-v"])