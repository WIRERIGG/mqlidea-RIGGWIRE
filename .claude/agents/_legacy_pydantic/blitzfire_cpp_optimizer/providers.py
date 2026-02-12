"""BLITZFIRE C++ Optimizer Model Providers.

Provides LLM model configuration for the BLITZFIRE optimization agent.
Supports multiple providers with fallback options for reliability.
"""

import os
from typing import Union
from pydantic_ai.models import Model, KnownModelName

try:
    from pydantic_ai.models.test import TestModel
except ImportError:
    TestModel = None

def get_llm_model() -> Union[Model, KnownModelName]:
    """Get the appropriate LLM model for BLITZFIRE C++ optimization.
    
    Returns the best available model with fallback options:
    1. Claude Sonnet (preferred for code optimization)
    2. GPT-4 (good alternative)  
    3. TestModel (for validation and testing)
    """
    
    # Check for available API keys and return appropriate model name
    anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
    openai_api_key = os.getenv('OPENAI_API_KEY')
    
    # Prefer Claude Sonnet for code optimization
    if anthropic_api_key:
        return 'claude-3-5-sonnet-20241022'
    
    # Fall back to OpenAI models
    if openai_api_key:
        return 'gpt-4o'
    
    # Use TestModel for validation framework when no API keys available
    if TestModel:
        return TestModel()
    
    # Default fallback
    return 'claude-3-5-sonnet-20241022'

def get_optimization_model() -> Union[Model, KnownModelName]:
    """Get specialized model for optimization analysis (alias for get_llm_model)."""
    return get_llm_model()

def get_safety_model() -> Union[Model, KnownModelName]:
    """Get specialized model for safety analysis (alias for get_llm_model)."""
    return get_llm_model()

# Configuration for different optimization contexts
MODEL_CONFIGS = {
    "analysis": {
        "temperature": 0.1,  # Low temperature for consistent analysis
        "max_tokens": 4000,
        "system_role": "code_analyzer"
    },
    "optimization": {
        "temperature": 0.2,  # Slightly higher for creative optimizations
        "max_tokens": 6000,
        "system_role": "code_optimizer"  
    },
    "benchmarking": {
        "temperature": 0.1,  # Precise for benchmark generation
        "max_tokens": 3000,
        "system_role": "benchmark_generator"
    },
    "safety": {
        "temperature": 0.0,  # Maximum precision for safety checks
        "max_tokens": 2000,
        "system_role": "safety_validator"
    }
}

def get_model_for_context(context: str) -> tuple[Union[Model, KnownModelName], dict]:
    """Get model and configuration for specific optimization context."""
    model = get_llm_model()
    config = MODEL_CONFIGS.get(context, MODEL_CONFIGS["analysis"])
    return model, config

def get_provider_info():
    """Get provider information for debugging."""
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    openai_key = os.getenv('OPENAI_API_KEY')
    
    return {
        "anthropic_available": bool(anthropic_key),
        "openai_available": bool(openai_key),
        "preferred_provider": "anthropic" if anthropic_key else "openai" if openai_key else "none",
        "model_configs": list(MODEL_CONFIGS.keys())
    }

# Export main functions
__all__ = [
    "get_llm_model",
    "get_optimization_model", 
    "get_safety_model",
    "get_model_for_context",
    "get_provider_info",
    "MODEL_CONFIGS"
]