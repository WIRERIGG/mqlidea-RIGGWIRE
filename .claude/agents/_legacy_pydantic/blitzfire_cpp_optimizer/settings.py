"""Settings configuration for BLITZFIRE C++ Optimizer Agent."""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv
from typing import List, Optional

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
    
    # LLM Configuration
    llm_provider: str = Field(
        default="anthropic",
        description="LLM provider (anthropic, openai)"
    )
    
    llm_api_key: str = Field(
        default="",
        description="API key for the LLM provider"
    )
    
    llm_model: str = Field(
        default="claude-3-5-sonnet-20241022",
        description="LLM model to use"
    )
    
    llm_base_url: Optional[str] = Field(
        default="https://api.anthropic.com/v1",
        description="Base URL for LLM API"
    )
    
    # Wire Ground Configuration
    project_root: str = Field(
        default="/IdeaProjects/wire_ground",
        description="Wire Ground project root directory"
    )
    
    build_directory: str = Field(
        default="cmake-build-debug",
        description="CMake build directory"
    )
    
    scripts_directory: str = Field(
        default="scripts",
        description="Wire Ground scripts directory"
    )
    
    # C++ Toolchain Configuration
    compiler_executable: str = Field(
        default="clang++",
        description="C++ compiler executable"
    )
    
    cpp_standard: str = Field(
        default="c++20",
        description="C++ standard version"
    )
    
    clang_tidy_executable: str = Field(
        default="clang-tidy",
        description="Clang-tidy executable path"
    )
    
    # Optimization Configuration
    default_optimization_level: str = Field(
        default="standard",
        description="Default optimization level (conservative, standard, aggressive, extreme)"
    )
    
    default_domain: str = Field(
        default="general",
        description="Default optimization domain (general, hft, game, embedded, scientific)"
    )
    
    # Safety Configuration
    safety_first_mode: bool = Field(
        default=True,
        description="Prioritize safety over maximum performance"
    )
    
    zero_warning_policy: bool = Field(
        default=True,
        description="Enforce zero-warning compilation"
    )
    
    auto_rollback_on_failure: bool = Field(
        default=True,
        description="Automatically rollback failed optimizations"
    )
    
    # Performance Thresholds
    min_performance_improvement: float = Field(
        default=1.1,
        description="Minimum performance improvement threshold (1.1 = 10% improvement)"
    )
    
    benchmark_iterations: int = Field(
        default=1000,
        description="Number of benchmark iterations"
    )
    
    benchmark_timeout: int = Field(
        default=60,
        description="Benchmark timeout in seconds"
    )
    
    # Subagent Configuration
    enable_performance_analyzer: bool = Field(default=True)
    enable_algorithmic_improver: bool = Field(default=True)
    enable_memory_optimizer: bool = Field(default=True)
    enable_simd_vectorizer: bool = Field(default=True)
    enable_safety_validator: bool = Field(default=True)
    enable_benchmark_generator: bool = Field(default=True)


# Alias for backwards compatibility
BlitzfireCppOptimizerSettings = Settings

def load_settings() -> Settings:
    """Load settings with proper error handling."""
    try:
        return Settings()
    except Exception as e:
        print(f"Warning: Could not load full settings: {e}")
        # Return minimal working settings
        return Settings(
            llm_provider="anthropic",
            llm_model="claude-3-5-sonnet-20241022"
        )