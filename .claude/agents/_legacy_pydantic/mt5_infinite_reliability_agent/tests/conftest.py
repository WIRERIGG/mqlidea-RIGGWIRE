"""
Test configuration and fixtures for MT5 Infinite Reliability Agent tests.
"""

import pytest
from pathlib import Path
from pydantic_ai.models.test import TestModel
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse

# Import agent components
import sys
# Add parent of parent to allow importing mt5_infinite_reliability_agent as a package
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from mt5_infinite_reliability_agent.agent import agent
from mt5_infinite_reliability_agent.dependencies import AgentDependencies
from mt5_infinite_reliability_agent.settings import Settings


@pytest.fixture
def test_model():
    """Provide TestModel for fast testing without API calls."""
    return TestModel()


@pytest.fixture
def test_agent(test_model):
    """Create agent with TestModel for testing."""
    return agent.override(model=test_model)


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    return Settings(
        anthropic_api_key="test_api_key_12345",
        llm_model="claude-opus-4-5-20251101",
        app_env="development",
        log_level="DEBUG",
        debug=True,
        max_code_size_kb=500,
        analysis_timeout_seconds=300
    )


@pytest.fixture
def test_dependencies(mock_settings):
    """Create test dependencies instance."""
    return AgentDependencies.from_settings(
        mock_settings,
        analysis_mode="full",
        proof_level="detailed",
        enable_rollback=True
    )


@pytest.fixture
def simple_mql5_code():
    """Provide simple MQL5 code sample for testing."""
    return """
//+------------------------------------------------------------------+
//| Simple EA Example                                                 |
//+------------------------------------------------------------------+
int OnInit()
{
    return(INIT_SUCCEEDED);
}

void OnTick()
{
    double ma = iMA(_Symbol, PERIOD_H1, 14, 0, MODE_SMA, PRICE_CLOSE);
    if (ma > 0)
    {
        Print("MA Value: ", ma);
    }
}
"""


@pytest.fixture
def complex_mql5_code():
    """Provide complex MQL5 code with multiple issues."""
    return """
//+------------------------------------------------------------------+
//| Complex EA with Issues                                            |
//+------------------------------------------------------------------+
input int MAPeriod = 14;
input double LotSize = 0.1;

int OnInit()
{
    // Missing validation
    return(INIT_SUCCEEDED);
}

void OnTick()
{
    double ma1 = iMA(_Symbol, PERIOD_H1, MAPeriod, 0, MODE_SMA, PRICE_CLOSE);
    double ma2 = iMA(_Symbol, PERIOD_H1, 50, 0, MODE_SMA, PRICE_CLOSE);
    double rsi = iRSI(_Symbol, PERIOD_H1, 14, PRICE_CLOSE);

    // Complexity issue: deep nesting
    if (ma1 > ma2)
    {
        if (rsi < 30)
        {
            if (AccountFreeMargin() > 1000)
            {
                // Missing error handling
                int ticket = OrderSend(_Symbol, OP_BUY, LotSize, Ask, 3, 0, 0);
            }
        }
    }

    // Memory issue: unchecked array access
    double prices[];
    ArrayResize(prices, 100);
    for (int i = 0; i <= 100; i++)  // Buffer overflow
    {
        prices[i] = Close[i];
    }
}
"""


@pytest.fixture
def sample_parsed_code():
    """Provide sample parsed code structure."""
    return {
        "ast": {
            "type": "Program",
            "functions": ["OnInit", "OnTick"],
            "variables": ["MAPeriod", "LotSize"]
        },
        "stats": {
            "function_count": 2,
            "variable_count": 2,
            "line_count": 35
        },
        "patterns": {
            "loops": 1,
            "conditions": 3,
            "indicators": 3
        },
        "hash": "abc123def456"
    }


@pytest.fixture
def sample_analysis_result():
    """Provide sample analysis result."""
    return {
        "issues_found": 4,
        "severity_breakdown": {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 1
        },
        "dimensions": {
            "complexity": {
                "score": 6.5,
                "issues": [
                    {
                        "dimension": "complexity",
                        "severity": "high",
                        "message": "Deep nesting level (3+) detected",
                        "line": 18,
                        "fix_suggestion": "Extract nested logic into separate function"
                    }
                ]
            },
            "memory": {
                "score": 7.0,
                "issues": [
                    {
                        "dimension": "memory",
                        "severity": "medium",
                        "message": "Potential buffer overflow in array access",
                        "line": 30,
                        "fix_suggestion": "Use ArraySize() to check bounds"
                    }
                ]
            },
            "security": {
                "score": 8.0,
                "issues": [
                    {
                        "dimension": "security",
                        "severity": "medium",
                        "message": "Missing input validation for MAPeriod",
                        "line": 5,
                        "fix_suggestion": "Add range validation for input parameters"
                    }
                ]
            },
            "robustness": {
                "score": 7.5,
                "issues": [
                    {
                        "dimension": "robustness",
                        "severity": "low",
                        "message": "Missing error handling for OrderSend",
                        "line": 24,
                        "fix_suggestion": "Check ticket value and handle errors"
                    }
                ]
            }
        },
        "overall_score": 7.25,
        "issues": []  # Will be populated from dimension issues
    }


@pytest.fixture
def function_model_with_tool_calling():
    """Create FunctionModel that simulates tool calling behavior."""

    call_count = 0

    async def agent_function(messages, tools):
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            # Initial response - acknowledge request
            return ModelResponse(
                content="I'll analyze this MQL5 code for reliability issues."
            )
        elif call_count == 2:
            # Call parse_mql5 tool
            return {
                "parse_mql5": {
                    "code": "sample_code"
                }
            }
        elif call_count == 3:
            # Call analyze_code tool
            return {
                "analyze_code": {
                    "parsed_code": {"ast": {}, "stats": {}},
                    "dimensions": ["complexity", "memory", "security", "robustness"],
                    "severity_threshold": "medium"
                }
            }
        elif call_count == 4:
            # Call transform_code tool
            return {
                "transform_code": {
                    "original_code": "sample_code",
                    "issues": [],
                    "auto_format": True,
                    "create_backup": True
                }
            }
        elif call_count == 5:
            # Call verify_transformation tool
            return {
                "verify_transformation": {
                    "original_code": "sample_code",
                    "transformed_code": "fixed_code",
                    "transformations": []
                }
            }
        elif call_count == 6:
            # Call generate_certificate tool
            return {
                "generate_certificate": {
                    "analysis": {},
                    "transformations": [],
                    "verification": {},
                    "proof_level": "detailed",
                    "output_format": "json"
                }
            }
        else:
            # Final response
            return ModelResponse(
                content="Analysis complete. Code has been verified and certified."
            )

    return FunctionModel(agent_function)


@pytest.fixture
def temp_mql5_file(tmp_path, simple_mql5_code):
    """Create temporary MQL5 file for testing."""
    test_file = tmp_path / "test_ea.mq5"
    test_file.write_text(simple_mql5_code)
    return test_file


@pytest.fixture
def temp_output_file(tmp_path):
    """Provide temporary output file path."""
    return tmp_path / "output_ea.mq5"


# Helper functions for tests

def assert_valid_analysis_result(result):
    """Assert that analysis result has valid structure."""
    assert "issues_found" in result
    assert "severity_breakdown" in result
    assert "dimensions" in result
    assert "overall_score" in result
    assert isinstance(result["issues_found"], int)
    assert isinstance(result["overall_score"], (int, float))


def assert_valid_transformation_result(result):
    """Assert that transformation result has valid structure."""
    assert "success" in result
    assert "transformations" in result
    assert "fixed_code" in result
    assert isinstance(result["transformations"], list)
    assert isinstance(result["fixed_code"], str)


def assert_valid_verification_result(result):
    """Assert that verification result has valid structure."""
    assert "verified" in result
    assert "checks" in result
    assert "confidence" in result
    assert isinstance(result["verified"], bool)
    assert isinstance(result["confidence"], (int, float))


def assert_valid_certificate(result):
    """Assert that certificate has valid structure."""
    assert "certificate" in result
    cert = result["certificate"]
    assert "id" in cert
    assert "timestamp" in cert
    assert "proof_chain" in cert
    assert "summary" in cert
    assert isinstance(cert["proof_chain"], list)
