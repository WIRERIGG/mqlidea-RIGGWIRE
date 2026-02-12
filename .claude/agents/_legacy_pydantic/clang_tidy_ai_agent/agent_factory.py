"""
Clang-Tidy AI Agent Factory with comprehensive validation and code quality focus.

This factory creates validated Clang-Tidy agents with specialized validation rules
for C++ static analysis, code quality checking, and automated fixing.
"""

import asyncio
import json
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Protocol, Callable
import hashlib

# Import the template factory
import sys
sys.path.append(str(Path(__file__).parent.parent))
from agent_factory_template import (
    AgentFactory, AgentFactoryConfig, ValidationLevel, ValidationResult,
    InputValidator, OutputValidator, BackendValidator, ValidatedAgent
)

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
                    self.data = {"mock": "clang_tidy_result", "prompt": prompt}
            return Result()

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import conint, confloat

try:
    from models import (
        ClangTidyDependencies,
        IssueDiscoveryResponse,
        FixStrategyResponse,
        FixApplicationResponse,
        ValidationResponse,
        ArchonTaskResponse
    )
    from tools import (
        ClangTidyAnalyzer,
        IssueDiscoveryEngine,
        FixStrategyPlanner,
        FixApplicationEngine,
        ValidationEngine
    )
except ImportError:
    # Mock imports for testing
    class ClangTidyDependencies:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class IssueDiscoveryResponse(BaseModel):
        issues: List[Dict[str, Any]] = Field(default_factory=list)

    class FixStrategyResponse(BaseModel):
        strategies: List[Dict[str, Any]] = Field(default_factory=list)

    class FixApplicationResponse(BaseModel):
        applied_fixes: List[Dict[str, Any]] = Field(default_factory=list)

    class ValidationResponse(BaseModel):
        is_valid: bool = True
        errors: List[str] = Field(default_factory=list)

    class ArchonTaskResponse(BaseModel):
        task_id: str = "mock"
        status: str = "completed"

    # Mock tool classes
    class ClangTidyAnalyzer:
        pass

    class IssueDiscoveryEngine:
        pass

    class FixStrategyPlanner:
        pass

    class FixApplicationEngine:
        pass

    class ValidationEngine:
        pass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ClangTidyAgentType(str, Enum):
    """Types of Clang-Tidy agents."""
    ISSUE_DISCOVERER = "issue_discoverer"         # Finds code quality issues
    FIX_STRATEGIST = "fix_strategist"            # Plans fix strategies
    FIX_APPLICATOR = "fix_applicator"            # Applies fixes to code
    VALIDATOR = "validator"                       # Validates fixes and results
    ORCHESTRATOR = "orchestrator"                # Coordinates the full pipeline
    ARCHON_INTEGRATOR = "archon_integrator"      # Manages Archon task integration


class ClangTidyValidationLevel(str, Enum):
    """Clang-Tidy specific validation levels."""
    ENTERPRISE = "enterprise"      # Maximum validation for production code
    PRODUCTION = "production"      # Standard production validation
    DEVELOPMENT = "development"    # Development-friendly validation
    EXPERIMENTAL = "experimental" # Minimal validation for experimentation


class ClangTidyInputValidator(InputValidator):
    """Specialized input validator for Clang-Tidy analysis tasks."""

    async def validate_source_file(self, file_path: str) -> ValidationResult:
        """Validate source file for Clang-Tidy analysis."""
        result = ValidationResult(
            is_valid=True,
            validation_type="source_file_validation"
        )

        try:
            path_obj = Path(file_path)

            # Check file existence
            if not path_obj.exists():
                result.add_error(f"Source file does not exist: {file_path}")
                return result

            # Check file extension
            valid_extensions = {'.cpp', '.cc', '.cxx', '.c', '.h', '.hpp', '.hxx'}
            if path_obj.suffix not in valid_extensions:
                result.add_warning(f"Unusual file extension for C++: {path_obj.suffix}")

            # Check file size
            file_size = path_obj.stat().st_size
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                result.add_warning("Large file size may impact analysis performance")
            elif file_size == 0:
                result.add_error("Empty source file")

            # Check file content for basic C++ indicators
            try:
                content = path_obj.read_text(encoding='utf-8', errors='ignore')
                cpp_indicators = [
                    '#include', 'namespace', 'class ', 'struct ',
                    'template', 'using ', 'std::', 'const ', 'auto '
                ]

                indicator_count = sum(1 for indicator in cpp_indicators if indicator in content)
                if indicator_count == 0:
                    result.add_warning("File may not contain C++ code")

                result.metadata["file_size"] = file_size
                result.metadata["line_count"] = content.count('\n') + 1
                result.metadata["cpp_indicators"] = indicator_count

            except Exception as e:
                result.add_warning(f"Could not read file content: {str(e)}")

        except Exception as e:
            result.add_error(f"File validation failed: {str(e)}")

        return result

    async def validate_clang_tidy_config(self, config: Dict[str, Any]) -> ValidationResult:
        """Validate Clang-Tidy configuration."""
        result = ValidationResult(
            is_valid=True,
            validation_type="clang_tidy_config"
        )

        required_fields = ["checks", "warnings_as_errors"]
        for field in required_fields:
            if field not in config:
                result.add_error(f"Missing required config field: {field}")

        # Validate checks format
        if "checks" in config:
            checks = config["checks"]
            if not isinstance(checks, str):
                result.add_error("Checks must be a string")
            else:
                # Check for dangerous or experimental checks
                dangerous_checks = [
                    "misc-unused-parameters",  # Can be too noisy
                    "readability-magic-numbers",  # Often too strict
                ]

                enabled_dangerous = [check for check in dangerous_checks if check in checks]
                if enabled_dangerous:
                    result.add_warning(f"Enabled potentially noisy checks: {enabled_dangerous}")

                result.metadata["checks_string"] = checks
                result.metadata["check_count"] = len(checks.split(','))

        # Validate severity levels
        if "severity" in config:
            valid_severities = ["error", "warning", "note"]
            if config["severity"] not in valid_severities:
                result.add_error(f"Invalid severity level: {config['severity']}")

        return result

    async def validate_fix_strategy(self, strategy: Dict[str, Any]) -> ValidationResult:
        """Validate fix strategy parameters."""
        result = ValidationResult(
            is_valid=True,
            validation_type="fix_strategy_validation"
        )

        # Check strategy type
        if "strategy_type" not in strategy:
            result.add_error("Missing strategy_type")
        else:
            valid_strategies = ["automated", "guided", "manual", "conservative"]
            if strategy["strategy_type"] not in valid_strategies:
                result.add_error(f"Invalid strategy type: {strategy['strategy_type']}")

        # Check risk level
        if "risk_level" in strategy:
            valid_risks = ["low", "medium", "high"]
            if strategy["risk_level"] not in valid_risks:
                result.add_error(f"Invalid risk level: {strategy['risk_level']}")

        # Check fix confidence threshold
        if "confidence_threshold" in strategy:
            try:
                threshold = float(strategy["confidence_threshold"])
                if not 0.0 <= threshold <= 1.0:
                    result.add_error("Confidence threshold must be between 0.0 and 1.0")
                result.metadata["confidence_threshold"] = threshold
            except (ValueError, TypeError):
                result.add_error("Confidence threshold must be a number")

        return result


class ClangTidyOutputValidator(OutputValidator):
    """Specialized output validator for Clang-Tidy analysis results."""

    async def validate_issue_discovery(self, issues: List[Dict[str, Any]]) -> ValidationResult:
        """Validate discovered issues format."""
        result = ValidationResult(
            is_valid=True,
            validation_type="issue_discovery_validation"
        )

        if not isinstance(issues, list):
            result.add_error("Issues must be a list")
            return result

        required_fields = ["check_name", "severity", "message", "file", "line"]
        severity_levels = ["error", "warning", "note"]

        issue_count_by_severity = {"error": 0, "warning": 0, "note": 0}

        for i, issue in enumerate(issues):
            if not isinstance(issue, dict):
                result.add_error(f"Issue {i} must be a dictionary")
                continue

            # Check required fields
            for field in required_fields:
                if field not in issue:
                    result.add_error(f"Issue {i} missing required field: {field}")

            # Validate severity
            if "severity" in issue:
                severity = issue["severity"]
                if severity in severity_levels:
                    issue_count_by_severity[severity] += 1
                else:
                    result.add_warning(f"Issue {i} has unknown severity: {severity}")

            # Validate line number
            if "line" in issue:
                try:
                    line_num = int(issue["line"])
                    if line_num <= 0:
                        result.add_error(f"Issue {i} has invalid line number: {line_num}")
                except (ValueError, TypeError):
                    result.add_error(f"Issue {i} line number must be an integer")

        result.metadata["total_issues"] = len(issues)
        result.metadata["issues_by_severity"] = issue_count_by_severity

        # Warn about excessive issues
        if len(issues) > 1000:
            result.add_warning("Very large number of issues detected - consider filtering")

        return result

    async def validate_fix_application(self, fixes: List[Dict[str, Any]]) -> ValidationResult:
        """Validate applied fixes format."""
        result = ValidationResult(
            is_valid=True,
            validation_type="fix_application_validation"
        )

        if not isinstance(fixes, list):
            result.add_error("Fixes must be a list")
            return result

        required_fields = ["issue_id", "fix_type", "status"]
        valid_statuses = ["applied", "failed", "skipped", "manual_required"]

        status_counts = {status: 0 for status in valid_statuses}

        for i, fix in enumerate(fixes):
            if not isinstance(fix, dict):
                result.add_error(f"Fix {i} must be a dictionary")
                continue

            # Check required fields
            for field in required_fields:
                if field not in fix:
                    result.add_error(f"Fix {i} missing required field: {field}")

            # Validate status
            if "status" in fix:
                status = fix["status"]
                if status in valid_statuses:
                    status_counts[status] += 1
                else:
                    result.add_warning(f"Fix {i} has unknown status: {status}")

            # Check for fix details
            if fix.get("status") == "failed" and "error_message" not in fix:
                result.add_warning(f"Fix {i} failed but no error message provided")

        result.metadata["total_fixes"] = len(fixes)
        result.metadata["fixes_by_status"] = status_counts
        result.metadata["success_rate"] = (
            status_counts["applied"] / len(fixes) if fixes else 0.0
        )

        return result


class ClangTidyBackendValidator(BackendValidator):
    """Specialized backend validator for Clang-Tidy operations."""

    async def validate_analysis_cache(self, cache: Dict[str, Any]) -> ValidationResult:
        """Validate analysis result cache."""
        result = ValidationResult(
            is_valid=True,
            validation_type="analysis_cache_validation"
        )

        # Check cache structure
        for key, value in cache.items():
            if not isinstance(key, str):
                result.add_error(f"Cache key must be string: {type(key)}")

            # Validate cached analysis results
            if isinstance(value, dict):
                if "issues" in value and not isinstance(value["issues"], list):
                    result.add_error(f"Invalid cached issues format for key: {key}")

                if "timestamp" in value:
                    try:
                        # Check if timestamp is too old (>24 hours)
                        timestamp = datetime.fromisoformat(value["timestamp"])
                        age = datetime.now() - timestamp
                        if age.total_seconds() > 24 * 3600:
                            result.add_warning(f"Stale cache entry: {key}")
                    except Exception:
                        result.add_warning(f"Invalid timestamp format in cache: {key}")

        # Check cache size
        cache_size = len(json.dumps(cache, default=str))
        if cache_size > 100 * 1024 * 1024:  # 100MB limit
            result.add_warning(f"Large analysis cache size: {cache_size / 1024 / 1024:.2f}MB")

        result.metadata["cache_entries"] = len(cache)
        result.metadata["cache_size_mb"] = cache_size / 1024 / 1024

        return result

    async def validate_archon_integration(self, archon_data: Dict[str, Any]) -> ValidationResult:
        """Validate Archon MCP integration data."""
        result = ValidationResult(
            is_valid=True,
            validation_type="archon_integration_validation"
        )

        if not archon_data:
            result.add_warning("No Archon integration data")
            return result

        # Check required Archon fields
        required_fields = ["project_id", "task_id", "status"]
        for field in required_fields:
            if field not in archon_data:
                result.add_error(f"Missing Archon field: {field}")

        # Validate task status
        if "status" in archon_data:
            valid_statuses = ["todo", "doing", "review", "done"]
            if archon_data["status"] not in valid_statuses:
                result.add_error(f"Invalid Archon task status: {archon_data['status']}")

        # Check task metadata
        if "metadata" in archon_data:
            metadata = archon_data["metadata"]
            if not isinstance(metadata, dict):
                result.add_error("Archon metadata must be a dictionary")

        result.metadata["has_archon_integration"] = True
        result.metadata["archon_status"] = archon_data.get("status", "unknown")

        return result


class ClangTidyAgentConfig(AgentFactoryConfig):
    """Extended configuration for Clang-Tidy agents."""

    agent_type: ClangTidyAgentType
    clang_tidy_checks: str = Field(
        default="*,-readability-magic-numbers",
        description="Clang-Tidy checks to enable"
    )
    fix_strategy: str = Field(
        default="conservative",
        description="Fix application strategy"
    )
    enable_auto_fix: bool = Field(
        default=False,
        description="Enable automatic fix application"
    )
    confidence_threshold: float = Field(
        default=0.8,
        ge=0.0, le=1.0,
        description="Minimum confidence for automatic fixes"
    )
    enable_archon_integration: bool = Field(
        default=True,
        description="Enable Archon MCP task management"
    )
    clang_tidy_validation_level: ClangTidyValidationLevel = Field(
        default=ClangTidyValidationLevel.PRODUCTION,
        description="Clang-Tidy specific validation level"
    )

    @field_validator('fix_strategy')
    @classmethod
    def validate_fix_strategy(cls, v: str) -> str:
        """Validate fix strategy."""
        valid_strategies = ["conservative", "aggressive", "guided", "manual"]
        if v.lower() not in valid_strategies:
            raise ValueError(f"Invalid fix strategy. Must be one of: {valid_strategies}")
        return v.lower()


class ClangTidyAgentFactory(AgentFactory):
    """Factory for creating specialized Clang-Tidy analysis agents."""

    def __init__(self):
        super().__init__(default_validation_level=ValidationLevel.STRICT)
        self.clang_tidy_configs: Dict[str, ClangTidyAgentConfig] = {}

    def create_clang_tidy_agent(
        self,
        config: ClangTidyAgentConfig,
        custom_tools: Optional[List[Callable]] = None
    ) -> ValidatedAgent:
        """Create a specialized Clang-Tidy agent with analysis-focused validation."""

        # Create custom validators with Clang-Tidy specific rules
        input_validator = ClangTidyInputValidator(
            validation_level=config.validation_level,
            custom_rules={
                "validate_file_extension": lambda path: str(path).endswith(('.cpp', '.h', '.cc')),
                "validate_file_size": lambda path: Path(path).stat().st_size < 50 * 1024 * 1024,
                "validate_readable": lambda path: Path(path).is_file() and os.access(path, os.R_OK)
            }
        )

        output_validator = ClangTidyOutputValidator(
            validation_level=config.validation_level,
            custom_rules={
                "validate_issues_format": lambda out: isinstance(out, (list, dict)),
                "validate_has_results": lambda out: len(out) > 0 if isinstance(out, list) else bool(out),
                "validate_no_critical_errors": lambda out: self._no_critical_errors(out)
            }
        )

        backend_validator = ClangTidyBackendValidator(
            validation_level=config.validation_level,
            custom_rules={
                "required_keys": ["analysis_cache", "archon_data", "session_info"]
            }
        )

        # Determine system prompt based on agent type
        system_prompt = self._get_specialized_prompt(config)

        # Create the Pydantic AI agent
        agent = Agent(
            model=lambda: "mock_model",  # Will be replaced with actual model
            deps_type=ClangTidyDependencies,
            system_prompt=system_prompt
        )

        # Register tools based on configuration
        tools = self._get_tools_for_config(config)
        if custom_tools:
            tools.extend(custom_tools)

        for tool in tools:
            if hasattr(agent, 'tool'):
                agent.tool(tool)

        # Create validated agent wrapper
        validated_agent = ValidatedAgent(
            agent=agent,
            config=config,
            input_validator=input_validator,
            output_validator=output_validator,
            backend_validator=backend_validator
        )

        # Store Clang-Tidy specific config
        self.clang_tidy_configs[config.agent_name] = config
        self._agent_registry[config.agent_name] = validated_agent

        logger.info(f"Created Clang-Tidy agent: {config.agent_name} (type: {config.agent_type})")

        return validated_agent

    def create_standard_clang_tidy_agents(self) -> Dict[str, ValidatedAgent]:
        """Create the standard set of Clang-Tidy analysis agents."""
        agents = {}

        # Issue Discovery Agent
        discovery_config = ClangTidyAgentConfig(
            agent_name="clang_tidy_discoverer",
            agent_type=ClangTidyAgentType.ISSUE_DISCOVERER,
            system_prompt="You are a Clang-Tidy issue discovery specialist.",
            clang_tidy_checks="*,-readability-magic-numbers,-misc-unused-parameters",
            validation_level=ValidationLevel.STRICT,
            clang_tidy_validation_level=ClangTidyValidationLevel.PRODUCTION
        )
        agents["discoverer"] = self.create_clang_tidy_agent(discovery_config)

        # Fix Strategy Agent
        strategist_config = ClangTidyAgentConfig(
            agent_name="clang_tidy_strategist",
            agent_type=ClangTidyAgentType.FIX_STRATEGIST,
            system_prompt="You are a Clang-Tidy fix strategy planning expert.",
            fix_strategy="conservative",
            confidence_threshold=0.9,
            validation_level=ValidationLevel.STRICT,
            clang_tidy_validation_level=ClangTidyValidationLevel.PRODUCTION
        )
        agents["strategist"] = self.create_clang_tidy_agent(strategist_config)

        # Fix Application Agent
        applicator_config = ClangTidyAgentConfig(
            agent_name="clang_tidy_applicator",
            agent_type=ClangTidyAgentType.FIX_APPLICATOR,
            system_prompt="You are a Clang-Tidy automated fix application specialist.",
            enable_auto_fix=True,
            confidence_threshold=0.85,
            validation_level=ValidationLevel.STRICT,
            clang_tidy_validation_level=ClangTidyValidationLevel.ENTERPRISE
        )
        agents["applicator"] = self.create_clang_tidy_agent(applicator_config)

        # Validation Agent
        validator_config = ClangTidyAgentConfig(
            agent_name="clang_tidy_validator",
            agent_type=ClangTidyAgentType.VALIDATOR,
            system_prompt="You are a Clang-Tidy fix validation and quality assurance expert.",
            fix_strategy="manual",
            validation_level=ValidationLevel.STRICT,
            clang_tidy_validation_level=ClangTidyValidationLevel.ENTERPRISE
        )
        agents["validator"] = self.create_clang_tidy_agent(validator_config)

        # Orchestrator Agent
        orchestrator_config = ClangTidyAgentConfig(
            agent_name="clang_tidy_orchestrator",
            agent_type=ClangTidyAgentType.ORCHESTRATOR,
            system_prompt="You are a Clang-Tidy pipeline orchestration expert.",
            enable_archon_integration=True,
            validation_level=ValidationLevel.STRICT,
            clang_tidy_validation_level=ClangTidyValidationLevel.PRODUCTION
        )
        agents["orchestrator"] = self.create_clang_tidy_agent(orchestrator_config)

        return agents

    def _get_specialized_prompt(self, config: ClangTidyAgentConfig) -> str:
        """Get specialized system prompt based on agent type."""
        base_prompt = "You are a specialized Clang-Tidy AI agent for C++ code quality analysis."

        if config.agent_type == ClangTidyAgentType.ISSUE_DISCOVERER:
            return base_prompt + " Focus on discovering and categorizing code quality issues."
        elif config.agent_type == ClangTidyAgentType.FIX_STRATEGIST:
            return base_prompt + " Specialize in planning safe and effective fix strategies."
        elif config.agent_type == ClangTidyAgentType.FIX_APPLICATOR:
            return base_prompt + " Expert in applying automated fixes with high confidence."
        elif config.agent_type == ClangTidyAgentType.VALIDATOR:
            return base_prompt + " Focus on validating fixes and ensuring code quality improvements."
        elif config.agent_type == ClangTidyAgentType.ORCHESTRATOR:
            return base_prompt + " Coordinate the complete analysis and fix pipeline."
        else:
            return base_prompt

    def _get_tools_for_config(self, config: ClangTidyAgentConfig) -> List[Callable]:
        """Get appropriate tools based on configuration."""
        tools = []

        # Add mock tools for testing
        async def mock_analysis_tool():
            return {"issues": [], "status": "completed"}

        async def mock_fix_tool():
            return {"fixes": [], "status": "applied"}

        tools.append(mock_analysis_tool)

        if config.enable_auto_fix:
            tools.append(mock_fix_tool)

        return tools

    def _no_critical_errors(self, output: Any) -> bool:
        """Check if output contains no critical errors."""
        if isinstance(output, list):
            return not any(
                item.get("severity") == "error" for item in output
                if isinstance(item, dict)
            )
        return True

    async def validate_clang_tidy_pipeline(
        self,
        file_path: str,
        checks: str = "*"
    ) -> Dict[str, ValidationResult]:
        """Validate complete Clang-Tidy analysis pipeline."""
        results = {}

        # Input validation
        input_validator = ClangTidyInputValidator(validation_level=ValidationLevel.STRICT)
        results["file_validation"] = await input_validator.validate_source_file(file_path)
        results["config_validation"] = await input_validator.validate_clang_tidy_config({
            "checks": checks,
            "warnings_as_errors": True
        })

        # Backend validation
        backend_validator = ClangTidyBackendValidator(validation_level=ValidationLevel.STRICT)

        # Mock cache and archon data for validation
        mock_cache = {
            "analysis_1": {"issues": [{"severity": "warning", "check": "test"}]},
            "analysis_2": {"issues": []}
        }
        mock_archon = {
            "project_id": "test_project",
            "task_id": "test_task",
            "status": "doing"
        }

        results["cache_validation"] = await backend_validator.validate_analysis_cache(mock_cache)
        results["archon_validation"] = await backend_validator.validate_archon_integration(mock_archon)

        return results


# Module-level factory instance
_clang_tidy_factory: Optional[ClangTidyAgentFactory] = None


def get_clang_tidy_factory() -> ClangTidyAgentFactory:
    """Get or create the global Clang-Tidy agent factory."""
    global _clang_tidy_factory
    if _clang_tidy_factory is None:
        _clang_tidy_factory = ClangTidyAgentFactory()
    return _clang_tidy_factory


async def create_and_validate_clang_tidy_agents() -> Dict[str, ValidatedAgent]:
    """Create standard Clang-Tidy agents and validate them."""
    factory = get_clang_tidy_factory()
    agents = factory.create_standard_clang_tidy_agents()

    # Validate all agents
    validation_results = await factory.validate_all_agents()

    # Log validation results
    for name, result in validation_results.items():
        if not result.is_valid:
            logger.error(f"Clang-Tidy agent {name} validation failed: {result.errors}")
        elif result.has_warnings:
            logger.warning(f"Clang-Tidy agent {name} has warnings: {result.warnings}")
        else:
            logger.info(f"Clang-Tidy agent {name} validated successfully")

    return agents