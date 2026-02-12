"""
Optimized settings configuration for the Clang-Tidy AI Agent.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict, validator
from dotenv import load_dotenv
import os


class OptimizedSettings(BaseSettings):
    """Application settings with validation and environment loading."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Core Paths
    clang_tidy_binary_path: Path = Field(
        default=Path("/usr/bin/clang-tidy"),
        description="Path to clang-tidy binary"
    )
    project_root: Path = Field(
        default=Path("/IdeaProjects/wire_ground"),
        description="Project root directory"
    )
    cache_dir: Path = Field(
        default=Path("/tmp/clang_tidy_cache"),
        description="Cache directory for analysis results"
    )
    
    # LLM Configuration
    llm_provider: str = Field(
        default="anthropic",
        description="LLM provider (anthropic/openai)"
    )
    llm_api_key: str = Field(
        default="",
        description="API key for LLM provider"
    )
    llm_model: str = Field(
        default="claude-3-sonnet-20240229",
        description="Model to use for AI analysis"
    )
    llm_max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retries for LLM API calls"
    )
    llm_timeout: int = Field(
        default=30,
        ge=5,
        le=120,
        description="Timeout for LLM API calls in seconds"
    )
    
    # Performance Settings
    max_concurrent_analyses: int = Field(
        default=4,
        ge=1,
        le=16,
        description="Maximum concurrent file analyses"
    )
    cache_ttl_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Cache TTL in seconds (1 hour default)"
    )
    subprocess_timeout: int = Field(
        default=30,
        ge=5,
        le=300,
        description="Subprocess timeout in seconds"
    )
    
    # Circuit Breaker Settings
    circuit_breaker_threshold: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Failures before circuit opens"
    )
    circuit_breaker_timeout: int = Field(
        default=60,
        ge=10,
        le=600,
        description="Circuit breaker reset timeout in seconds"
    )
    
    # Feature Flags
    enable_caching: bool = Field(
        default=True,
        description="Enable result caching"
    )
    enable_knowledge_base: bool = Field(
        default=True,
        description="Enable knowledge base for learning"
    )
    enable_progress_tracking: bool = Field(
        default=True,
        description="Enable markdown progress tracking"
    )
    enable_performance_metrics: bool = Field(
        default=True,
        description="Enable performance metrics collection"
    )
    enable_multi_compiler_validation: bool = Field(
        default=True,
        description="Enable validation with multiple compilers"
    )
    
    # Database Configuration
    sqlite_db_path: Path = Field(
        default=Path("/tmp/clang_tidy_ai.db"),
        description="Path to SQLite cache database"
    )
    knowledge_base_path: Path = Field(
        default=Path("/tmp/clang_tidy_knowledge.db"),
        description="Path to knowledge base database"
    )
    
    # Compiler Paths
    gcc_path: Path = Field(
        default=Path("/usr/bin/g++"),
        description="Path to GCC compiler"
    )
    clang_path: Path = Field(
        default=Path("/usr/bin/clang++"),
        description="Path to Clang compiler"
    )
    cmake_path: Path = Field(
        default=Path("/usr/bin/cmake"),
        description="Path to CMake"
    )
    
    # Integration Settings
    git_auto_commit: bool = Field(
        default=False,
        description="Automatically commit fixes to git"
    )
    cmake_build_dir: str = Field(
        default="cmake-build-debug",
        description="CMake build directory name"
    )
    audit_log_path: Path = Field(
        default=Path("/tmp/clang_tidy_audit.log"),
        description="Path to audit log file"
    )
    
    # Clang-Tidy Specific Settings
    default_checks: str = Field(
        default="readability-*,performance-*,modernize-*,bugprone-*",
        description="Default clang-tidy checks to run"
    )
    fix_categories: str = Field(
        default="readability-braces-around-statements,modernize-use-nullptr",
        description="Categories safe for automatic fixing"
    )
    
    @validator("llm_api_key")
    def validate_api_key(cls, v, values):
        """Validate API key is provided for LLM operations."""
        if not v and values.get("llm_provider"):
            # Try to get from environment
            env_key = f"{values['llm_provider'].upper()}_API_KEY"
            v = os.getenv(env_key, "")
        return v
    
    @validator("project_root", "cache_dir", "sqlite_db_path", "knowledge_base_path")
    def ensure_paths_exist(cls, v):
        """Ensure required directories exist."""
        if isinstance(v, Path):
            if v.name.endswith('.db'):
                # For database files, ensure parent directory exists
                v.parent.mkdir(parents=True, exist_ok=True)
            else:
                # For directories, create them
                v.mkdir(parents=True, exist_ok=True)
        return v
    
    def validate_environment(self) -> bool:
        """Validate that required tools are available."""
        validations = []
        
        # Check clang-tidy
        if not self.clang_tidy_binary_path.exists():
            print(f"Warning: clang-tidy not found at {self.clang_tidy_binary_path}")
            validations.append(False)
        
        # Check compilers if multi-compiler validation is enabled
        if self.enable_multi_compiler_validation:
            if not self.gcc_path.exists():
                print(f"Warning: GCC not found at {self.gcc_path}")
            if not self.clang_path.exists():
                print(f"Warning: Clang not found at {self.clang_path}")
        
        # Check API key
        if not self.llm_api_key:
            print("Warning: No LLM API key configured")
            validations.append(False)
        
        return all(validations) if validations else True
    
    def get_summary(self) -> dict:
        """Get configuration summary."""
        return {
            "project_root": str(self.project_root),
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model,
            "max_concurrent": self.max_concurrent_analyses,
            "caching_enabled": self.enable_caching,
            "knowledge_base_enabled": self.enable_knowledge_base,
            "performance_metrics_enabled": self.enable_performance_metrics,
            "default_checks": self.default_checks
        }


def load_optimized_settings() -> OptimizedSettings:
    """Load settings with proper environment handling."""
    # Load .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    
    # Also check for agent-specific env file
    agent_env_path = Path(__file__).parent / ".env"
    if agent_env_path.exists():
        load_dotenv(agent_env_path, override=True)
    
    try:
        settings = OptimizedSettings()
        
        # Validate environment
        if not settings.validate_environment():
            print("Warning: Some environment validations failed")
        
        return settings
        
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file or environment"
        raise ValueError(error_msg) from e


# Create a default settings instance
default_settings = None

def get_settings() -> OptimizedSettings:
    """Get or create default settings instance."""
    global default_settings
    if default_settings is None:
        default_settings = load_optimized_settings()
    return default_settings