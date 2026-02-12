"""
Model provider configuration for NEVER FAIL BUILD RESOLVER.
"""

import logging
from typing import Optional

from pydantic_ai.models import Model
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.test import TestModel

try:
    from pydantic_ai.providers.anthropic import AnthropicProvider
except ImportError:
    logging.warning("Anthropic provider not available. Install with: pip install anthropic")
    AnthropicProvider = None

try:
    from pydantic_ai.providers.openai import OpenAIProvider
except ImportError:
    logging.warning("OpenAI provider not available. Install with: pip install openai")
    OpenAIProvider = None

from .settings import BuildResolverSettings, load_settings

logger = logging.getLogger(__name__)


def get_llm_model(settings: Optional[BuildResolverSettings] = None) -> Model:
    """
    Get LLM model with fallback providers.
    
    Args:
        settings: Optional settings instance. If not provided, loads from global settings.
        
    Returns:
        Configured LLM model instance
        
    Raises:
        ValueError: If no valid API keys are available or providers are not installed
    """
    if settings is None:
        settings = load_settings()
    
    # Primary: Anthropic Claude (preferred for complex reasoning)
    if (settings.llm_provider == "anthropic" and 
        settings.anthropic_api_key and 
        AnthropicProvider is not None):
        
        try:
            provider = AnthropicProvider(api_key=settings.anthropic_api_key)
            model = AnthropicModel(settings.llm_model, provider=provider)
            logger.info(f"Initialized Anthropic model: {settings.llm_model}")
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize Anthropic model: {e}")
    
    # Fallback: OpenAI GPT
    if settings.openai_api_key and OpenAIProvider is not None:
        try:
            provider = OpenAIProvider(
                api_key=settings.openai_api_key,
                base_url=settings.llm_base_url if "openai" in settings.llm_base_url else "https://api.openai.com/v1"
            )
            # Use a capable model for build problem resolution
            model_name = "gpt-4-turbo" if "gpt" not in settings.llm_model else settings.llm_model
            model = OpenAIModel(model_name, provider=provider)
            logger.info(f"Initialized OpenAI model: {model_name}")
            return model
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI model: {e}")
    
    # Last resort: TestModel for development/testing
    logger.warning("No production models available, falling back to TestModel")
    return TestModel()


def get_test_model() -> TestModel:
    """
    Get test model for validation and development.
    
    Returns:
        TestModel instance for safe testing without API calls
    """
    return TestModel()


def validate_model_availability() -> dict:
    """
    Validate which model providers are available.
    
    Returns:
        Dictionary with availability status for each provider
    """
    availability = {
        "anthropic": {
            "provider_available": AnthropicProvider is not None,
            "api_key_configured": bool(load_settings().anthropic_api_key)
        },
        "openai": {
            "provider_available": OpenAIProvider is not None,
            "api_key_configured": bool(load_settings().openai_api_key)
        },
        "test": {
            "provider_available": True,
            "api_key_configured": True
        }
    }
    
    # Log availability status
    for provider, status in availability.items():
        if status["provider_available"] and status["api_key_configured"]:
            logger.info(f"{provider.capitalize()} provider: Available")
        elif not status["provider_available"]:
            logger.warning(f"{provider.capitalize()} provider: Not installed")
        else:
            logger.warning(f"{provider.capitalize()} provider: No API key configured")
    
    return availability


def get_optimal_model_for_task(task_type: str = "general") -> Model:
    """
    Get the optimal model for a specific task type.
    
    Args:
        task_type: Type of task ("analysis", "resolution", "learning", "general")
        
    Returns:
        Model instance optimized for the task type
    """
    settings = load_settings()
    
    # For complex build problem analysis, prefer Claude
    if task_type in ["analysis", "resolution"] and settings.anthropic_api_key:
        return get_llm_model(settings)
    
    # For general tasks, use configured model
    return get_llm_model(settings)


# Module-level model instances for easy import
try:
    primary_model = get_llm_model()
    test_model = get_test_model()
except Exception as e:
    logger.error(f"Failed to initialize models: {e}")
    # Fallback to test model
    primary_model = TestModel()
    test_model = TestModel()