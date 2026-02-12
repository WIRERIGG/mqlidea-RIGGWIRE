"""
Settings and configuration for Awareness Orchestrator.

Uses python-dotenv and pydantic-settings for proper environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict
from dotenv import load_dotenv
from pathlib import Path


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # LLM Configuration
    llm_provider: str = Field(default="anthropic", description="LLM provider (anthropic/openai)")
    llm_api_key: str = Field(..., description="API key for the LLM provider")
    llm_model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Model name to use"
    )
    llm_base_url: str | None = Field(
        default=None,
        description="Base URL for the LLM API (optional)"
    )

    # Orchestrator Configuration
    max_agents: int = Field(default=3, description="Maximum number of agents to run")
    enable_parallel: bool = Field(default=True, description="Enable parallel agent execution")
    context_depth: int = Field(default=3, description="Depth of context enrichment")

    # Learning Configuration
    learning_db_path: Path = Field(
        default=Path(".learning/orchestrator.json"),
        description="Path to learning database"
    )
    enable_learning: bool = Field(default=True, description="Enable pattern learning")

    # Logging Configuration
    log_dir: Path = Field(
        default=Path("/tmp/awareness_orchestrator_logs"),
        description="Directory for logs"
    )
    log_level: str = Field(default="INFO", description="Logging level")


def load_settings() -> Settings:
    """Load settings with proper error handling and environment loading."""
    # Load environment variables from .env file
    load_dotenv()

    try:
        settings = Settings()

        # Ensure directories exist
        settings.learning_db_path.parent.mkdir(parents=True, exist_ok=True)
        settings.log_dir.mkdir(parents=True, exist_ok=True)

        return settings
    except Exception as e:
        error_msg = f"Failed to load settings: {e}"
        if "llm_api_key" in str(e).lower():
            error_msg += "\nMake sure to set LLM_API_KEY in your .env file"
        raise ValueError(error_msg) from e
