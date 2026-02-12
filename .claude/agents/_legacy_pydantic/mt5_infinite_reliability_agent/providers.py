"""
Model provider configuration for MT5 Infinite Reliability Agent.
Fixed to Anthropic Claude Opus 4.5 for superior mathematical reasoning.
"""

from pydantic_ai.models.anthropic import AnthropicModel
from .settings import settings


def get_llm_model() -> AnthropicModel:
    """
    Get Claude Opus 4.5 model for mathematical reasoning and proof generation.

    Returns:
        Configured Anthropic model instance, or TestModel if no API key
    """
    import os
    from pydantic_ai.models.test import TestModel

    # Get API key from settings or environment
    api_key = settings.anthropic_api_key or os.environ.get('ANTHROPIC_API_KEY')

    if not api_key:
        # Return TestModel for validation/testing without API key
        import logging
        logging.warning("No ANTHROPIC_API_KEY found, using TestModel for validation")
        return TestModel()

    # Ensure it's in the environment for the Anthropic client
    os.environ['ANTHROPIC_API_KEY'] = api_key

    return AnthropicModel(settings.llm_model)


# No fallback model needed - Claude Opus 4.5 is the best choice for this task
# If needed in the future, fallback to Claude Sonnet 4.5:
# def get_fallback_model() -> AnthropicModel:
#     return AnthropicModel(
#         "claude-sonnet-4-5-20250929",
#         api_key=settings.anthropic_api_key
#     )
