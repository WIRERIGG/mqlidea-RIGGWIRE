"""
Optimized model providers for the Clang-Tidy AI Agent with fallback support.
"""

from typing import Union, Optional, Any
import os
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.models.test import TestModel
import structlog

logger = structlog.get_logger(__name__)


class OptimizedModelProvider:
    """Manages LLM model providers with fallback and circuit breaker support."""
    
    def __init__(self, settings):
        """Initialize the model provider with settings."""
        self.settings = settings
        self.primary_model = None
        self.fallback_model = None
        self.test_model = None
        
        # Circuit breaker state
        self.failures = 0
        self.circuit_open = False
        
        # Initialize models
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize primary and fallback models."""
        try:
            # Create primary model
            self.primary_model = self._create_model(
                self.settings.llm_provider,
                self.settings.llm_api_key,
                self.settings.llm_model
            )
            
            # Create test model for development
            self.test_model = TestModel()
            
            # Optionally create fallback model
            fallback_provider = os.getenv("FALLBACK_LLM_PROVIDER")
            if fallback_provider and fallback_provider != self.settings.llm_provider:
                fallback_api_key = os.getenv(f"{fallback_provider.upper()}_API_KEY")
                fallback_model = os.getenv("FALLBACK_LLM_MODEL", "gpt-4")
                
                if fallback_api_key:
                    self.fallback_model = self._create_model(
                        fallback_provider,
                        fallback_api_key,
                        fallback_model
                    )
                    logger.info(
                        "Fallback model configured",
                        provider=fallback_provider,
                        model=fallback_model
                    )
        
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
            # Fall back to test model if initialization fails
            self.primary_model = TestModel()
    
    def _create_model(
        self, 
        provider: str, 
        api_key: str, 
        model_name: str
    ) -> Union[OpenAIModel, AnthropicModel, TestModel]:
        """Create a model instance based on provider."""
        if not api_key:
            logger.warning(f"No API key for {provider}, using TestModel")
            return TestModel()
        
        provider = provider.lower()
        
        if provider == "anthropic":
            return AnthropicModel(
                model_name=model_name,
                api_key=api_key
            )
        elif provider == "openai":
            return OpenAIModel(
                model_name=model_name,
                api_key=api_key
            )
        elif provider == "test":
            return TestModel()
        else:
            raise ValueError(f"Unknown provider: {provider}")
    
    def get_model(self) -> Any:
        """
        Get the appropriate model with circuit breaker logic.
        
        Returns:
            The model to use (primary, fallback, or test)
        """
        # If circuit is open, try fallback or test model
        if self.circuit_open:
            if self.fallback_model:
                logger.info("Using fallback model due to circuit breaker")
                return self.fallback_model
            else:
                logger.warning("Circuit open, using test model")
                return self.test_model
        
        # Return primary model if available
        if self.primary_model:
            return self.primary_model
        
        # Last resort: test model
        logger.warning("No primary model available, using test model")
        return self.test_model
    
    def record_success(self):
        """Record a successful API call."""
        self.failures = 0
        if self.circuit_open:
            logger.info("Circuit breaker reset after successful call")
            self.circuit_open = False
    
    def record_failure(self):
        """Record a failed API call and potentially open circuit."""
        self.failures += 1
        
        if self.failures >= self.settings.circuit_breaker_threshold:
            if not self.circuit_open:
                logger.warning(
                    "Circuit breaker opened",
                    failures=self.failures,
                    threshold=self.settings.circuit_breaker_threshold
                )
                self.circuit_open = True
    
    def is_available(self) -> bool:
        """Check if the primary model is available."""
        return self.primary_model is not None and not self.circuit_open
    
    def get_model_info(self) -> dict:
        """Get information about configured models."""
        info = {
            "primary": {
                "provider": self.settings.llm_provider,
                "model": self.settings.llm_model,
                "available": self.is_available()
            },
            "circuit_breaker": {
                "open": self.circuit_open,
                "failures": self.failures,
                "threshold": self.settings.circuit_breaker_threshold
            }
        }
        
        if self.fallback_model:
            info["fallback"] = {
                "configured": True,
                "provider": os.getenv("FALLBACK_LLM_PROVIDER", "unknown")
            }
        else:
            info["fallback"] = {"configured": False}
        
        return info


class ModelManager:
    """Manages multiple model providers for different tasks."""
    
    def __init__(self, settings):
        """Initialize the model manager."""
        self.settings = settings
        self.providers = {}
        
        # Create providers for different tasks
        self.providers["analysis"] = OptimizedModelProvider(settings)
        self.providers["explanation"] = OptimizedModelProvider(settings)
        self.providers["fixing"] = OptimizedModelProvider(settings)
    
    def get_provider(self, task_type: str = "analysis") -> OptimizedModelProvider:
        """Get a provider for a specific task type."""
        return self.providers.get(task_type, self.providers["analysis"])
    
    def get_all_providers_info(self) -> dict:
        """Get information about all providers."""
        return {
            task: provider.get_model_info()
            for task, provider in self.providers.items()
        }
    
    def reset_all_circuits(self):
        """Reset all circuit breakers."""
        for provider in self.providers.values():
            provider.failures = 0
            provider.circuit_open = False
        logger.info("All circuit breakers reset")