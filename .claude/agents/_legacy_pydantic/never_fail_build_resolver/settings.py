"""
Configuration management for NEVER FAIL BUILD RESOLVER using pydantic-settings.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class BuildResolverSettings(BaseSettings):
    """Comprehensive settings for NEVER FAIL BUILD RESOLVER."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration
    llm_provider: str = Field(default="anthropic")
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key (fallback)")
    llm_model: str = Field(default="claude-3-5-sonnet-20241022")
    llm_base_url: str = Field(default="https://api.anthropic.com/v1")
    
    # Project Configuration
    project_root: Path = Field(default=Path("/IdeaProjects/wire_ground"), description="Wire_ground project root directory")
    cmake_binary_path: Path = Field(
        default=Path("/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake"),
        description="Path to CMake executable"
    )
    build_dir: str = Field(default="cmake-build-debug")
    target_name: str = Field(default="wire_ground_tests")
    
    # Build System Configuration
    compiler_path: Path = Field(default=Path("/usr/bin/clang++"))
    clang_tidy_path: Path = Field(default=Path("/usr/bin/clang-tidy"))
    cmake_generator: str = Field(default="Ninja")
    build_type: str = Field(default="Debug")
    parallel_jobs: int = Field(default=14)
    
    # Resolution Configuration
    default_resolution_mode: str = Field(default="smart")
    max_resolution_time_fast: int = Field(default=180)
    max_resolution_time_smart: int = Field(default=600)
    max_resolution_time_thorough: int = Field(default=1200)
    max_resolution_time_emergency: int = Field(default=120)
    
    # State Management
    state_persistence_dir: Path = Field(default=Path("/tmp/never_fail_build_states"))
    backup_dir: Path = Field(default=Path("/tmp/never_fail_backups"))
    checkpoint_retention_days: int = Field(default=7)
    auto_cleanup_enabled: bool = Field(default=True)
    
    # Learning System
    pattern_learning_enabled: bool = Field(default=True)
    resolution_history_size: int = Field(default=1000)
    pattern_confidence_threshold: float = Field(default=0.75)
    auto_update_patterns: bool = Field(default=True)
    
    # Safety Configuration
    backup_before_changes: bool = Field(default=True)
    max_backup_size_gb: int = Field(default=5)
    safe_mode: bool = Field(default=True)
    allow_system_modifications: bool = Field(default=True)
    command_timeout_seconds: int = Field(default=300)
    
    # MCP Integration (Optional)
    mcp_server_url: Optional[str] = Field(default="http://archon-mcp:8051")
    mcp_enabled: bool = Field(default=True)
    archon_project_id: Optional[str] = Field(None)
    
    # Logging and Monitoring
    log_level: str = Field(default="INFO")
    debug_mode: bool = Field(default=False)
    verbose_logging: bool = Field(default=False)
    log_file_path: Path = Field(default=Path("/tmp/never_fail_build.log"))
    max_log_size_mb: int = Field(default=100)
    
    @field_validator('default_resolution_mode')
    @classmethod
    def validate_resolution_mode(cls, v):
        valid_modes = {'fast', 'smart', 'thorough', 'emergency'}
        if v not in valid_modes:
            raise ValueError(f"Resolution mode must be one of: {valid_modes}")
        return v
    
    @field_validator('pattern_confidence_threshold')
    @classmethod
    def validate_confidence_threshold(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError("Pattern confidence threshold must be between 0.0 and 1.0")
        return v
    
    @field_validator('anthropic_api_key', 'openai_api_key', mode='before')
    @classmethod
    def validate_api_keys(cls, v):
        """Validate API keys if provided."""
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("API key cannot be empty if provided")
        return v
    
    def has_valid_api_key(self) -> bool:
        """Check if at least one valid API key is available."""
        return bool(self.anthropic_api_key) or bool(self.openai_api_key)
    
    def get_resolution_timeout(self, mode: str) -> int:
        """Get timeout for specific resolution mode."""
        timeouts = {
            "fast": self.max_resolution_time_fast,
            "smart": self.max_resolution_time_smart,
            "thorough": self.max_resolution_time_thorough,
            "emergency": self.max_resolution_time_emergency
        }
        return timeouts.get(mode, self.max_resolution_time_smart)


def load_settings() -> BuildResolverSettings:
    """Load settings with proper error handling and environment loading."""
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        settings = BuildResolverSettings()
        
        # Validate that at least one API key is available
        if not settings.has_valid_api_key():
            raise ValueError(
                "No valid API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file"
            )
        
        # Ensure critical directories exist
        settings.state_persistence_dir.mkdir(parents=True, exist_ok=True)
        settings.backup_dir.mkdir(parents=True, exist_ok=True)
        
        return settings
        
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "api_key" in str(e).lower():
            error_msg += "\nMake sure to set ANTHROPIC_API_KEY or OPENAI_API_KEY in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance for easy import
try:
    settings = load_settings()
except Exception:
    # For testing and development, create settings with environment fallbacks
    import os
    os.environ.setdefault("ANTHROPIC_API_KEY", "test_key")
    settings = load_settings()