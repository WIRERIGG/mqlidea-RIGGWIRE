"""LLM provider configuration for the Blitzfire Code Agent."""

from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.anthropic import AnthropicModel

# Gemini is optional
try:
    from pydantic_ai.providers.gemini import GeminiProvider
    from pydantic_ai.models.gemini import GeminiModel
    GEMINI_AVAILABLE = True
except ImportError:
    GeminiProvider = None
    GeminiModel = None
    GEMINI_AVAILABLE = False

from .settings import BlitzfireSettings, settings


def get_llm_model(config: BlitzfireSettings = None):
    """Get configured LLM model with proper environment loading."""
    if config is None:
        config = settings

    provider_name = config.llm_provider.lower()

    if provider_name == "openai":
        provider = OpenAIProvider(
            base_url=config.llm_base_url,
            api_key=config.llm_api_key
        )
        return OpenAIModel(config.llm_model, provider=provider)

    elif provider_name == "anthropic":
        provider = AnthropicProvider(api_key=config.llm_api_key)
        return AnthropicModel(config.llm_model, provider=provider)

    elif provider_name == "gemini":
        if not GEMINI_AVAILABLE:
            raise ValueError(
                "Gemini provider not available. Install with: pip install google-generativeai"
            )
        provider = GeminiProvider(api_key=config.llm_api_key)
        return GeminiModel(config.llm_model, provider=provider)

    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}. "
            "Supported providers: openai, anthropic, gemini"
        )


def get_test_model():
    """Get a test model for development and testing."""
    from pydantic_ai.models.test import TestModel
    return TestModel()