"""
Agent Factory for Multi-Agent Debugging System with comprehensive validation.

This module provides a factory pattern for creating and managing debugging agents
with full validation of inputs, outputs, and backend operations.
"""

import asyncio
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Protocol
import hashlib
import logging

try:
    from pydantic_ai import Agent, RunContext
except ImportError:
    # Mock implementation for testing
    class RunContext:
        def __init__(self, deps):
            self.deps = deps

    class Agent:
        def __init__(self, model, deps_type=None, system_prompt=""):
            self.model = model
            self.deps_type = deps_type
            self.system_prompt = system_prompt

        async def run(self, prompt, deps=None, **kwargs):
            class Result:
                def __init__(self):
                    self.data = {"mock": "result", "prompt": prompt}
            return Result()

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import conint, confloat

try:
    from .providers import get_llm_model
except ImportError:
    def get_llm_model():
        return lambda: "mock_model"

try:
    from .dependencies import (
        AgentDependencies, DebuggingContext, AnalysisMode, ToolType,
        create_debugging_context, ToolResult
    )
except ImportError:
    # Mock classes for testing
    from enum import Enum
    from dataclasses import dataclass
    from datetime import datetime

    class AnalysisMode(str, Enum):
        STATIC = "static"
        DYNAMIC = "dynamic"
        COMPREHENSIVE = "comprehensive"

    class ToolType(str, Enum):
        GDB = "gdb"
        STRACE = "strace"
        LTRACE = "ltrace"
        PERF = "perf"
        CPPCHECK = "cppcheck"
        CLANG_TIDY = "clang-tidy"
        VALGRIND = "valgrind"

    @dataclass
    class ToolResult:
        tool_name: str
        command: str
        exit_code: int
        stdout: str
        stderr: str
        execution_time: float
        issues_found: List[Dict[str, Any]]
        success: bool
        error_message: Optional[str] = None

    @dataclass
    class AgentDependencies:
        context: Any
        message_queue: List[Any]
        results_cache: Dict[str, Any]

    def create_debugging_context(path, mode=None):
        return type('MockContext', (), {'target_path': path, 'analysis_mode': mode or AnalysisMode.STATIC})()

try:
    from .prompts import (
        LEAD_AGENT_PROMPT, TOOL_AGENT_PROMPT_TEMPLATE,
        DETAIL_AGENT_PROMPT, PLAN_AGENT_PROMPT
    )
except ImportError:
    # Mock prompts
    LEAD_AGENT_PROMPT = "Mock lead agent prompt"
    TOOL_AGENT_PROMPT_TEMPLATE = "Mock tool agent prompt for {tool_name}"
    DETAIL_AGENT_PROMPT = "Mock detail agent prompt"
    PLAN_AGENT_PROMPT = "Mock plan agent prompt"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)


class AgentType(str, Enum):
    """Types of agents in the debugging system."""
    LEAD = "lead"
    TOOL = "tool"
    DETAIL = "detail"
    PLAN = "plan"
    VALIDATOR = "validator"


class ValidationLevel(str, Enum):
    """Validation strictness levels."""
    STRICT = "strict"      # Full validation with type checking
    MODERATE = "moderate"  # Basic validation
    MINIMAL = "minimal"    # Only critical validation


class AgentConfig(BaseModel):
    """Configuration for agent creation with validation."""

    agent_type: AgentType
    agent_name: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=10)
    validation_level: ValidationLevel = ValidationLevel.STRICT
    max_retries: conint(ge=0, le=10) = 3
    timeout_seconds: confloat(ge=1.0, le=3600.0) = 300.0
    enable_caching: bool = True
    enable_logging: bool = True
    tool_config: Optional[Dict[str, Any]] = None

    @field_validator('agent_name')
    @classmethod
    def validate_agent_name(cls, v: str) -> str:
        """Ensure agent name follows naming conventions."""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Agent name must be alphanumeric with underscores/hyphens only")
        return v

    @model_validator(mode='after')
    def validate_tool_config(self) -> 'AgentConfig':
        """Validate tool-specific configurations."""
        if self.agent_type == AgentType.TOOL and not self.tool_config:
            raise ValueError("Tool agents require tool_config")
        return self


class ValidationResult(BaseModel):
    """Result of validation operations."""

    is_valid: bool
    validation_type: str
    timestamp: datetime = Field(default_factory=datetime.now)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def add_error(self, error: str) -> None:
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning without affecting validity."""
        self.warnings.append(warning)


class IValidator(Protocol):
    """Protocol for validators."""

    async def validate(self, data: Any) -> ValidationResult:
        """Validate data and return result."""
        ...


class InputValidator(BaseModel):
    """Validates agent inputs before processing."""

    validation_level: ValidationLevel

    async def validate_file_path(self, path: str) -> ValidationResult:
        """Validate file path for debugging."""
        result = ValidationResult(
            is_valid=True,
            validation_type="file_path"
        )

        try:
            path_obj = Path(path)

            # Check existence
            if not path_obj.exists():
                result.add_error(f"Path does not exist: {path}")
                return result

            # Check if it's a file
            if not path_obj.is_file():
                result.add_error(f"Path is not a file: {path}")
                return result

            # Check file extension for C++ files
            valid_extensions = {'.cpp', '.cc', '.cxx', '.c', '.h', '.hpp'}
            if path_obj.suffix not in valid_extensions:
                result.add_warning(f"Unusual file extension: {path_obj.suffix}")

            # Check file size (warn if > 10MB)
            if path_obj.stat().st_size > 10 * 1024 * 1024:
                result.add_warning("Large file size may impact performance")

            result.metadata["file_size"] = path_obj.stat().st_size
            result.metadata["extension"] = path_obj.suffix

        except Exception as e:
            result.add_error(f"File validation failed: {str(e)}")

        return result

    async def validate_analysis_mode(self, mode: str) -> ValidationResult:
        """Validate analysis mode selection."""
        result = ValidationResult(
            is_valid=True,
            validation_type="analysis_mode"
        )

        try:
            # Convert to enum
            analysis_mode = AnalysisMode(mode)
            result.metadata["mode"] = analysis_mode.value

            # Add recommendations based on mode
            if analysis_mode == AnalysisMode.STATIC:
                result.metadata["tools"] = ["cppcheck", "clang-tidy"]
            elif analysis_mode == AnalysisMode.DYNAMIC:
                result.metadata["tools"] = ["gdb", "valgrind", "strace"]
            else:  # comprehensive
                result.metadata["tools"] = ["all"]

        except ValueError:
            result.add_error(f"Invalid analysis mode: {mode}")

        return result


class OutputValidator(BaseModel):
    """Validates agent outputs after processing."""

    validation_level: ValidationLevel

    async def validate_tool_result(self, result: ToolResult) -> ValidationResult:
        """Validate tool execution results."""
        validation = ValidationResult(
            is_valid=True,
            validation_type="tool_result"
        )

        # Check required fields
        if not result.tool_name:
            validation.add_error("Tool name is required")

        if not result.command:
            validation.add_error("Command is required")

        # Check exit code
        if result.exit_code != 0 and not result.error_message:
            validation.add_warning("Non-zero exit code without error message")

        # Validate issues format
        for issue in result.issues_found:
            if not isinstance(issue, dict):
                validation.add_error("Issue must be a dictionary")
            elif "severity" not in issue or "message" not in issue:
                validation.add_warning("Issue missing severity or message")

        validation.metadata["tool"] = result.tool_name
        validation.metadata["issues_count"] = len(result.issues_found)

        return validation

    async def validate_analysis_result(self, result: Dict[str, Any]) -> ValidationResult:
        """Validate complete analysis results."""
        validation = ValidationResult(
            is_valid=True,
            validation_type="analysis_result"
        )

        required_fields = ["success", "session_id", "tools_executed", "total_issues"]

        for field in required_fields:
            if field not in result:
                validation.add_error(f"Missing required field: {field}")

        # Validate types
        if "total_issues" in result and not isinstance(result["total_issues"], int):
            validation.add_error("total_issues must be an integer")

        if "tools_executed" in result and not isinstance(result["tools_executed"], list):
            validation.add_error("tools_executed must be a list")

        return validation


class BackendValidator(BaseModel):
    """Validates backend operations and data integrity."""

    validation_level: ValidationLevel

    async def validate_cache_integrity(self, cache: Dict[str, Any]) -> ValidationResult:
        """Validate cache data integrity."""
        result = ValidationResult(
            is_valid=True,
            validation_type="cache_integrity"
        )

        for key, value in cache.items():
            # Check key format
            if not isinstance(key, str):
                result.add_error(f"Invalid cache key type: {type(key)}")

            # Check value serialization
            try:
                json.dumps(value, default=str)
            except (TypeError, ValueError) as e:
                result.add_error(f"Cache value not serializable: {key}")

        result.metadata["cache_size"] = len(cache)
        return result

    async def validate_message_queue(self, messages: List[Any]) -> ValidationResult:
        """Validate message queue integrity."""
        result = ValidationResult(
            is_valid=True,
            validation_type="message_queue"
        )

        for msg in messages:
            if not hasattr(msg, 'sender') or not hasattr(msg, 'recipient'):
                result.add_error("Message missing required fields")

            if hasattr(msg, 'timestamp'):
                if not isinstance(msg.timestamp, datetime):
                    result.add_warning("Invalid timestamp format")

        result.metadata["queue_size"] = len(messages)
        return result


class AgentWrapper(BaseModel):
    """Wrapper for agents with validation capabilities."""

    config: AgentConfig
    agent: Any  # Pydantic AI Agent
    input_validator: InputValidator
    output_validator: OutputValidator
    backend_validator: BackendValidator
    execution_history: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    async def execute_with_validation(
        self,
        prompt: str,
        dependencies: AgentDependencies,
        **kwargs
    ) -> Dict[str, Any]:
        """Execute agent with full validation pipeline."""
        execution_id = hashlib.md5(
            f"{self.config.agent_name}_{datetime.now().isoformat()}".encode()
        ).hexdigest()[:8]

        execution_record = {
            "id": execution_id,
            "agent": self.config.agent_name,
            "start_time": datetime.now().isoformat(),
            "validation_results": {}
        }

        try:
            # Pre-execution validation
            if self.config.validation_level != ValidationLevel.MINIMAL:
                # Validate dependencies context
                if hasattr(dependencies.context, 'target_path'):
                    path_validation = await self.input_validator.validate_file_path(
                        dependencies.context.target_path
                    )
                    execution_record["validation_results"]["input_path"] = path_validation.dict()

                    if not path_validation.is_valid:
                        raise ValueError(f"Input validation failed: {path_validation.errors}")

                # Validate cache integrity
                cache_validation = await self.backend_validator.validate_cache_integrity(
                    dependencies.results_cache
                )
                execution_record["validation_results"]["cache"] = cache_validation.dict()

            # Execute agent
            if self.config.enable_logging:
                logger.info(f"Executing agent: {self.config.agent_name}")

            result = await self.agent.run(prompt, deps=dependencies, **kwargs)

            # Post-execution validation
            if self.config.validation_level == ValidationLevel.STRICT:
                # Validate output structure
                if hasattr(result, 'data'):
                    output_validation = await self.output_validator.validate_analysis_result(
                        result.data if isinstance(result.data, dict) else {"data": result.data}
                    )
                    execution_record["validation_results"]["output"] = output_validation.dict()

            execution_record["end_time"] = datetime.now().isoformat()
            execution_record["success"] = True
            execution_record["result"] = str(result)

        except Exception as e:
            execution_record["end_time"] = datetime.now().isoformat()
            execution_record["success"] = False
            execution_record["error"] = str(e)

            if self.config.enable_logging:
                logger.error(f"Agent execution failed: {self.config.agent_name} - {str(e)}")

            raise

        finally:
            self.execution_history.append(execution_record)

        return execution_record


class AgentFactory:
    """Factory for creating validated debugging agents."""

    def __init__(self, default_validation_level: ValidationLevel = ValidationLevel.STRICT):
        self.default_validation_level = default_validation_level
        self._agent_registry: Dict[str, AgentWrapper] = {}
        self._creation_count = 0

    def create_agent(self, config: AgentConfig) -> AgentWrapper:
        """Create a new agent with validation capabilities."""
        # Determine system prompt
        if config.agent_type == AgentType.LEAD:
            system_prompt = LEAD_AGENT_PROMPT or config.system_prompt
        elif config.agent_type == AgentType.TOOL:
            tool_name = config.tool_config.get("tool_name", "generic") if config.tool_config else "generic"
            # Get tool mission from TOOL_MISSIONS dict, or use a generic mission
            try:
                from .prompts import TOOL_MISSIONS
                tool_mission = TOOL_MISSIONS.get(tool_name, f"DIAGNOSTIC SPECIALIST: Analyze {tool_name} output for issues and recommendations.")
            except ImportError:
                tool_mission = f"DIAGNOSTIC SPECIALIST: Analyze {tool_name} output for issues and recommendations."
            system_prompt = TOOL_AGENT_PROMPT_TEMPLATE.format(tool_name=tool_name, tool_mission=tool_mission) or config.system_prompt
        elif config.agent_type == AgentType.DETAIL:
            system_prompt = DETAIL_AGENT_PROMPT or config.system_prompt
        elif config.agent_type == AgentType.PLAN:
            system_prompt = PLAN_AGENT_PROMPT or config.system_prompt
        else:
            system_prompt = config.system_prompt

        # Ensure system prompt is not empty
        if not system_prompt or len(system_prompt.strip()) < 10:
            system_prompt = f"You are a {config.agent_type.value} agent for debugging C++ code. Provide detailed analysis and recommendations."

        # Create the Pydantic AI agent
        agent = Agent(
            get_llm_model(),
            deps_type=AgentDependencies,
            system_prompt=system_prompt
        )

        # Create validators
        input_validator = InputValidator(validation_level=config.validation_level)
        output_validator = OutputValidator(validation_level=config.validation_level)
        backend_validator = BackendValidator(validation_level=config.validation_level)

        # Create wrapper
        wrapper = AgentWrapper(
            config=config,
            agent=agent,
            input_validator=input_validator,
            output_validator=output_validator,
            backend_validator=backend_validator
        )

        # Register agent
        self._agent_registry[config.agent_name] = wrapper
        self._creation_count += 1

        logger.info(f"Created agent: {config.agent_name} (type: {config.agent_type})")

        return wrapper

    def create_standard_agents(self) -> Dict[str, AgentWrapper]:
        """Create the standard set of debugging agents."""
        agents = {}

        # Lead agent
        lead_config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="lead_coordinator",
            system_prompt=LEAD_AGENT_PROMPT,
            validation_level=ValidationLevel.STRICT
        )
        agents["lead"] = self.create_agent(lead_config)

        # Tool agents
        tools = ["gdb", "strace", "ltrace", "perf", "cppcheck", "clang-tidy", "valgrind"]
        for tool in tools:
            tool_config = AgentConfig(
                agent_type=AgentType.TOOL,
                agent_name=f"{tool}_agent",
                system_prompt=f"You are a specialized {tool} debugging agent for C++ code analysis.",
                tool_config={"tool_name": tool},
                validation_level=ValidationLevel.MODERATE
            )
            agents[tool] = self.create_agent(tool_config)

        # Detail agent
        detail_config = AgentConfig(
            agent_type=AgentType.DETAIL,
            agent_name="detail_correlator",
            system_prompt=DETAIL_AGENT_PROMPT,
            validation_level=ValidationLevel.STRICT
        )
        agents["detail"] = self.create_agent(detail_config)

        # Plan agent
        plan_config = AgentConfig(
            agent_type=AgentType.PLAN,
            agent_name="plan_generator",
            system_prompt=PLAN_AGENT_PROMPT,
            validation_level=ValidationLevel.MODERATE
        )
        agents["plan"] = self.create_agent(plan_config)

        return agents

    def get_agent(self, name: str) -> Optional[AgentWrapper]:
        """Retrieve a registered agent by name."""
        return self._agent_registry.get(name)

    def list_agents(self) -> List[str]:
        """List all registered agent names."""
        return list(self._agent_registry.keys())

    def get_statistics(self) -> Dict[str, Any]:
        """Get factory statistics."""
        return {
            "agents_created": self._creation_count,
            "agents_registered": len(self._agent_registry),
            "agent_names": self.list_agents(),
            "validation_levels": {
                name: wrapper.config.validation_level.value
                for name, wrapper in self._agent_registry.items()
            }
        }

    async def validate_all_agents(self) -> Dict[str, ValidationResult]:
        """Validate all registered agents."""
        results = {}

        for name, wrapper in self._agent_registry.items():
            result = ValidationResult(
                is_valid=True,
                validation_type="agent_health_check"
            )

            # Check configuration
            try:
                # Validate the config model itself
                wrapper.config.model_validate(wrapper.config.model_dump())
                result.metadata["config_valid"] = True
            except Exception as e:
                result.add_error(f"Configuration invalid: {str(e)}")

            # Check execution history
            if wrapper.execution_history:
                failures = sum(1 for exec in wrapper.execution_history if not exec.get("success", False))
                if failures > 0:
                    result.add_warning(f"{failures} failed executions in history")

            results[name] = result

        return results


# Module-level factory instance
_factory: Optional[AgentFactory] = None


def get_factory() -> AgentFactory:
    """Get or create the global agent factory."""
    global _factory
    if _factory is None:
        _factory = AgentFactory()
    return _factory


async def create_and_validate_agents() -> Dict[str, AgentWrapper]:
    """Create standard agents and validate them."""
    factory = get_factory()
    agents = factory.create_standard_agents()

    # Validate all agents
    validation_results = await factory.validate_all_agents()

    # Log validation results
    for name, result in validation_results.items():
        if not result.is_valid:
            logger.error(f"Agent {name} validation failed: {result.errors}")
        elif result.has_warnings:
            logger.warning(f"Agent {name} has warnings: {result.warnings}")
        else:
            logger.info(f"Agent {name} validated successfully")

    return agents