"""LLM provider configuration for the Never Fail Build Resolver Agent."""

from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.gemini import GeminiModel
from typing import Union
import os

from .settings import BuildResolverSettings

# Try to import optional model types
try:
    from pydantic_ai.models.ollama import OllamaModel
    ModelType = Union[OpenAIModel, AnthropicModel, GeminiModel, OllamaModel]
except ImportError:
    OllamaModel = None
    ModelType = Union[OpenAIModel, AnthropicModel, GeminiModel]

def get_llm_model(settings: BuildResolverSettings) -> ModelType:
    """Get configured LLM model based on settings."""
    
    provider = settings.llm_provider.lower()
    
    # Set environment variables for API keys (PydanticAI reads from environment)
    if hasattr(settings, 'llm_api_key') and settings.llm_api_key:
        if provider == "openai":
            os.environ.setdefault('OPENAI_API_KEY', settings.llm_api_key)
        elif provider == "anthropic":
            os.environ.setdefault('ANTHROPIC_API_KEY', settings.llm_api_key)
        elif provider == "gemini":
            os.environ.setdefault('GEMINI_API_KEY', settings.llm_api_key)
    
    if provider == "openai":
        return OpenAIModel(
            model_name=settings.llm_model
        )
    
    elif provider == "anthropic":
        return AnthropicModel(
            model_name=settings.llm_model
        )
    
    elif provider == "gemini":
        return GeminiModel(
            model_name=settings.llm_model
        )
        
    elif provider == "ollama":
        if OllamaModel is None:
            raise ValueError("Ollama model not available in this PydanticAI installation")
        return OllamaModel(
            model_name=settings.llm_model
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")

def get_default_model() -> ModelType:
    """Get default model for fallback scenarios."""
    # Set test API key for validation
    os.environ.setdefault('OPENAI_API_KEY', 'test-key-for-validation')
    
    return OpenAIModel(
        model_name="gpt-4o-mini"
    )