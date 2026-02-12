"""
Blitzfire Code Agent Factory with comprehensive validation and optimization focus.

This factory creates validated Blitzfire agents with specialized validation rules
for C++ optimization, performance analysis, and assembly generation.
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
                    self.data = {"mock": "blitzfire_result", "prompt": prompt}
            return Result()

from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic.types import conint, confloat

try:
    from .providers import get_llm_model
    from .dependencies import BlitzfireDependencies
    from .models import (
        BlitzfireResponse, AnalysisResult, OptimizationStrategy,
        AssemblyComparison, BenchmarkResult, Architecture, OptimizationMode
    )
    from .prompts import get_system_prompt
    from .tools import (
        analyze_code, generate_optimizations, validate_assembly,
        benchmark_performance, hft_audit, interactive_chat
    )
except ImportError:
    # Mock imports for testing
    def get_llm_model():
        return lambda: "mock_model"

    def get_system_prompt():
        return "You are a Blitzfire optimization agent for C++ code."

    class BlitzfireDependencies:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    class BlitzfireResponse(BaseModel):
        optimization_suggestions: List[str] = Field(default_factory=list)
        performance_impact: str = "unknown"

    class AnalysisResult(BaseModel):
        complexity_score: float = 0.0
        optimization_opportunities: List[str] = Field(default_factory=list)

    # Mock tools
    async def analyze_code(*args, **kwargs):
        return {"analysis": "mock"}

    async def generate_optimizations(*args, **kwargs):
        return {"optimizations": "mock"}

    async def validate_assembly(*args, **kwargs):
        return {"assembly": "mock"}

    async def benchmark_performance(*args, **kwargs):
        return {"benchmark": "mock"}

    async def hft_audit(*args, **kwargs):
        return {"audit": "mock"}

    async def interactive_chat(*args, **kwargs):
        return {"chat": "mock"}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BlitzfireAgentType(str, Enum):
    """Types of Blitzfire agents."""
    OPTIMIZER = "optimizer"           # Code optimization specialist
    ANALYZER = "analyzer"            # Performance analysis expert
    BENCHMARKER = "benchmarker"      # Benchmarking and validation
    HFT_SPECIALIST = "hft_specialist" # High-frequency trading optimization
    ASSEMBLY_EXPERT = "assembly_expert" # Assembly generation and validation
    INTERACTIVE_TUTOR = "interactive_tutor" # Educational interaction


class BlitzfireValidationLevel(str, Enum):
    """Blitzfire-specific validation levels."""
    PERFORMANCE_CRITICAL = "performance_critical"  # Maximum validation for HFT
    PRODUCTION = "production"                      # Standard production validation
    DEVELOPMENT = "development"                    # Development-friendly validation
    EXPERIMENTAL = "experimental"                  # Minimal validation for experimentation


class BlitzfireInputValidator(InputValidator):
    """Specialized input validator for Blitzfire optimization tasks."""

    async def validate_cpp_code(self, code: str) -> ValidationResult:
        """Validate C++ code input for optimization."""
        result = ValidationResult(
            is_valid=True,
            validation_type="cpp_code_validation"
        )

        try:
            # Check if it's actually C++ code
            cpp_indicators = [
                '#include', 'std::', 'namespace', 'class ', 'template<',
                'int main', 'void ', 'const ', 'auto ', 'for (', 'while ('
            ]

            if not any(indicator in code for indicator in cpp_indicators):
                result.add_error("Input does not appear to be C++ code")

            # Check for dangerous patterns that shouldn't be optimized
            dangerous_patterns = [
                r'system\s*\(',      # system calls
                r'exec[vl]?\s*\(',   # exec family
                r'eval\s*\(',        # eval
                r'#include\s*<windows\.h>', # Windows-specific code warning
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    result.add_warning(f"Potentially dangerous pattern detected: {pattern}")

            # Check code size
            if len(code) > 100000:  # 100KB limit
                result.add_warning("Large code size may impact optimization performance")
            elif len(code) < 50:
                result.add_warning("Very small code snippet may not benefit from optimization")

            # Check for optimization opportunities
            optimization_hints = [
                ('vector', 'SIMD optimization opportunities'),
                ('loop', 'Loop optimization opportunities'),
                ('malloc|new', 'Memory allocation optimization'),
                ('printf|cout', 'I/O optimization opportunities'),
            ]

            detected_opportunities = []
            for pattern, opportunity in optimization_hints:
                if re.search(pattern, code, re.IGNORECASE):
                    detected_opportunities.append(opportunity)

            result.metadata["code_size"] = len(code)
            result.metadata["line_count"] = code.count('\n') + 1
            result.metadata["optimization_opportunities"] = detected_opportunities

        except Exception as e:
            result.add_error(f"C++ code validation failed: {str(e)}")

        return result

    async def validate_optimization_target(self, target: str) -> ValidationResult:
        """Validate optimization target specification."""
        result = ValidationResult(
            is_valid=True,
            validation_type="optimization_target"
        )

        valid_targets = [
            'performance', 'memory', 'latency', 'throughput', 'cache_efficiency',
            'branch_prediction', 'vectorization', 'parallelization', 'hft_latency'
        ]

        if target.lower() not in valid_targets:
            result.add_error(f"Invalid optimization target: {target}. Valid targets: {valid_targets}")

        # Add metadata about optimization focus
        if target.lower() in ['hft_latency', 'latency']:
            result.metadata["optimization_class"] = "ultra_low_latency"
        elif target.lower() in ['performance', 'throughput']:
            result.metadata["optimization_class"] = "high_performance"
        else:
            result.metadata["optimization_class"] = "balanced"

        return result

    async def validate_architecture_spec(self, arch: str) -> ValidationResult:
        """Validate target architecture specification."""
        result = ValidationResult(
            is_valid=True,
            validation_type="architecture_spec"
        )

        supported_architectures = [
            'x86_64', 'arm64', 'armv7', 'riscv64', 'generic'
        ]

        if arch.lower() not in [a.lower() for a in supported_architectures]:
            result.add_warning(f"Unsupported architecture: {arch}. May use generic optimizations.")

        # Add optimization capabilities based on architecture
        arch_capabilities = {
            'x86_64': ['SSE', 'AVX', 'AVX2', 'AVX512'],
            'arm64': ['NEON', 'SVE'],
            'armv7': ['NEON'],
            'riscv64': ['Vector Extension'],
            'generic': ['Standard optimizations']
        }

        result.metadata["architecture"] = arch
        result.metadata["capabilities"] = arch_capabilities.get(arch.lower(), [])

        return result


class BlitzfireOutputValidator(OutputValidator):
    """Specialized output validator for Blitzfire optimization results."""

    async def validate_optimization_result(self, result: Dict[str, Any]) -> ValidationResult:
        """Validate optimization analysis results."""
        validation = ValidationResult(
            is_valid=True,
            validation_type="optimization_result"
        )

        required_fields = [
            "optimization_suggestions", "performance_impact", "complexity_analysis"
        ]

        for field in required_fields:
            if field not in result:
                validation.add_error(f"Missing required field: {field}")

        # Validate optimization suggestions
        if "optimization_suggestions" in result:
            suggestions = result["optimization_suggestions"]
            if not isinstance(suggestions, list):
                validation.add_error("optimization_suggestions must be a list")
            elif len(suggestions) == 0:
                validation.add_warning("No optimization suggestions provided")

        # Validate performance impact
        if "performance_impact" in result:
            impact = result["performance_impact"]
            if isinstance(impact, str):
                # Check for performance improvement indicators
                improvement_indicators = ['faster', 'improved', 'optimized', 'reduced', 'enhanced']
                if not any(indicator in impact.lower() for indicator in improvement_indicators):
                    validation.add_warning("Performance impact statement unclear")

        # Validate benchmark results if present
        if "benchmark_results" in result:
            benchmark = result["benchmark_results"]
            if isinstance(benchmark, dict):
                if "execution_time" in benchmark:
                    try:
                        exec_time = float(benchmark["execution_time"])
                        if exec_time <= 0:
                            validation.add_error("Invalid execution time")
                        validation.metadata["execution_time"] = exec_time
                    except (ValueError, TypeError):
                        validation.add_error("Execution time must be a number")

        validation.metadata["suggestions_count"] = len(result.get("optimization_suggestions", []))

        return validation

    async def validate_assembly_output(self, assembly: str) -> ValidationResult:
        """Validate generated assembly code."""
        result = ValidationResult(
            is_valid=True,
            validation_type="assembly_validation"
        )

        if not assembly or len(assembly.strip()) == 0:
            result.add_error("Empty assembly output")
            return result

        # Check for valid assembly patterns
        assembly_patterns = [
            r'mov\s+', r'add\s+', r'sub\s+', r'jmp\s+', r'call\s+',
            r'push\s+', r'pop\s+', r'ret\s*$', r'\.text', r'\.data'
        ]

        pattern_matches = sum(1 for pattern in assembly_patterns
                            if re.search(pattern, assembly, re.MULTILINE | re.IGNORECASE))

        if pattern_matches == 0:
            result.add_warning("Output doesn't appear to contain valid assembly code")

        # Check for optimization indicators in assembly
        optimization_indicators = [
            ('vectorized', r'xmm\d+|ymm\d+|zmm\d+'),  # SIMD registers
            ('loop_unrolled', r'(\w+):\s*.*\1'),        # Loop labels
            ('inlined', r'call.*inline'),                # Inline calls
        ]

        optimizations_detected = []
        for opt_name, pattern in optimization_indicators:
            if re.search(pattern, assembly, re.IGNORECASE):
                optimizations_detected.append(opt_name)

        result.metadata["assembly_size"] = len(assembly)
        result.metadata["line_count"] = assembly.count('\n') + 1
        result.metadata["optimizations_detected"] = optimizations_detected

        return result


class BlitzfireBackendValidator(BackendValidator):
    """Specialized backend validator for Blitzfire operations."""

    async def validate_optimization_cache(self, cache: Dict[str, Any]) -> ValidationResult:
        """Validate optimization result cache."""
        result = ValidationResult(
            is_valid=True,
            validation_type="optimization_cache"
        )

        # Check cache structure
        for key, value in cache.items():
            if not isinstance(key, str):
                result.add_error(f"Cache key must be string: {type(key)}")

            # Validate cached optimization results
            if isinstance(value, dict) and "optimization_suggestions" in value:
                if not isinstance(value["optimization_suggestions"], list):
                    result.add_error(f"Invalid cached optimization format for key: {key}")

        # Check cache size and performance
        cache_size = len(json.dumps(cache, default=str))
        if cache_size > 50 * 1024 * 1024:  # 50MB limit for optimization cache
            result.add_warning(f"Large optimization cache size: {cache_size / 1024 / 1024:.2f}MB")

        result.metadata["cache_entries"] = len(cache)
        result.metadata["cache_size_mb"] = cache_size / 1024 / 1024

        return result

    async def validate_performance_metrics(self, metrics: Dict[str, Any]) -> ValidationResult:
        """Validate performance measurement data."""
        result = ValidationResult(
            is_valid=True,
            validation_type="performance_metrics"
        )

        required_metrics = ["execution_time", "memory_usage"]
        for metric in required_metrics:
            if metric not in metrics:
                result.add_warning(f"Missing performance metric: {metric}")

        # Validate execution time
        if "execution_time" in metrics:
            try:
                exec_time = float(metrics["execution_time"])
                if exec_time <= 0:
                    result.add_error("Execution time must be positive")
                elif exec_time > 3600:  # 1 hour limit
                    result.add_warning("Very long execution time detected")
                result.metadata["execution_time"] = exec_time
            except (ValueError, TypeError):
                result.add_error("Invalid execution time format")

        # Validate memory usage
        if "memory_usage" in metrics:
            try:
                memory = float(metrics["memory_usage"])
                if memory < 0:
                    result.add_error("Memory usage cannot be negative")
                result.metadata["memory_usage_mb"] = memory / 1024 / 1024
            except (ValueError, TypeError):
                result.add_error("Invalid memory usage format")

        return result


class BlitzfireAgentConfig(AgentFactoryConfig):
    """Extended configuration for Blitzfire agents."""

    agent_type: BlitzfireAgentType
    optimization_target: str = Field(default="performance", description="Primary optimization target")
    target_architecture: str = Field(default="x86_64", description="Target CPU architecture")
    hft_mode: bool = Field(default=False, description="Enable high-frequency trading optimizations")
    enable_assembly_analysis: bool = Field(default=True, description="Enable assembly code analysis")
    enable_benchmarking: bool = Field(default=True, description="Enable performance benchmarking")
    enable_interactive_mode: bool = Field(default=False, description="Enable interactive tutoring")
    blitzfire_validation_level: BlitzfireValidationLevel = Field(
        default=BlitzfireValidationLevel.PRODUCTION,
        description="Blitzfire-specific validation level"
    )

    @field_validator('optimization_target')
    @classmethod
    def validate_optimization_target(cls, v: str) -> str:
        """Validate optimization target."""
        valid_targets = [
            'performance', 'memory', 'latency', 'throughput', 'cache_efficiency',
            'branch_prediction', 'vectorization', 'parallelization', 'hft_latency'
        ]
        if v.lower() not in valid_targets:
            raise ValueError(f"Invalid optimization target. Must be one of: {valid_targets}")
        return v.lower()

    @field_validator('target_architecture')
    @classmethod
    def validate_architecture(cls, v: str) -> str:
        """Validate target architecture."""
        supported_archs = ['x86_64', 'arm64', 'armv7', 'riscv64', 'generic']
        if v.lower() not in supported_archs:
            raise ValueError(f"Unsupported architecture. Supported: {supported_archs}")
        return v.lower()


class BlitzfireAgentFactory(AgentFactory):
    """Factory for creating specialized Blitzfire optimization agents."""

    def __init__(self):
        super().__init__(default_validation_level=ValidationLevel.STRICT)
        self.blitzfire_configs: Dict[str, BlitzfireAgentConfig] = {}

    def create_blitzfire_agent(
        self,
        config: BlitzfireAgentConfig,
        custom_tools: Optional[List[Callable]] = None
    ) -> ValidatedAgent:
        """Create a specialized Blitzfire agent with optimization-focused validation."""

        # Create custom validators with Blitzfire-specific rules
        input_validator = BlitzfireInputValidator(
            validation_level=config.validation_level,
            custom_rules={
                "validate_cpp": lambda code: self._validate_cpp_code_sync(code),
                "validate_size": lambda code: len(str(code)) < 1000000,
                "validate_optimization_safe": lambda code: not any(
                    dangerous in str(code).lower()
                    for dangerous in ['system(', 'exec(', 'eval(']
                )
            }
        )

        output_validator = BlitzfireOutputValidator(
            validation_level=config.validation_level,
            custom_rules={
                "validate_optimization": lambda out: "optimization" in str(out).lower(),
                "validate_performance": lambda out: self._validate_performance_metrics(out),
                "validate_completeness": lambda out: isinstance(out, dict) and len(out) > 0
            }
        )

        backend_validator = BlitzfireBackendValidator(
            validation_level=config.validation_level,
            custom_rules={
                "required_keys": ["optimization_cache", "performance_metrics", "session_data"]
            }
        )

        # Determine system prompt based on agent type
        system_prompt = self._get_specialized_prompt(config)

        # Create the Pydantic AI agent
        agent = Agent(
            get_llm_model(),
            deps_type=BlitzfireDependencies,
            system_prompt=system_prompt
        )

        # Register tools based on configuration
        tools = self._get_tools_for_config(config)
        if custom_tools:
            tools.extend(custom_tools)

        for tool in tools:
            agent.tool(tool)

        # Create validated agent wrapper
        validated_agent = ValidatedAgent(
            agent=agent,
            config=config,
            input_validator=input_validator,
            output_validator=output_validator,
            backend_validator=backend_validator
        )

        # Store Blitzfire-specific config
        self.blitzfire_configs[config.agent_name] = config
        self._agent_registry[config.agent_name] = validated_agent

        logger.info(f"Created Blitzfire agent: {config.agent_name} (type: {config.agent_type})")

        return validated_agent

    def create_standard_blitzfire_agents(self) -> Dict[str, ValidatedAgent]:
        """Create the standard set of Blitzfire optimization agents."""
        agents = {}

        # Optimizer agent
        optimizer_config = BlitzfireAgentConfig(
            agent_name="blitzfire_optimizer",
            agent_type=BlitzfireAgentType.OPTIMIZER,
            system_prompt="You are a Blitzfire C++ optimization specialist.",
            optimization_target="performance",
            validation_level=ValidationLevel.STRICT,
            blitzfire_validation_level=BlitzfireValidationLevel.PRODUCTION
        )
        agents["optimizer"] = self.create_blitzfire_agent(optimizer_config)

        # Analyzer agent
        analyzer_config = BlitzfireAgentConfig(
            agent_name="blitzfire_analyzer",
            agent_type=BlitzfireAgentType.ANALYZER,
            system_prompt="You are a Blitzfire performance analysis expert.",
            optimization_target="cache_efficiency",
            validation_level=ValidationLevel.STRICT,
            blitzfire_validation_level=BlitzfireValidationLevel.PRODUCTION
        )
        agents["analyzer"] = self.create_blitzfire_agent(analyzer_config)

        # HFT specialist agent
        hft_config = BlitzfireAgentConfig(
            agent_name="blitzfire_hft_specialist",
            agent_type=BlitzfireAgentType.HFT_SPECIALIST,
            system_prompt="You are a Blitzfire high-frequency trading optimization specialist.",
            optimization_target="hft_latency",
            hft_mode=True,
            validation_level=ValidationLevel.STRICT,
            blitzfire_validation_level=BlitzfireValidationLevel.PERFORMANCE_CRITICAL
        )
        agents["hft_specialist"] = self.create_blitzfire_agent(hft_config)

        # Assembly expert agent
        assembly_config = BlitzfireAgentConfig(
            agent_name="blitzfire_assembly_expert",
            agent_type=BlitzfireAgentType.ASSEMBLY_EXPERT,
            system_prompt="You are a Blitzfire assembly code generation and analysis expert.",
            optimization_target="vectorization",
            enable_assembly_analysis=True,
            validation_level=ValidationLevel.STRICT,
            blitzfire_validation_level=BlitzfireValidationLevel.PRODUCTION
        )
        agents["assembly_expert"] = self.create_blitzfire_agent(assembly_config)

        # Interactive tutor agent
        tutor_config = BlitzfireAgentConfig(
            agent_name="blitzfire_tutor",
            agent_type=BlitzfireAgentType.INTERACTIVE_TUTOR,
            system_prompt="You are a Blitzfire interactive optimization tutor.",
            optimization_target="performance",
            enable_interactive_mode=True,
            validation_level=ValidationLevel.MODERATE,
            blitzfire_validation_level=BlitzfireValidationLevel.DEVELOPMENT
        )
        agents["tutor"] = self.create_blitzfire_agent(tutor_config)

        return agents

    def _get_specialized_prompt(self, config: BlitzfireAgentConfig) -> str:
        """Get specialized system prompt based on agent type."""
        if config.agent_type == BlitzfireAgentType.OPTIMIZER:
            return get_system_prompt() + "\n\nFocus on generating specific, actionable C++ optimization recommendations."
        elif config.agent_type == BlitzfireAgentType.HFT_SPECIALIST:
            return get_system_prompt() + "\n\nSpecialize in ultra-low latency optimizations for high-frequency trading systems."
        elif config.agent_type == BlitzfireAgentType.ASSEMBLY_EXPERT:
            return get_system_prompt() + "\n\nExpertise in assembly code generation, analysis, and SIMD optimization."
        elif config.agent_type == BlitzfireAgentType.INTERACTIVE_TUTOR:
            return get_system_prompt() + "\n\nProvide educational, step-by-step optimization guidance."
        else:
            return get_system_prompt()

    def _get_tools_for_config(self, config: BlitzfireAgentConfig) -> List[Callable]:
        """Get appropriate tools based on configuration."""
        tools = [analyze_code, generate_optimizations]

        if config.enable_assembly_analysis:
            tools.append(validate_assembly)

        if config.enable_benchmarking:
            tools.append(benchmark_performance)

        if config.hft_mode:
            tools.append(hft_audit)

        if config.enable_interactive_mode:
            tools.append(interactive_chat)

        return tools

    def _validate_cpp_code_sync(self, code: str) -> bool:
        """Synchronous C++ code validation for custom rules."""
        return isinstance(code, str) and any(
            indicator in code for indicator in ['#include', 'std::', 'int main']
        )

    def _validate_performance_metrics(self, output: Any) -> bool:
        """Validate performance metrics in output."""
        if isinstance(output, dict):
            return any(
                key in output for key in ['execution_time', 'performance_impact', 'speedup']
            )
        return "performance" in str(output).lower()

    async def validate_blitzfire_pipeline(
        self,
        code: str,
        optimization_target: str = "performance"
    ) -> Dict[str, ValidationResult]:
        """Validate complete Blitzfire optimization pipeline."""
        results = {}

        # Input validation
        input_validator = BlitzfireInputValidator(validation_level=ValidationLevel.STRICT)
        results["code_validation"] = await input_validator.validate_cpp_code(code)
        results["target_validation"] = await input_validator.validate_optimization_target(optimization_target)

        # Backend validation
        backend_validator = BlitzfireBackendValidator(validation_level=ValidationLevel.STRICT)

        # Mock cache and metrics for validation
        mock_cache = {
            "optimization_1": {"optimization_suggestions": ["Use SIMD", "Loop unrolling"]},
            "optimization_2": {"optimization_suggestions": ["Cache optimization"]}
        }
        mock_metrics = {
            "execution_time": 0.005,
            "memory_usage": 1024000,
            "cpu_usage": 45.0
        }

        results["cache_validation"] = await backend_validator.validate_optimization_cache(mock_cache)
        results["metrics_validation"] = await backend_validator.validate_performance_metrics(mock_metrics)

        return results


# Module-level factory instance
_blitzfire_factory: Optional[BlitzfireAgentFactory] = None


def get_blitzfire_factory() -> BlitzfireAgentFactory:
    """Get or create the global Blitzfire agent factory."""
    global _blitzfire_factory
    if _blitzfire_factory is None:
        _blitzfire_factory = BlitzfireAgentFactory()
    return _blitzfire_factory


async def create_and_validate_blitzfire_agents() -> Dict[str, ValidatedAgent]:
    """Create standard Blitzfire agents and validate them."""
    factory = get_blitzfire_factory()
    agents = factory.create_standard_blitzfire_agents()

    # Validate all agents
    validation_results = await factory.validate_all_agents()

    # Log validation results
    for name, result in validation_results.items():
        if not result.is_valid:
            logger.error(f"Blitzfire agent {name} validation failed: {result.errors}")
        elif result.has_warnings:
            logger.warning(f"Blitzfire agent {name} has warnings: {result.warnings}")
        else:
            logger.info(f"Blitzfire agent {name} validated successfully")

    return agents