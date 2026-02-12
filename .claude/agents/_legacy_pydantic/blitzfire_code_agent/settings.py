"""Configuration settings for the Blitzfire Code Agent."""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables from .env file
load_dotenv()

class BlitzfireSettings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider")
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(default="gpt-4o-mini", description="Model name to use")
    llm_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="Base URL for the LLM API"
    )

    # External Service Configuration
    godbolt_base_url: str = Field(
        default="https://godbolt.org",
        description="Godbolt Compiler Explorer API base URL"
    )
    godbolt_timeout: int = Field(default=30, description="Godbolt API timeout in seconds")
    godbolt_cache_ttl: int = Field(default=3600, description="Godbolt cache TTL in seconds")

    # Docker Configuration
    docker_enabled: bool = Field(default=True, description="Enable Docker benchmarking")
    docker_image: str = Field(default="blitzfire/benchmark:latest", description="Docker image for benchmarking")
    docker_timeout: int = Field(default=120, description="Docker execution timeout in seconds")
    docker_memory_limit: str = Field(default="2g", description="Docker memory limit")

    # Project Integration
    project_root: str = Field(
        default="/IdeaProjects/wire_ground",
        description="Project root directory path"
    )
    clang_binary_path: str = Field(
        default="/usr/bin/clang++",
        description="Path to clang++ compiler"
    )
    clang_tidy_binary_path: str = Field(
        default="/usr/bin/clang-tidy",
        description="Path to clang-tidy binary"
    )

    # Agent Behavior Configuration
    blitzfire_mode: str = Field(
        default="general",
        description="Optimization mode (general, hft, embedded, game)"
    )
    default_architecture: str = Field(
        default="x86_64",
        description="Default target architecture"
    )
    default_optimization_level: str = Field(
        default="-O3",
        description="Default compiler optimization level"
    )
    safety_level: str = Field(
        default="high",
        description="Safety constraint level (low, medium, high)"
    )

    # Performance and Caching
    analysis_cache_ttl: int = Field(default=1800, description="Analysis cache TTL in seconds")
    benchmark_cache_ttl: int = Field(default=7200, description="Benchmark cache TTL in seconds")
    max_code_size: int = Field(default=50000, description="Maximum code size to analyze")
    max_analysis_time: int = Field(default=30, description="Maximum analysis time in seconds")

    # HFT-specific settings
    hft_audit_level: str = Field(
        default="comprehensive",
        description="HFT audit level (basic, standard, comprehensive)"
    )
    hft_overflow_checks: bool = Field(default=True, description="Enable HFT overflow checks")
    hft_race_detection: bool = Field(default=True, description="Enable HFT race condition detection")

def load_settings() -> BlitzfireSettings:
    """Load settings with proper error handling and environment loading."""
    try:
        return BlitzfireSettings()
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        raise ValueError(error_msg) from e

# Create global settings instance
settings = load_settings()