"""
LLM provider configuration for Awareness Orchestrator.

Supports multiple providers with proper error handling.
"""

import os
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from .settings import Settings, load_settings


def get_llm_model(settings: Settings | None = None):
    """Get configured LLM model with proper environment loading."""
    if settings is None:
        settings = load_settings()

    if settings.llm_provider.lower() == "anthropic":
        # Set API key in environment for pydantic-ai
        os.environ['ANTHROPIC_API_KEY'] = settings.llm_api_key
        return AnthropicModel(settings.llm_model)

    elif settings.llm_provider.lower() == "openai":
        # Set API key in environment for pydantic-ai
        os.environ['OPENAI_API_KEY'] = settings.llm_api_key
        if settings.llm_base_url:
            os.environ['OPENAI_BASE_URL'] = settings.llm_base_url
        return OpenAIModel(settings.llm_model)

    else:
        raise ValueError(
            f"Unsupported LLM provider: {settings.llm_provider}. "
            "Supported providers: anthropic, openai"
        )
