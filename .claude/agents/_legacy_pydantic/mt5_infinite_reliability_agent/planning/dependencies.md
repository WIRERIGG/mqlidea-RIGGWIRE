# MT5 Infinite Reliability Agent - Dependency Configuration

**Agent**: mt5_infinite_reliability_agent
**Generated**: 2025-12-20
**Model**: Claude Opus 4.5 (claude-opus-4-5-20251101)

## Overview

This agent is self-contained with minimal external dependencies. All verification logic is implemented in Python tools. The only external dependency is the Anthropic API for LLM reasoning and proof generation.

## Philosophy

**Simplicity First**: This agent uses local Python-based verification tools with no external API dependencies (beyond the LLM). Configuration is minimal - just the LLM API key and local file paths.

## Configuration Files

### 1. settings.py - Environment Configuration

```python
"""
Configuration management for MT5 Infinite Reliability Agent.
Minimal settings - only LLM configuration required.
"""

import os
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM Configuration (Anthropic Claude only)
    llm_provider: Literal["anthropic"] = Field(
        default="anthropic",
        description="LLM provider (fixed to Anthropic)"
    )
    anthropic_api_key: str = Field(
        ...,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude"
    )
    llm_model: str = Field(
        default="claude-opus-4-5-20251101",
        description="Claude model for mathematical reasoning"
    )

    # Optional: MT5 Installation Path (for future compiler integration)
    mt5_terminal_path: Optional[str] = Field(
        None,
        description="Path to MT5 terminal installation (optional)"
    )

    # Application Configuration
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    debug: bool = Field(
        default=False,
        description="Debug mode"
    )

    # Analysis Configuration
    default_proof_level: Literal["basic", "detailed", "comprehensive"] = Field(
        default="detailed",
        description="Default proof detail level"
    )
    max_code_size_kb: int = Field(
        default=500,
        description="Maximum MQL5 file size to process (KB)"
    )
    analysis_timeout_seconds: int = Field(
        default=300,
        description="Maximum time for analysis operation"
    )

    # Verification Settings
    enable_atomic_rollback: bool = Field(
        default=True,
        description="Enable atomic transformation with rollback"
    )
    max_transformations: int = Field(
        default=100,
        description="Maximum number of transformations per session"
    )

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Ensure API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError(
                "ANTHROPIC_API_KEY cannot be empty. "
                "Set it in your .env file or environment."
            )
        return v

    @field_validator("max_code_size_kb")
    @classmethod
    def validate_code_size(cls, v):
        """Ensure reasonable code size limit."""
        if v < 1 or v > 10000:
            raise ValueError("max_code_size_kb must be between 1 and 10000")
        return v


def load_settings() -> Settings:
    """Load settings with proper error handling."""
    try:
        return Settings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "anthropic_api_key" in str(e).lower():
            error_msg += "\nMake sure to set ANTHROPIC_API_KEY in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance
settings = load_settings()
```

### 2. providers.py - Model Provider Configuration

```python
"""
Model provider configuration for MT5 Infinite Reliability Agent.
Fixed to Anthropic Claude Opus 4.5 for superior mathematical reasoning.
"""

from pydantic_ai.models.anthropic import AnthropicModel
from .settings import settings


def get_llm_model() -> AnthropicModel:
    """
    Get Claude Opus 4.5 model for mathematical reasoning and proof generation.

    Returns:
        Configured Anthropic model instance
    """
    return AnthropicModel(
        settings.llm_model,
        api_key=settings.anthropic_api_key
    )


# No fallback model needed - Claude Opus 4.5 is the best choice for this task
# If needed in the future, fallback to Claude Sonnet 4.5:
# def get_fallback_model() -> AnthropicModel:
#     return AnthropicModel(
#         "claude-sonnet-4-5-20250929",
#         api_key=settings.anthropic_api_key
#     )
```

### 3. dependencies.py - Agent Dependencies

```python
"""
Dependencies for MT5 Infinite Reliability Agent.
Simple dataclass for file paths and analysis configuration.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Literal
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class AgentDependencies:
    """
    Dependencies injected into agent runtime context.

    Minimal configuration - just paths and analysis options.
    All verification logic is in Python tools, not external services.
    """

    # Input/Output Paths
    source_code_path: Optional[Path] = None
    output_path: Optional[Path] = None

    # Analysis Configuration
    verification_depth: Literal["basic", "standard", "comprehensive"] = "standard"
    analysis_mode: Literal["analyze", "fix", "certify", "full"] = "full"
    dimensions: List[str] = field(
        default_factory=lambda: ["complexity", "memory", "security", "robustness"]
    )

    # Transformation Settings
    auto_apply: bool = True
    enable_rollback: bool = True

    # Proof Generation
    proof_level: Literal["basic", "detailed", "comprehensive"] = "detailed"

    # Session Context
    session_id: Optional[str] = None
    user_id: Optional[str] = None

    # Configuration Overrides
    max_code_size_kb: Optional[int] = None
    timeout_seconds: Optional[int] = None
    debug: bool = False

    # Internal State (not for user configuration)
    _snapshot_stack: List[str] = field(default_factory=list, init=False, repr=False)
    _transformation_count: int = field(default=0, init=False, repr=False)

    def __post_init__(self):
        """Validate paths and configuration."""
        if self.source_code_path:
            self.source_code_path = Path(self.source_code_path)
            if not self.source_code_path.exists():
                logger.warning(f"Source code path does not exist: {self.source_code_path}")

        if self.output_path:
            self.output_path = Path(self.output_path)
            # Create parent directory if it doesn't exist
            self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def validate_dimensions(self) -> bool:
        """Validate analysis dimensions are supported."""
        valid_dimensions = {
            "complexity", "memory", "security", "robustness",
            "temporal", "concurrency", "probabilistic", "adaptive"
        }
        for dim in self.dimensions:
            if dim not in valid_dimensions:
                logger.error(f"Invalid dimension: {dim}")
                return False
        return True

    def add_snapshot(self, code_snapshot: str) -> None:
        """Add code snapshot for rollback capability."""
        if self.enable_rollback:
            self._snapshot_stack.append(code_snapshot)
            logger.debug(f"Snapshot added (stack size: {len(self._snapshot_stack)})")

    def rollback(self) -> Optional[str]:
        """Rollback to previous code state."""
        if self._snapshot_stack:
            snapshot = self._snapshot_stack.pop()
            logger.info("Rolled back to previous snapshot")
            return snapshot
        logger.warning("No snapshots available for rollback")
        return None

    def increment_transformation_count(self) -> int:
        """Track number of transformations applied."""
        self._transformation_count += 1
        return self._transformation_count

    @classmethod
    def from_settings(cls, settings, **kwargs):
        """
        Create dependencies from settings with overrides.

        Args:
            settings: Settings instance
            **kwargs: Override values

        Returns:
            Configured AgentDependencies instance
        """
        return cls(
            verification_depth=kwargs.get("verification_depth", "standard"),
            proof_level=kwargs.get("proof_level", settings.default_proof_level),
            max_code_size_kb=kwargs.get("max_code_size_kb", settings.max_code_size_kb),
            timeout_seconds=kwargs.get("timeout_seconds", settings.analysis_timeout_seconds),
            enable_rollback=kwargs.get("enable_rollback", settings.enable_atomic_rollback),
            debug=kwargs.get("debug", settings.debug),
            **{k: v for k, v in kwargs.items()
               if k not in [
                   "verification_depth", "proof_level", "max_code_size_kb",
                   "timeout_seconds", "enable_rollback", "debug"
               ]}
        )

    def to_dict(self) -> dict:
        """Export configuration as dictionary."""
        return {
            "source_code_path": str(self.source_code_path) if self.source_code_path else None,
            "output_path": str(self.output_path) if self.output_path else None,
            "verification_depth": self.verification_depth,
            "analysis_mode": self.analysis_mode,
            "dimensions": self.dimensions,
            "auto_apply": self.auto_apply,
            "enable_rollback": self.enable_rollback,
            "proof_level": self.proof_level,
            "session_id": self.session_id,
            "transformation_count": self._transformation_count,
        }
```

### 4. agent.py - Agent Initialization

```python
"""
MT5 Infinite Reliability Agent - Pydantic AI Agent Implementation
Analyzes MQL5 code for safety issues and generates verified fixes with mathematical proofs.
"""

import logging
from typing import Optional
from pydantic_ai import Agent

from .providers import get_llm_model
from .dependencies import AgentDependencies
from .settings import settings

logger = logging.getLogger(__name__)

# System prompt (will be provided by prompt-engineer subagent)
SYSTEM_PROMPT = """
You are the MT5 Infinite Reliability Agent, an expert in MQL5/MT5 code analysis and verification.

Your mission: Analyze MQL5 trading code for safety issues, generate verified fixes with
mathematical proofs, and produce certified refactored code.

Core capabilities:
1. Multi-dimensional code analysis (complexity, memory safety, security, robustness)
2. Automatic fix generation with atomic transformations
3. Verification with pre/post-condition validation
4. Certificate generation with proof chains and audit trails

You use Python-based verification tools and mathematical reasoning to ensure code correctness.
Every transformation must be justified with a proof, and all changes are atomic with rollback capability.

[Detailed prompt will be provided by prompt-engineer subagent]
"""

# Initialize the agent with Claude Opus 4.5
agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT,
    retries=2  # Conservative retries for expensive Opus 4.5 calls
)

logger.info("MT5 Infinite Reliability Agent initialized with Claude Opus 4.5")

# Tools will be registered by tool-integrator subagent:
# - mql5_parser: Parse MQL5 code and generate AST
# - static_analyzer: Detect issues across multiple dimensions
# - code_transformer: Apply verified transformations
# - verifier: Validate transformations maintain correctness
# - certificate_generator: Create proof chains and certificates


# Convenience functions for agent usage
async def analyze_mql5_code(
    code: str,
    mode: str = "full",
    proof_level: str = "detailed",
    **dependency_overrides
) -> dict:
    """
    Analyze MQL5 code and optionally fix issues.

    Args:
        code: MQL5 source code to analyze
        mode: "analyze", "fix", "certify", or "full"
        proof_level: "basic", "detailed", or "comprehensive"
        **dependency_overrides: Override default dependencies

    Returns:
        Analysis results with fixes, proofs, and certificate
    """
    deps = AgentDependencies.from_settings(
        settings,
        analysis_mode=mode,
        proof_level=proof_level,
        **dependency_overrides
    )

    # Add initial code snapshot for rollback
    deps.add_snapshot(code)

    try:
        result = await agent.run(
            f"Analyze this MQL5 code in {mode} mode:\n\n{code}",
            deps=deps
        )

        # Result should be structured JSON with analysis, transformations, and certificate
        return result.data

    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        # Attempt rollback
        original_code = deps.rollback()
        if original_code:
            logger.info("Rolled back to original code")
        raise


async def analyze_mql5_file(
    file_path: str,
    output_path: Optional[str] = None,
    **kwargs
) -> dict:
    """
    Analyze MQL5 file and optionally write fixed code to output.

    Args:
        file_path: Path to MQL5 source file
        output_path: Optional path to write fixed code
        **kwargs: Additional configuration options

    Returns:
        Analysis results with fixes, proofs, and certificate
    """
    from pathlib import Path

    source_path = Path(file_path)
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    # Read source code
    code = source_path.read_text(encoding="utf-8")

    # Set up dependencies
    deps = AgentDependencies.from_settings(
        settings,
        source_code_path=source_path,
        output_path=Path(output_path) if output_path else None,
        **kwargs
    )

    deps.add_snapshot(code)

    try:
        result = await agent.run(
            f"Analyze MQL5 file: {file_path}\n\nCode:\n{code}",
            deps=deps
        )

        # Write fixed code to output if specified
        if output_path and "refactored_code" in result.data:
            output_file = Path(output_path)
            output_file.write_text(result.data["refactored_code"], encoding="utf-8")
            logger.info(f"Fixed code written to: {output_path}")

        return result.data

    except Exception as e:
        logger.error(f"File analysis failed: {e}")
        original_code = deps.rollback()
        if original_code:
            logger.info("Rolled back to original code")
        raise


def create_agent_with_deps(**dependency_overrides) -> tuple[Agent, AgentDependencies]:
    """
    Create agent instance with custom dependencies.

    Args:
        **dependency_overrides: Custom dependency values

    Returns:
        Tuple of (agent, dependencies)
    """
    deps = AgentDependencies.from_settings(settings, **dependency_overrides)
    return agent, deps
```

## Environment Configuration

### .env.example

```bash
# ============================================================================
# MT5 Infinite Reliability Agent - Environment Configuration
# ============================================================================

# LLM Configuration (REQUIRED)
# ----------------------------------------
# Only Anthropic Claude is supported (best for mathematical reasoning)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Model selection (default: claude-opus-4-5-20251101)
LLM_MODEL=claude-opus-4-5-20251101

# Optional: MT5 Installation Path
# ----------------------------------------
# Path to MT5 terminal for future compiler integration
# MT5_TERMINAL_PATH=/path/to/MetaTrader5

# Application Settings
# ----------------------------------------
APP_ENV=development  # Options: development, staging, production
LOG_LEVEL=INFO       # Options: DEBUG, INFO, WARNING, ERROR
DEBUG=false

# Analysis Configuration
# ----------------------------------------
# Default proof detail level: basic, detailed, comprehensive
DEFAULT_PROOF_LEVEL=detailed

# Maximum MQL5 file size to process (KB)
MAX_CODE_SIZE_KB=500

# Maximum time for analysis operation (seconds)
ANALYSIS_TIMEOUT_SECONDS=300

# Verification Settings
# ----------------------------------------
# Enable atomic transformation with rollback
ENABLE_ATOMIC_ROLLBACK=true

# Maximum number of transformations per session
MAX_TRANSFORMATIONS=100
```

## Python Dependencies

### requirements.txt

```txt
# ============================================================================
# MT5 Infinite Reliability Agent - Python Dependencies
# ============================================================================

# Core Pydantic AI Framework
pydantic-ai>=0.1.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# LLM Provider (Anthropic only)
anthropic>=0.40.0

# Code Analysis and Parsing
# Note: tree-sitter-mql5 may not exist yet, will build custom parser
# tree-sitter>=0.20.0
# tree-sitter-mql5>=0.1.0  # If available

# Code Processing
regex>=2023.0.0
attrs>=23.0.0

# Cryptography for Certificate Generation
cryptography>=41.0.0
hashlib-extra>=1.0.0  # For Merkle tree hashing

# Async Utilities
asyncio>=3.4.3
aiofiles>=23.0.0

# Data Validation and Serialization
jsonschema>=4.20.0
pyyaml>=6.0.1

# Testing Framework
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Code Quality Tools
black>=23.0.0
ruff>=0.1.0
mypy>=1.7.0

# Logging and Monitoring
loguru>=0.7.0
rich>=13.7.0  # For beautiful console output

# Performance Profiling (development only)
memory-profiler>=0.61.0
```

## Directory Structure

```
dependencies/
├── __init__.py          # Package initialization
├── settings.py          # Environment configuration with BaseSettings
├── providers.py         # Claude Opus 4.5 model provider
├── dependencies.py      # AgentDependencies dataclass
├── agent.py            # Agent initialization and convenience functions
├── .env.example        # Environment variable template
└── requirements.txt    # Python dependencies
```

## Tool Dependencies

The agent requires these Python tools (to be built by tool-integrator):

### 1. mql5_parser
**Purpose**: Parse MQL5 code and generate AST
**Dependencies**: `regex`, `attrs`
**Interface**:
```python
async def parse_mql5(code: str) -> dict:
    """Returns AST structure with functions, variables, control flow"""
```

### 2. static_analyzer
**Purpose**: Detect issues across multiple dimensions
**Dependencies**: Internal metrics calculators
**Interface**:
```python
async def analyze_code(ast: dict, dimensions: List[str]) -> dict:
    """Returns issues with severity scores"""
```

### 3. code_transformer
**Purpose**: Apply verified transformations
**Dependencies**: Template engine, snapshot manager
**Interface**:
```python
async def apply_transformation(code: str, fix: dict) -> str:
    """Returns transformed code with rollback support"""
```

### 4. verifier
**Purpose**: Validate transformations
**Dependencies**: Pre/post-condition checker
**Interface**:
```python
async def verify_transformation(original: str, fixed: str, proof: str) -> bool:
    """Returns verification status"""
```

### 5. certificate_generator
**Purpose**: Create proof chains and certificates
**Dependencies**: `cryptography`, hash functions
**Interface**:
```python
async def generate_certificate(analysis: dict, transformations: List[dict]) -> dict:
    """Returns structured certificate with Merkle tree"""
```

## Configuration Patterns

### Minimal Usage (Defaults)
```python
from dependencies import settings, AgentDependencies

# Use all defaults
deps = AgentDependencies.from_settings(settings)
```

### Custom Analysis Configuration
```python
deps = AgentDependencies.from_settings(
    settings,
    verification_depth="comprehensive",
    proof_level="comprehensive",
    dimensions=["complexity", "memory", "security", "robustness", "temporal"]
)
```

### File-Based Workflow
```python
from dependencies.agent import analyze_mql5_file

result = await analyze_mql5_file(
    file_path="/path/to/expert_advisor.mq5",
    output_path="/path/to/fixed_expert_advisor.mq5",
    mode="full",
    proof_level="detailed"
)
```

## Security Considerations

### API Key Management
- Store ANTHROPIC_API_KEY in `.env` file (never commit)
- Validate key on startup (non-empty check)
- Use environment variables in production
- Rotate keys regularly

### File Access
- Validate file paths to prevent directory traversal
- Check file size limits before processing
- Use read-only access for source files
- Create output directories with proper permissions

### Code Safety
- Sandbox all MQL5 code execution (no eval/exec)
- Validate all transformations before applying
- Maintain rollback capability for every change
- Log all operations for audit trail

## Testing Configuration

### conftest.py
```python
import pytest
from unittest.mock import Mock
from pathlib import Path

@pytest.fixture
def test_settings():
    """Mock settings for testing."""
    return Mock(
        llm_provider="anthropic",
        anthropic_api_key="test-key-123",
        llm_model="claude-opus-4-5-20251101",
        default_proof_level="detailed",
        max_code_size_kb=500,
        analysis_timeout_seconds=300,
        enable_atomic_rollback=True,
        debug=True
    )

@pytest.fixture
def test_dependencies():
    """Test dependencies with minimal configuration."""
    from dependencies import AgentDependencies
    return AgentDependencies(
        verification_depth="basic",
        proof_level="basic",
        debug=True
    )

@pytest.fixture
def sample_mql5_code():
    """Sample MQL5 code for testing."""
    return """
    //+------------------------------------------------------------------+
    //| Expert initialization function                                   |
    //+------------------------------------------------------------------+
    int OnInit()
    {
        // Initialize EA
        return(INIT_SUCCEEDED);
    }
    """

@pytest.fixture
def test_agent(test_settings):
    """Test agent with mocked model."""
    from pydantic_ai import Agent
    from pydantic_ai.models.test import TestModel
    from dependencies import AgentDependencies

    return Agent(
        TestModel(),
        deps_type=AgentDependencies,
        system_prompt="Test agent for MQL5 analysis"
    )
```

## Quality Checklist

- [x] Minimal environment variables (only ANTHROPIC_API_KEY required)
- [x] Single model provider (Anthropic Claude Opus 4.5)
- [x] Simple AgentDependencies dataclass (no complex factories)
- [x] Type-safe dependency injection
- [x] File path validation and safety
- [x] Rollback capability implemented
- [x] Security measures documented
- [x] Testing configuration provided
- [x] No external API dependencies (except LLM)
- [x] Standard library focused (minimal third-party deps)

## Integration Notes

### For main_agent_reference (Main Claude Code)
- Use `agent.py` convenience functions for easy integration
- File-based workflow: `analyze_mql5_file(path, output_path)`
- Code-based workflow: `analyze_mql5_code(code, mode, proof_level)`

### For prompt-engineer
- Replace `SYSTEM_PROMPT` placeholder in `agent.py`
- Include details about 8D analysis framework
- Specify proof generation requirements
- Define transformation validation criteria

### For tool-integrator
- Implement 5 Python tools specified in "Tool Dependencies" section
- Register tools with agent instance
- Use `AgentDependencies` for passing configuration to tools
- Ensure all tools support async/await pattern

### For pydantic-ai-validator
- Use test fixtures from `conftest.py`
- Test with sample MQL5 code fixture
- Validate rollback functionality
- Verify certificate generation

## Notes

This is a PLANNING document. The main agent will implement these specifications as actual Python code. Key design decisions:

1. **Single Model Provider**: Claude Opus 4.5 only (best for mathematical reasoning)
2. **No External APIs**: All verification in Python tools
3. **Simple Dependencies**: Dataclass with file paths and config flags
4. **Atomic Transformations**: Rollback capability built into dependencies
5. **File-Based I/O**: Read MQL5 files, write fixed code and certificates

The agent is designed for reliability through simplicity - minimal configuration, maximum safety.
