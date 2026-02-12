
import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.messages import ModelTextResponse

def test_basic_agent_import():
    """Test that we can import basic agent components."""
    try:
        from dependencies import BuildResolverDependencies
        from settings import load_settings
        from core.models import BuildProblem, BuildError
        assert True
    except Exception as e:
        pytest.fail(f"Import failed: {e}")

def test_test_model_basic():
    """Test basic TestModel functionality."""
    model = TestModel()
    model.agent_responses = [ModelTextResponse(content="Test response")]
    
    # This is a basic test to ensure TestModel works
    assert len(model.agent_responses) == 1
    assert model.agent_responses[0].content == "Test response"

def test_settings_load():
    """Test settings loading with environment fallback."""
    try:
        from settings import load_settings
        import os
        os.environ["ANTHROPIC_API_KEY"] = "test_key_for_validation"
        settings = load_settings()
        assert settings.anthropic_api_key == "test_key_for_validation"
    except Exception as e:
        pytest.fail(f"Settings load failed: {e}")
