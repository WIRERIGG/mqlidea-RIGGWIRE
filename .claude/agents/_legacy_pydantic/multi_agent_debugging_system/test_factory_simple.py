#!/usr/bin/env python3
"""
Simple test script to validate the agent factory implementation.
This can run without external dependencies installed.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Mock the pydantic_ai module if not available
try:
    from pydantic_ai import Agent, RunContext
except ImportError:
    print("Warning: pydantic_ai not installed, using mock implementation")

    class RunContext:
        def __init__(self, deps):
            self.deps = deps

    class Agent:
        def __init__(self, model, deps_type=None, system_prompt=""):
            self.model = model
            self.deps_type = deps_type
            self.system_prompt = system_prompt
            self.tools = []

        def tool(self, func):
            self.tools.append(func)
            return func

        async def run(self, prompt, deps=None, **kwargs):
            class Result:
                def __init__(self):
                    self.data = {"mock": "result", "prompt": prompt}
            return Result()

# Mock providers if needed
try:
    from providers import get_llm_model
except ImportError:
    def get_llm_model():
        return lambda: "mock_model"

# Now import our factory
from agent_factory import (
    AgentFactory, AgentConfig, AgentType, ValidationLevel,
    ValidationResult, InputValidator, OutputValidator, BackendValidator
)
from dependencies import create_debugging_context, AgentDependencies, AnalysisMode


def test_agent_config():
    """Test agent configuration validation."""
    print("Testing AgentConfig validation...")

    # Valid config
    try:
        config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="test_agent",
            system_prompt="Test system prompt for agent"
        )
        print("✅ Valid config created successfully")
        print(f"   - Name: {config.agent_name}")
        print(f"   - Type: {config.agent_type}")
        print(f"   - Validation Level: {config.validation_level}")
    except Exception as e:
        print(f"❌ Failed to create valid config: {e}")
        return False

    # Test invalid agent name
    try:
        invalid_config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="test@agent!",  # Invalid characters
            system_prompt="Test prompt"
        )
        print("❌ Invalid agent name should have failed")
        return False
    except ValueError as e:
        print(f"✅ Invalid agent name correctly rejected: {str(e)[:50]}...")

    # Test tool agent without config
    try:
        invalid_tool = AgentConfig(
            agent_type=AgentType.TOOL,
            agent_name="tool_agent",
            system_prompt="Test prompt"
            # Missing tool_config
        )
        print("❌ Tool agent without config should have failed")
        return False
    except ValueError as e:
        print(f"✅ Tool agent without config correctly rejected: {str(e)[:50]}...")

    return True


def test_factory_creation():
    """Test factory pattern."""
    print("\nTesting AgentFactory...")

    try:
        factory = AgentFactory()
        print(f"✅ Factory created with default validation level: {factory.default_validation_level}")

        # Create a test agent
        config = AgentConfig(
            agent_type=AgentType.LEAD,
            agent_name="factory_test_agent",
            system_prompt="Test agent from factory",
            validation_level=ValidationLevel.MODERATE
        )

        wrapper = factory.create_agent(config)
        print(f"✅ Agent created via factory: {wrapper.config.agent_name}")
        print(f"   - Has input validator: {wrapper.input_validator is not None}")
        print(f"   - Has output validator: {wrapper.output_validator is not None}")
        print(f"   - Has backend validator: {wrapper.backend_validator is not None}")

        # Check statistics
        stats = factory.get_statistics()
        print(f"✅ Factory statistics:")
        print(f"   - Agents created: {stats['agents_created']}")
        print(f"   - Agents registered: {stats['agents_registered']}")

        return True

    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False


def test_validation_components():
    """Test validation components."""
    print("\nTesting Validation Components...")

    try:
        # Test ValidationResult
        result = ValidationResult(
            is_valid=True,
            validation_type="test"
        )
        print(f"✅ ValidationResult created: valid={result.is_valid}")

        # Test error handling
        result.add_error("Test error")
        print(f"✅ Error added: valid={result.is_valid}, errors={result.errors}")

        # Test warning handling
        result2 = ValidationResult(is_valid=True, validation_type="test2")
        result2.add_warning("Test warning")
        print(f"✅ Warning added: valid={result2.is_valid}, has_warnings={result2.has_warnings}")

        # Test validators
        input_val = InputValidator(validation_level=ValidationLevel.STRICT)
        output_val = OutputValidator(validation_level=ValidationLevel.MODERATE)
        backend_val = BackendValidator(validation_level=ValidationLevel.MINIMAL)

        print(f"✅ Validators created with different levels")

        return True

    except Exception as e:
        print(f"❌ Validation component test failed: {e}")
        return False


async def test_async_validation():
    """Test async validation methods."""
    print("\nTesting Async Validation...")

    try:
        # Create validators
        input_validator = InputValidator(validation_level=ValidationLevel.STRICT)
        backend_validator = BackendValidator(validation_level=ValidationLevel.STRICT)

        # Test file path validation
        test_path = __file__  # This script itself
        result = await input_validator.validate_file_path(test_path)
        print(f"✅ File path validation: valid={result.is_valid}")
        print(f"   - File size: {result.metadata.get('file_size', 0)} bytes")
        print(f"   - Extension: {result.metadata.get('extension', 'unknown')}")

        # Test analysis mode validation
        result = await input_validator.validate_analysis_mode("comprehensive")
        print(f"✅ Analysis mode validation: valid={result.is_valid}")
        print(f"   - Mode: {result.metadata.get('mode', 'unknown')}")

        # Test cache integrity
        test_cache = {
            "tool1": {"result": "data"},
            "tool2": {"result": "more data"}
        }
        result = await backend_validator.validate_cache_integrity(test_cache)
        print(f"✅ Cache validation: valid={result.is_valid}")
        print(f"   - Cache size: {result.metadata.get('cache_size', 0)}")

        return True

    except Exception as e:
        print(f"❌ Async validation test failed: {e}")
        return False


async def test_standard_agents():
    """Test creation of standard debugging agents."""
    print("\nTesting Standard Agent Creation...")

    try:
        factory = AgentFactory()
        agents = factory.create_standard_agents()

        print(f"✅ Created {len(agents)} standard agents:")
        for name, wrapper in agents.items():
            print(f"   - {name}: type={wrapper.config.agent_type.value}, "
                  f"validation={wrapper.config.validation_level.value}")

        # Validate all agents
        validation_results = await factory.validate_all_agents()

        all_valid = all(r.is_valid for r in validation_results.values())
        print(f"✅ Agent health check: all_valid={all_valid}")

        for name, result in validation_results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"   {status} {name}: {len(result.errors)} errors, {len(result.warnings)} warnings")

        return all_valid

    except Exception as e:
        print(f"❌ Standard agents test failed: {e}")
        return False


async def test_agent_execution():
    """Test agent execution with validation."""
    print("\nTesting Agent Execution with Validation...")

    try:
        factory = AgentFactory()

        # Create test agent
        config = AgentConfig(
            agent_type=AgentType.TOOL,
            agent_name="execution_test",
            system_prompt="Test execution",
            tool_config={"tool_name": "test"},
            validation_level=ValidationLevel.MODERATE,
            enable_logging=False  # Disable logging for cleaner output
        )

        wrapper = factory.create_agent(config)

        # Create test dependencies
        context = create_debugging_context(
            target_path=__file__,
            analysis_mode=AnalysisMode.STATIC
        )

        deps = AgentDependencies(
            context=context,
            message_queue=[],
            results_cache={}
        )

        # Execute with validation
        execution_record = await wrapper.execute_with_validation(
            prompt="Test prompt for validation",
            dependencies=deps
        )

        print(f"✅ Agent execution completed: success={execution_record['success']}")
        print(f"   - Execution ID: {execution_record['id']}")
        print(f"   - Has validation results: {'validation_results' in execution_record}")

        # Check execution history
        print(f"✅ Execution history: {len(wrapper.execution_history)} records")

        return execution_record['success']

    except Exception as e:
        print(f"❌ Agent execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_tests():
    """Run all tests."""
    print("="*60)
    print("AGENT FACTORY VALIDATION TEST SUITE")
    print("="*60)

    results = []

    # Synchronous tests
    results.append(("AgentConfig Validation", test_agent_config()))
    results.append(("Factory Creation", test_factory_creation()))
    results.append(("Validation Components", test_validation_components()))

    # Asynchronous tests
    async def run_async_tests():
        async_results = []
        async_results.append(("Async Validation", await test_async_validation()))
        async_results.append(("Standard Agents", await test_standard_agents()))
        async_results.append(("Agent Execution", await test_agent_execution()))
        return async_results

    async_results = asyncio.run(run_async_tests())
    results.extend(async_results)

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! The agent factory with validation is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)