#!/usr/bin/env python3
"""
Test script for Blitzfire Code Agent factory integration.
Validates the factory pattern implementation and validation capabilities.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Test the agent import
try:
    from agent import BlitzfireCodeAgent, BlitzfireAnalysisRequest
    from agent_factory import (
        BlitzfireAgentFactory, BlitzfireAgentConfig, BlitzfireAgentType,
        BlitzfireValidationLevel, get_blitzfire_factory
    )
    IMPORTS_SUCCESSFUL = True
    print("✅ Successfully imported Blitzfire agent components")
except ImportError as e:
    IMPORTS_SUCCESSFUL = False
    print(f"❌ Import failed: {e}")


def test_agent_config():
    """Test Blitzfire agent configuration."""
    print("\n🧪 Testing BlitzfireAgentConfig...")

    try:
        # Valid config
        config = BlitzfireAgentConfig(
            agent_name="test_blitzfire_optimizer",
            agent_type=BlitzfireAgentType.OPTIMIZER,
            system_prompt="You are a Blitzfire C++ optimization specialist.",
            optimization_target="performance",
            target_architecture="x86_64",
            validation_level="strict"
        )
        print(f"✅ Valid config created: {config.agent_name}")
        print(f"   - Type: {config.agent_type}")
        print(f"   - Target: {config.optimization_target}")
        print(f"   - Architecture: {config.target_architecture}")

        # Test validation
        try:
            invalid_config = BlitzfireAgentConfig(
                agent_name="test",
                agent_type=BlitzfireAgentType.OPTIMIZER,
                system_prompt="Test",
                optimization_target="invalid_target"
            )
            print("❌ Should have failed with invalid optimization target")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid target: {str(e)[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_factory_creation():
    """Test Blitzfire factory creation."""
    print("\n🏭 Testing BlitzfireAgentFactory...")

    try:
        factory = get_blitzfire_factory()
        print(f"✅ Factory created successfully")

        # Create a test agent
        config = BlitzfireAgentConfig(
            agent_name="factory_test_optimizer",
            agent_type=BlitzfireAgentType.OPTIMIZER,
            system_prompt="Test optimizer agent for factory validation.",
            optimization_target="performance",
            hft_mode=False,
            validation_level="moderate"
        )

        agent = factory.create_blitzfire_agent(config)
        print(f"✅ Agent created via factory: {agent.config.agent_name}")
        print(f"   - Has input validator: {agent.input_validator is not None}")
        print(f"   - Has output validator: {agent.output_validator is not None}")
        print(f"   - Has backend validator: {agent.backend_validator is not None}")

        return True

    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False


async def test_validation_pipeline():
    """Test validation pipeline with sample C++ code."""
    print("\n🔍 Testing Validation Pipeline...")

    try:
        factory = get_blitzfire_factory()

        # Test with sample C++ code
        sample_code = """
        #include <iostream>
        #include <vector>

        int main() {
            std::vector<int> data(1000);
            for (int i = 0; i < 1000; ++i) {
                data[i] = i * 2;
            }

            int sum = 0;
            for (int value : data) {
                sum += value;
            }

            std::cout << "Sum: " << sum << std::endl;
            return 0;
        }
        """

        # Run validation pipeline
        validation_results = await factory.validate_blitzfire_pipeline(
            code=sample_code,
            optimization_target="performance"
        )

        print(f"✅ Validation pipeline completed")
        for validation_type, result in validation_results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"   {status} {validation_type}: valid={result.is_valid}")
            if result.errors:
                print(f"      Errors: {result.errors}")
            if result.warnings:
                print(f"      Warnings: {result.warnings}")

        return all(result.is_valid for result in validation_results.values())

    except Exception as e:
        print(f"❌ Validation pipeline test failed: {e}")
        return False


async def test_agent_execution():
    """Test agent execution with validation."""
    print("\n⚡ Testing Agent Execution...")

    try:
        # Test both factory and legacy modes
        for use_factory in [True, False]:
            mode_name = "Factory" if use_factory else "Legacy"
            print(f"\n   Testing {mode_name} Mode:")

            agent = BlitzfireCodeAgent(use_factory=use_factory, session_id="test_session")

            request = BlitzfireAnalysisRequest(
                code_content="""
                #include <iostream>
                int main() {
                    int sum = 0;
                    for (int i = 0; i < 100; ++i) {
                        sum += i;
                    }
                    std::cout << sum << std::endl;
                    return 0;
                }
                """,
                architecture="x86_64",
                optimization_mode="general",
                include_benchmarks=False,  # Skip benchmarks for testing
                include_assembly=False     # Skip assembly for testing
            )

            response = await agent.analyze_and_optimize(request=request)

            print(f"   ✅ {mode_name} execution completed")
            print(f"      - Has analysis: {bool(response.analysis)}")
            print(f"      - Has strategy: {bool(response.strategy)}")
            print(f"      - Processing time: {response.processing_time_seconds:.3f}s")
            print(f"      - Blitzfire score: {response.blitzfire_score}")

            if hasattr(response, 'metadata') and response.metadata:
                print(f"      - Factory mode: {response.metadata.get('factory_mode', 'unknown')}")
                if 'validation_results' in response.metadata:
                    print(f"      - Has validation results: True")

        return True

    except Exception as e:
        print(f"❌ Agent execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_standard_agents():
    """Test creation of standard Blitzfire agents."""
    print("\n🔧 Testing Standard Agent Creation...")

    try:
        factory = get_blitzfire_factory()
        agents = factory.create_standard_blitzfire_agents()

        print(f"✅ Created {len(agents)} standard Blitzfire agents:")
        for name, agent in agents.items():
            print(f"   - {name}: type={agent.config.agent_type.value}")

        # Test agent health
        health_results = await factory.validate_all_agents()
        all_healthy = all(result.is_valid for result in health_results.values())

        print(f"✅ Agent health check: all_healthy={all_healthy}")
        for name, result in health_results.items():
            status = "✅" if result.is_valid else "❌"
            print(f"   {status} {name}: {len(result.errors)} errors, {len(result.warnings)} warnings")

        return all_healthy

    except Exception as e:
        print(f"❌ Standard agents test failed: {e}")
        return False


async def test_validation_status():
    """Test validation status reporting."""
    print("\n📊 Testing Validation Status...")

    try:
        # Test factory mode
        factory_agent = BlitzfireCodeAgent(use_factory=True, session_id="factory_test")
        factory_status = await factory_agent.get_validation_status()

        print(f"✅ Factory validation status:")
        print(f"   - Factory mode: {factory_status.get('factory_mode')}")
        print(f"   - Validation enabled: {factory_status.get('validation_enabled')}")

        # Test legacy mode
        legacy_agent = BlitzfireCodeAgent(use_factory=False, session_id="legacy_test")
        legacy_status = await legacy_agent.get_validation_status()

        print(f"✅ Legacy validation status:")
        print(f"   - Factory mode: {legacy_status.get('factory_mode')}")
        print(f"   - Validation: {legacy_status.get('validation')}")

        return True

    except Exception as e:
        print(f"❌ Validation status test failed: {e}")
        return False


async def run_all_tests():
    """Run all Blitzfire agent tests."""
    print("=" * 60)
    print("BLITZFIRE CODE AGENT FACTORY TEST SUITE")
    print("=" * 60)

    if not IMPORTS_SUCCESSFUL:
        print("❌ Cannot run tests due to import failures")
        return False

    results = []

    # Synchronous tests
    results.append(("Agent Config", test_agent_config()))
    results.append(("Factory Creation", test_factory_creation()))

    # Asynchronous tests
    async_results = [
        ("Validation Pipeline", await test_validation_pipeline()),
        ("Agent Execution", await test_agent_execution()),
        ("Standard Agents", await test_standard_agents()),
        ("Validation Status", await test_validation_status())
    ]
    results.extend(async_results)

    # Summary
    print("\n" + "=" * 60)
    print("BLITZFIRE TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Blitzfire tests passed! Factory pattern working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)