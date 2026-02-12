# Agent Factory Migration Guide

## Overview

This guide explains how to migrate existing Pydantic AI agents to use the new factory pattern with comprehensive validation. The factory pattern provides:

- ✅ Standardized agent creation
- ✅ Input/output validation
- ✅ Backend state validation
- ✅ Execution monitoring
- ✅ Health checks
- ✅ Statistics and reporting

## Migration Steps

### 1. Import Factory Components

```python
from agent_factory_template import (
    create_agent_factory,
    AgentFactoryConfig,
    ValidationLevel,
    ValidatedAgent,
    InputValidator,
    OutputValidator,
    BackendValidator
)
```

### 2. Update Agent Configuration

Replace direct agent instantiation with factory configuration:

**Before:**
```python
agent = Agent(
    get_llm_model(),
    deps_type=AgentDependencies,
    system_prompt=SYSTEM_PROMPT
)
```

**After:**
```python
config = AgentFactoryConfig(
    agent_name="my_agent",
    agent_type="optimization",
    system_prompt=SYSTEM_PROMPT,
    validation_level=ValidationLevel.STRICT,
    dependencies_type=AgentDependencies
)

factory = create_agent_factory()
validated_agent = factory.create_agent(
    config=config,
    model_getter=get_llm_model,
    custom_tools=[tool1, tool2]
)
```

### 3. Add Custom Validation Rules

Define validation rules specific to your agent:

```python
custom_validators = {
    "input": {
        "validate_code": lambda code: ".cpp" in str(code),
        "validate_length": lambda text: len(str(text)) < 10000
    },
    "output": {
        "validate_result": lambda out: isinstance(out, dict),
        "validate_completeness": lambda out: "result" in out
    },
    "backend": {
        "required_keys": ["cache", "context", "session_id"]
    }
}

config = AgentFactoryConfig(
    agent_name="my_agent",
    system_prompt=SYSTEM_PROMPT,
    custom_validators=custom_validators
)
```

### 4. Update Execution Code

Replace direct agent runs with validated execution:

**Before:**
```python
result = await agent.run(prompt, deps=dependencies)
```

**After:**
```python
execution_record = await validated_agent.run_with_validation(
    prompt=prompt,
    deps=dependencies,
    input_schema=MyInputSchema,  # Optional
    output_schema=MyOutputSchema  # Optional
)

# Access result
result = execution_record["result"]
validation_results = execution_record["validation_results"]
```

### 5. Add Health Monitoring

Implement periodic health checks:

```python
async def monitor_agent_health():
    """Monitor agent health periodically."""
    while True:
        health_result = await validated_agent.health_check()

        if not health_result.is_valid:
            logger.error(f"Agent health check failed: {health_result.errors}")
            # Trigger alerts or recovery actions

        await asyncio.sleep(60)  # Check every minute
```

## Example Migrations

### Blitzfire Agent Migration

```python
# blitzfire_code_agent/agent.py

from agent_factory_template import create_agent_factory, AgentFactoryConfig, ValidationLevel

class BlitzfireAgentFactory:
    """Factory for Blitzfire optimization agents."""

    def __init__(self):
        self.factory = create_agent_factory()

    def create_optimizer_agent(self):
        """Create a Blitzfire optimizer agent with validation."""
        config = AgentFactoryConfig(
            agent_name="blitzfire_optimizer",
            agent_type="optimization",
            system_prompt=BLITZFIRE_SYSTEM_PROMPT,
            validation_level=ValidationLevel.STRICT,
            dependencies_type=BlitzfireDependencies,
            custom_validators={
                "input": {
                    "validate_cpp": lambda code: self._is_valid_cpp(code),
                    "validate_size": lambda code: len(str(code)) < 1000000
                },
                "output": {
                    "validate_optimization": lambda out: "optimized" in str(out).lower(),
                    "validate_metrics": lambda out: self._has_performance_metrics(out)
                }
            }
        )

        return self.factory.create_agent(
            config=config,
            model_getter=get_llm_model,
            custom_tools=[optimize_code, analyze_performance, generate_benchmark]
        )

    @staticmethod
    def _is_valid_cpp(code):
        """Validate C++ code."""
        return isinstance(code, str) and ("#include" in code or "int main" in code)

    @staticmethod
    def _has_performance_metrics(output):
        """Check if output contains performance metrics."""
        if isinstance(output, dict):
            return "execution_time" in output or "speedup" in output
        return False
```

### Clang-Tidy Agent Migration

```python
# clang_tidy_ai_agent/agent.py

from agent_factory_template import create_agent_factory, AgentFactoryConfig, ValidationLevel
from pathlib import Path

class ClangTidyAgentFactory:
    """Factory for Clang-Tidy analysis agents."""

    def __init__(self):
        self.factory = create_agent_factory()

    def create_analyzer_agent(self):
        """Create a Clang-Tidy analyzer agent with validation."""
        config = AgentFactoryConfig(
            agent_name="clang_tidy_analyzer",
            agent_type="analysis",
            system_prompt=CLANG_TIDY_SYSTEM_PROMPT,
            validation_level=ValidationLevel.MODERATE,
            dependencies_type=ClangTidyDependencies,
            custom_validators={
                "input": {
                    "validate_path": lambda p: Path(p).exists() if isinstance(p, str) else False,
                    "validate_extension": lambda p: str(p).endswith(('.cpp', '.h', '.cc'))
                },
                "output": {
                    "validate_warnings": lambda out: self._has_warning_structure(out),
                    "validate_fixes": lambda out: "fixes" in out if isinstance(out, dict) else False
                }
            }
        )

        return self.factory.create_agent(
            config=config,
            model_getter=get_llm_model,
            custom_tools=[run_clang_tidy, parse_diagnostics, apply_fixes]
        )

    @staticmethod
    def _has_warning_structure(output):
        """Validate warning output structure."""
        if isinstance(output, dict):
            return "warnings" in output or "errors" in output
        return "warning:" in str(output).lower() or "error:" in str(output).lower()
```

## Testing Your Migration

### 1. Unit Tests

```python
import pytest
from your_agent import YourAgentFactory

class TestAgentMigration:
    """Test migrated agent with factory pattern."""

    @pytest.mark.asyncio
    async def test_agent_creation(self):
        """Test agent creation via factory."""
        factory = YourAgentFactory()
        agent = factory.create_agent()

        assert agent is not None
        assert agent.config.validation_level == ValidationLevel.STRICT

    @pytest.mark.asyncio
    async def test_validation(self):
        """Test validation pipeline."""
        factory = YourAgentFactory()
        agent = factory.create_agent()

        # Test with valid input
        result = await agent.run_with_validation(
            prompt="Valid prompt",
            deps=create_test_dependencies()
        )

        assert result["success"]
        assert "validation_results" in result

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test agent health check."""
        factory = YourAgentFactory()
        agent = factory.create_agent()

        health = await agent.health_check()
        assert health.is_valid
```

### 2. Integration Tests

```python
async def test_full_pipeline():
    """Test complete agent pipeline with validation."""
    factory = YourAgentFactory()
    agent = factory.create_agent()

    # Execute multiple operations
    for i in range(5):
        result = await agent.run_with_validation(
            prompt=f"Test prompt {i}",
            deps=create_dependencies()
        )
        assert result["success"]

    # Check statistics
    stats = factory.get_statistics()
    assert stats["execution_stats"][agent.config.agent_name]["total"] == 5

    # Validate all agents
    validation_results = await factory.validate_all_agents()
    assert all(r.is_valid for r in validation_results.values())
```

## Benefits After Migration

1. **Consistent Error Handling**: All validation errors are captured and logged
2. **Performance Monitoring**: Track execution times and success rates
3. **Easy Debugging**: Complete execution history with validation results
4. **Health Monitoring**: Proactive detection of agent issues
5. **Statistics**: Comprehensive metrics for all agents
6. **Type Safety**: Strong typing with Pydantic models
7. **Extensibility**: Easy to add new validation rules

## Common Pitfalls

### 1. Missing Dependencies Type

**Issue**: Forgetting to specify dependencies_type in config
**Solution**: Always include dependencies_type in AgentFactoryConfig

### 2. Validation Too Strict

**Issue**: STRICT validation causing false positives
**Solution**: Start with MODERATE, gradually increase to STRICT

### 3. Custom Rules Not Async

**Issue**: Custom validation rules not handling async operations
**Solution**: Make validation functions async when needed

### 4. Large State Validation

**Issue**: Backend validation slow with large state
**Solution**: Implement caching or sampling for large state validation

## Support

For questions or issues with migration:
1. Check the test examples in `tests/test_factory_validation.py`
2. Review the template implementation in `agent_factory_template.py`
3. See working example in `multi_agent_debugging_system/agent_factory.py`