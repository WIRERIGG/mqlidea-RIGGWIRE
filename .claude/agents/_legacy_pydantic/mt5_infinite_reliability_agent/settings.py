"""
Configuration management for MT5 Infinite Reliability Agent.
Minimal settings - only LLM configuration required.
"""

import os
from pathlib import Path
from typing import Optional, Literal
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Find .env file relative to this module's location
_THIS_DIR = Path(__file__).parent
_ENV_FILE = _THIS_DIR / ".env"

# Load environment variables from .env file
load_dotenv(_ENV_FILE)


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM Configuration (Anthropic Claude only)
    llm_provider: Literal["anthropic"] = Field(
        default="anthropic",
        description="LLM provider (fixed to Anthropic)"
    )
    anthropic_api_key: Optional[str] = Field(
        default=None,
        alias="ANTHROPIC_API_KEY",
        description="Anthropic API key for Claude (optional for validation)"
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

    # FTMO Compliance Settings
    ftmo_daily_loss_limit: float = Field(
        default=5.0,
        description="FTMO daily loss limit percentage"
    )
    ftmo_max_drawdown_limit: float = Field(
        default=10.0,
        description="FTMO maximum drawdown limit percentage"
    )

    # Optimization Settings
    preserve_features: bool = Field(
        default=True,
        description="Never alter trading logic during optimization"
    )

    @field_validator("anthropic_api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key if provided (allows None for validation mode)."""
        if v is None:
            # Allow None for validation/testing mode
            return v
        if v.strip() == "":
            # Empty string is invalid, but we allow it to fall back to None
            return None
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
