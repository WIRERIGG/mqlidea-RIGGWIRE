"""Configuration settings for the Never Fail Build Resolver Agent."""

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional, List, Dict, Any
import os
import logging
from dotenv import load_dotenv

class BuildResolverSettings(BaseSettings):
    """Configuration settings for the Never Fail Build Resolver Agent."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8", 
        case_sensitive=False,
        extra="ignore"
    )
    
    # ============================================================================
    # LLM Configuration
    # ============================================================================
    
    llm_provider: str = Field(
        default="openai", 
        description="LLM provider (openai, anthropic, gemini, ollama)"
    )
    llm_api_key: str = Field(
        default="sk-test", 
        description="API key for the LLM provider"
    )
    llm_model: str = Field(
        default="gpt-4o-mini", 
        description="Model name to use"
    )
    llm_base_url: str = Field(
        default="https://api.openai.com/v1", 
        description="Base URL for LLM API"
    )
    
    # ============================================================================
    # Build System Configuration
    # ============================================================================
    
    project_root: Path = Field(
        default=Path("/IdeaProjects/wire_ground"), 
        description="Project root directory"
    )
    build_directory: Path = Field(
        default=Path("cmake-build-debug"), 
        description="Primary build directory"
    )
    cmake_binary_path: Path = Field(
        default=Path("/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake"),
        description="Path to CMake binary"
    )
    make_binary_path: Path = Field(
        default=Path("/usr/bin/make"), 
        description="Path to Make binary"
    )
    ninja_binary_path: Path = Field(
        default=Path("/usr/bin/ninja"), 
        description="Path to Ninja binary"
    )
    
    # ============================================================================
    # Compiler Toolchain Configuration
    # ============================================================================
    
    clang_binary_path: Path = Field(
        default=Path("/usr/bin/clang++"), 
        description="Path to Clang++ binary"
    )
    gcc_binary_path: Path = Field(
        default=Path("/usr/bin/g++"), 
        description="Path to GCC binary"
    )
    clang_tidy_binary_path: Path = Field(
        default=Path("/usr/bin/clang-tidy"), 
        description="Path to clang-tidy binary"
    )
    
    # ============================================================================
    # Resolution System Configuration  
    # ============================================================================
    
    # 4-Tier Resolution System Settings
    prevention_enabled: bool = Field(
        default=True, 
        description="Enable proactive prevention tier"
    )
    intelligent_resolution_enabled: bool = Field(
        default=True, 
        description="Enable intelligent resolution tier"
    )
    comprehensive_analysis_enabled: bool = Field(
        default=True, 
        description="Enable comprehensive problem solving tier"
    )
    nuclear_options_enabled: bool = Field(
        default=True, 
        description="Enable nuclear options tier (use with caution)"
    )
    
    # Timeout settings (in seconds)
    fast_mode_timeout: int = Field(
        default=30, 
        description="Timeout for fast mode resolution"
    )
    smart_mode_timeout: int = Field(
        default=300, 
        description="Timeout for smart mode resolution (5 minutes)"
    )
    thorough_mode_timeout: int = Field(
        default=1800, 
        description="Timeout for thorough mode resolution (30 minutes)"
    )
    emergency_mode_timeout: int = Field(
        default=3600, 
        description="Timeout for emergency mode resolution (1 hour)"
    )
    
    # ============================================================================
    # Agent-Specific Configuration
    # ============================================================================
    
    build_resolver_db_path: Path = Field(
        default=Path("./never_fail_build_resolver.db"), 
        description="SQLite database path for learning and caching"
    )
    build_resolver_log_level: str = Field(
        default="INFO", 
        description="Logging level"
    )
    max_build_errors_analyzed: int = Field(
        default=50, 
        description="Maximum build errors to analyze per session"
    )
    enable_learning_mode: bool = Field(
        default=True, 
        description="Enable learning from successful resolutions"
    )
    cache_build_analysis: bool = Field(
        default=True, 
        description="Cache build analysis results"
    )
    
    # ============================================================================
    # Safety and Backup Configuration
    # ============================================================================
    
    backup_before_resolution: bool = Field(
        default=True, 
        description="Create backups before applying resolutions"
    )
    backup_directory: Path = Field(
        default=Path(".build_resolver_backups"), 
        description="Directory for storing backups"
    )
    max_backups_retained: int = Field(
        default=10, 
        description="Maximum number of backups to retain"
    )
    rollback_on_failure: bool = Field(
        default=True, 
        description="Automatically rollback on resolution failure"
    )
    
    # ============================================================================
    # Integration Settings
    # ============================================================================
    
    # External script paths
    fix_build_script_path: Path = Field(
        default=Path("./scripts/fix_build.sh"), 
        description="Path to fix_build.sh script"
    )
    ai_clang_tidy_script_path: Path = Field(
        default=Path("./scripts/ai_clang_tidy.sh"), 
        description="Path to AI clang-tidy script"
    )
    build_safety_check_script_path: Path = Field(
        default=Path("./scripts/build_safety_check.sh"), 
        description="Path to build safety check script"
    )
    
    # Environment configuration
    build_environment_variables: Dict[str, str] = Field(
        default_factory=lambda: {
            "CMAKE_BUILD_TYPE": "Debug",
            "ENABLE_POWER_MODE": "ON",
            "SUPPRESS_DOCKER_WARNINGS": "ON",
            "ENABLE_SANITIZERS": "ON"
        },
        description="Default build environment variables"
    )
    
    # ============================================================================
    # Monitoring and Alerting
    # ============================================================================
    
    enable_build_monitoring: bool = Field(
        default=True, 
        description="Enable continuous build monitoring"
    )
    monitoring_interval_seconds: int = Field(
        default=300, 
        description="Interval between monitoring checks (5 minutes)"
    )
    alert_on_build_failure: bool = Field(
        default=True, 
        description="Send alerts on build failures"
    )
    alert_email: Optional[str] = Field(
        default=None, 
        description="Email address for build failure alerts"
    )
    
    # ============================================================================
    # Performance Configuration
    # ============================================================================
    
    parallel_analysis_jobs: int = Field(
        default=4, 
        description="Number of parallel analysis jobs"
    )
    enable_performance_profiling: bool = Field(
        default=False, 
        description="Enable performance profiling of resolution processes"
    )
    cache_size_limit_mb: int = Field(
        default=500, 
        description="Cache size limit in megabytes"
    )
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization validation."""
        if not self.project_root.exists():
            # Don't fail for testing - just warn
            pass
    
    def get_build_directory_path(self) -> Path:
        """Get the absolute path to the build directory."""
        if self.build_directory.is_absolute():
            return self.build_directory
        return self.project_root / self.build_directory
    
    def get_backup_directory_path(self) -> Path:
        """Get the absolute path to the backup directory."""
        if self.backup_directory.is_absolute():
            return self.backup_directory
        return self.project_root / self.backup_directory
    
    def validate_paths(self) -> List[str]:
        """Validate that required paths exist and are accessible.
        
        Returns:
            List of validation warnings (empty if all paths are valid)
        """
        warnings = []
        
        # Check critical build tools
        critical_tools = [
            ("CMake", self.cmake_binary_path),
            ("Make", self.make_binary_path),
        ]
        
        for tool_name, tool_path in critical_tools:
            if not tool_path.exists():
                warnings.append(f"{tool_name} binary not found at {tool_path}")
        
        # Check optional tools with fallback paths
        optional_tools = [
            ("Ninja", [self.ninja_binary_path, Path("/usr/local/bin/ninja")]),
            ("Clang++", [self.clang_binary_path, Path("/usr/local/bin/clang++")]),
            ("GCC", [self.gcc_binary_path, Path("/usr/local/bin/g++")]),
            ("clang-tidy", [
                self.clang_tidy_binary_path, 
                Path("/usr/local/bin/clang-tidy"),
                Path("/opt/homebrew/bin/clang-tidy")
            ]),
        ]
        
        for tool_name, potential_paths in optional_tools:
            found = False
            for path in potential_paths:
                if path.exists():
                    found = True
                    # Update the setting to the found path
                    if tool_name == "Ninja":
                        self.ninja_binary_path = path
                    elif tool_name == "Clang++":
                        self.clang_binary_path = path
                    elif tool_name == "GCC":
                        self.gcc_binary_path = path
                    elif tool_name == "clang-tidy":
                        self.clang_tidy_binary_path = path
                    break
            
            if not found:
                warnings.append(f"{tool_name} binary not found. Searched: {[str(p) for p in potential_paths]}")
        
        # Check project scripts
        project_scripts = [
            ("fix_build.sh", self.fix_build_script_path),
            ("ai_clang_tidy.sh", self.ai_clang_tidy_script_path),
            ("build_safety_check.sh", self.build_safety_check_script_path)
        ]
        
        for script_name, script_path in project_scripts:
            full_path = self.project_root / script_path if not script_path.is_absolute() else script_path
            if not full_path.exists():
                warnings.append(f"Project script {script_name} not found at {full_path}")
        
        return warnings
    
    def get_resolution_tier_config(self, tier: str) -> Dict:
        """Get configuration for a specific resolution tier."""
        tier_configs = {
            "prevention": {
                "enabled": self.prevention_enabled,
                "timeout": self.fast_mode_timeout,
                "description": "Proactive issue prevention"
            },
            "intelligent": {
                "enabled": self.intelligent_resolution_enabled,
                "timeout": self.smart_mode_timeout,
                "description": "Smart pattern-based resolution"
            },
            "comprehensive": {
                "enabled": self.comprehensive_analysis_enabled,
                "timeout": self.thorough_mode_timeout,
                "description": "Comprehensive problem solving"
            },
            "nuclear": {
                "enabled": self.nuclear_options_enabled,
                "timeout": self.emergency_mode_timeout,
                "description": "Emergency nuclear options"
            }
        }
        
        return tier_configs.get(tier.lower(), {})

def load_settings() -> BuildResolverSettings:
    """Load and validate settings with proper error handling."""
    load_dotenv()
    
    try:
        settings = BuildResolverSettings()
        
        # Validate paths and log warnings
        warnings = settings.validate_paths()
        if warnings:
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(warning)
        
        return settings
        
    except Exception as e:
        error_msg = f"Failed to load Build Resolver settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        raise ValueError(error_msg) from e

def get_default_settings() -> BuildResolverSettings:
    """Get default settings for testing and fallback scenarios."""
    return BuildResolverSettings(
        llm_api_key=os.getenv('LLM_API_KEY', 'test-key'),
        llm_provider='openai',
        llm_model='gpt-4o-mini'
    )