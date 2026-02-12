#!/usr/bin/env python3
"""
Test script for Clang-Tidy AI Agent factory integration.
Validates the factory pattern implementation and validation capabilities.
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Test the agent import
try:
    from agent import ClangTidyAIAgent, ClangTidyAnalysisRequest
    from agent_factory import (
        ClangTidyAgentFactory, ClangTidyAgentConfig, ClangTidyAgentType,
        ClangTidyValidationLevel, get_clang_tidy_factory
    )
    IMPORTS_SUCCESSFUL = True
    print("✅ Successfully imported Clang-Tidy agent components")
except ImportError as e:
    IMPORTS_SUCCESSFUL = False
    print(f"❌ Import failed: {e}")


def test_agent_config():
    """Test Clang-Tidy agent configuration."""
    print("\n🧪 Testing ClangTidyAgentConfig...")

    try:
        # Valid config
        config = ClangTidyAgentConfig(
            agent_name="test_clang_tidy_discoverer",
            agent_type=ClangTidyAgentType.ISSUE_DISCOVERER,
            system_prompt="You are a Clang-Tidy issue discovery specialist.",
            clang_tidy_checks="*,-readability-magic-numbers",
            fix_strategy="conservative",
            validation_level="strict"
        )
        print(f"✅ Valid config created: {config.agent_name}")
        print(f"   - Type: {config.agent_type}")
        print(f"   - Checks: {config.clang_tidy_checks}")
        print(f"   - Strategy: {config.fix_strategy}")

        # Test validation
        try:
            invalid_config = ClangTidyAgentConfig(
                agent_name="test",
                agent_type=ClangTidyAgentType.ISSUE_DISCOVERER,
                system_prompt="Test",
                fix_strategy="invalid_strategy"
            )
            print("❌ Should have failed with invalid fix strategy")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid strategy: {str(e)[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False


def test_factory_creation():
    """Test Clang-Tidy factory creation."""
    print("\n🏭 Testing ClangTidyAgentFactory...")

    try:
        factory = get_clang_tidy_factory()
        print(f"✅ Factory created successfully")

        # Create a test agent
        config = ClangTidyAgentConfig(
            agent_name="factory_test_discoverer",
            agent_type=ClangTidyAgentType.ISSUE_DISCOVERER,
            system_prompt="Test issue discoverer agent for factory validation.",
            clang_tidy_checks="modernize-*,readability-*",
            enable_auto_fix=False,
            validation_level="moderate"
        )

        agent = factory.create_clang_tidy_agent(config)
        print(f"✅ Agent created via factory: {agent.config.agent_name}")
        print(f"   - Has input validator: {agent.input_validator is not None}")
        print(f"   - Has output validator: {agent.output_validator is not None}")
        print(f"   - Has backend validator: {agent.backend_validator is not None}")

        return True

    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        return False


async def test_validation_pipeline():
    """Test validation pipeline with sample C++ file."""
    print("\n🔍 Testing Validation Pipeline...")

    try:
        factory = get_clang_tidy_factory()

        # Create a temporary C++ file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write("""
#include <iostream>
#include <vector>

class TestClass {
public:
    void testMethod() {
        auto i = 0;  // modernize-use-auto opportunity
        std::vector<int> vec;
        vec.push_back(1);
        vec.push_back(2);

        for (int i = 0; i < vec.size(); ++i) {  // modernize-loop-convert opportunity
            std::cout << vec[i] << std::endl;
        }
    }
};

int main() {
    TestClass tc;
    tc.testMethod();
    return 0;
}
            """)
            temp_file = f.name

        try:
            # Run validation pipeline
            validation_results = await factory.validate_clang_tidy_pipeline(
                file_path=temp_file,
                checks="modernize-*,readability-*"
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

        finally:
            # Clean up temp file
            Path(temp_file).unlink()

    except Exception as e:
        print(f"❌ Validation pipeline test failed: {e}")
        return False


async def test_agent_execution():
    """Test agent execution with validation."""
    print("\n⚡ Testing Agent Execution...")

    try:
        # Create a temporary C++ file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
            f.write("""
#include <iostream>
int main() {
    int x = 5;
    if (x = 10) {  // Assignment in condition - clang-tidy issue
        std::cout << "Test" << std::endl;
    }
    return 0;
}
            """)
            temp_file = f.name

        try:
            # Test both factory and legacy modes
            for use_factory in [True, False]:
                mode_name = "Factory" if use_factory else "Legacy"
                print(f"\n   Testing {mode_name} Mode:")

                agent = ClangTidyAIAgent(use_factory=use_factory, session_id="test_session")

                request = ClangTidyAnalysisRequest(
                    file_path=temp_file,
                    checks="bugprone-*,readability-*",
                    fix_strategy="conservative",
                    enable_auto_fix=False,  # Disable for testing
                    validation_level="production"
                )

                response = await agent.analyze_and_fix(request=request)

                print(f"   ✅ {mode_name} execution completed")
                print(f"      - Success: {response.get('success', False)}")
                print(f"      - Has phases: {bool(response.get('phases', {}))}")
                print(f"      - Factory mode: {response.get('factory_mode', 'unknown')}")

                if response.get('phases'):
                    phases = response['phases']
                    print(f"      - Phases completed: {list(phases.keys())}")

        finally:
            # Clean up temp file
            Path(temp_file).unlink()

        return True

    except Exception as e:
        print(f"❌ Agent execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_standard_agents():
    """Test creation of standard Clang-Tidy agents."""
    print("\n🔧 Testing Standard Agent Creation...")

    try:
        factory = get_clang_tidy_factory()
        agents = factory.create_standard_clang_tidy_agents()

        print(f"✅ Created {len(agents)} standard Clang-Tidy agents:")
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
        factory_agent = ClangTidyAIAgent(use_factory=True, session_id="factory_test")
        factory_status = await factory_agent.get_validation_status()

        print(f"✅ Factory validation status:")
        print(f"   - Factory mode: {factory_status.get('factory_mode')}")
        print(f"   - Validation enabled: {factory_status.get('validation_enabled')}")

        # Test legacy mode
        legacy_agent = ClangTidyAIAgent(use_factory=False, session_id="legacy_test")
        legacy_status = await legacy_agent.get_validation_status()

        print(f"✅ Legacy validation status:")
        print(f"   - Factory mode: {legacy_status.get('factory_mode')}")
        print(f"   - Validation: {legacy_status.get('validation')}")

        return True

    except Exception as e:
        print(f"❌ Validation status test failed: {e}")
        return False


async def run_all_tests():
    """Run all Clang-Tidy agent tests."""
    print("=" * 60)
    print("CLANG-TIDY AI AGENT FACTORY TEST SUITE")
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
    print("CLANG-TIDY TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All Clang-Tidy tests passed! Factory pattern working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the implementation.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)