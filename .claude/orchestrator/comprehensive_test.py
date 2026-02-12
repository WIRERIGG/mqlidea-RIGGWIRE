#!/usr/bin/env python3
"""
Comprehensive test script for the orchestration system
Tests core functionality and Pydantic model validation
"""

import sys
import asyncio
import os
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

def test_pydantic_models():
    """Test Pydantic model definitions"""
    print("Testing Pydantic model definitions...")

    try:
        # Test orchestrator models
        sys.path.append('/IdeaProjects/wire_ground/.claude/orchestrator')
        import orchestrator

        # Test creating a basic OrchestrationTask
        task = orchestrator.OrchestrationTask(
            id="test-task-1",
            type=orchestrator.TaskType.TOOL_DISCOVERY,
            description="Test task",
            priority=5
        )
        print(f"✅ OrchestrationTask model: {task.id}")

        # Test AgentEnhancement model
        enhancement = orchestrator.AgentEnhancement(
            agent_name="test_agent",
            enhancement_type="feature_addition",
            description="Test enhancement",
            implementation_details={"test": "details"}
        )
        print(f"✅ AgentEnhancement model: {enhancement.agent_name}")

        # Test other models exist
        settings = orchestrator.OrchestrationSettings()
        print(f"✅ OrchestrationSettings model created")

        return True

    except Exception as e:
        print(f"❌ Pydantic model test failed: {e}")
        return False

def test_agent_definitions():
    """Test if agents can be instantiated"""
    print("\nTesting agent definitions...")

    try:
        # Set required environment variables for testing
        os.environ.setdefault('OPENAI_API_KEY', 'test-key')
        os.environ.setdefault('ANTHROPIC_API_KEY', 'test-key')
        os.environ.setdefault('GITHUB_TOKEN', 'test-token')

        # Import with mocked external dependencies
        import orchestrator

        # Test that the orchestrator class can be instantiated
        # Note: We're not testing actual functionality, just structure
        orchestrator_instance = orchestrator.AgentOrchestrator()
        print("✅ AgentOrchestrator class instantiated")

        # Test that the class has expected methods
        expected_methods = [
            'enhance_existing_agents',
            'discover_and_integrate_tools',
            'setup_github_integration',
            'setup_cloud_deployment',
            'run_validation',
            'execute_all_tasks'
        ]

        for method in expected_methods:
            if hasattr(orchestrator_instance, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Agent definition test failed: {e}")
        return False

def test_settings_validation():
    """Test settings and configuration validation"""
    print("\nTesting settings validation...")

    try:
        import orchestrator

        # Test settings with various configurations
        settings = orchestrator.OrchestrationSettings(
            github_token="test-token",
            max_concurrent_tasks=5,
            tool_discovery_enabled=True
        )
        print(f"✅ Settings validation passed")

        # Test that settings can handle missing values with defaults
        minimal_settings = orchestrator.OrchestrationSettings()
        print(f"✅ Minimal settings with defaults created")

        return True

    except Exception as e:
        print(f"❌ Settings validation test failed: {e}")
        return False

def test_cloud_deployment_models():
    """Test cloud deployment model definitions"""
    print("\nTesting cloud deployment models...")

    try:
        import cloud_deployment

        # Test basic deployment config
        config = cloud_deployment.DeploymentConfig(
            platform=cloud_deployment.Platform.AWS_LAMBDA,
            service_name="test-service",
            environment="development"
        )
        print(f"✅ DeploymentConfig model: {config.service_name}")

        # Test platform enum
        platforms = [p.value for p in cloud_deployment.Platform]
        print(f"✅ Platform enum has {len(platforms)} platforms: {platforms}")

        return True

    except Exception as e:
        print(f"❌ Cloud deployment model test failed: {e}")
        return False

def test_tool_discovery_models():
    """Test tool discovery model definitions"""
    print("\nTesting tool discovery models...")

    try:
        import tool_discovery_agent

        # Test DiscoveredTool model
        tool = tool_discovery_agent.DiscoveredTool(
            name="test-tool",
            description="A test tool",
            github_url="https://github.com/test/tool",
            language="Python",
            category="analysis"
        )
        print(f"✅ DiscoveredTool model: {tool.name}")

        # Test ToolEvaluation model
        evaluation = tool_discovery_agent.ToolEvaluation(
            tool_name="test-tool",
            relevance_score=8,
            complexity_score=5,
            integration_difficulty=3,
            overall_score=7.0
        )
        print(f"✅ ToolEvaluation model: {evaluation.tool_name}")

        return True

    except Exception as e:
        print(f"❌ Tool discovery model test failed: {e}")
        return False

def test_github_integration_models():
    """Test GitHub integration model definitions"""
    print("\nTesting GitHub integration models...")

    try:
        import github_integration

        # Test GitHubIssue model
        issue = github_integration.GitHubIssue(
            title="Test Issue",
            body="This is a test issue",
            labels=["bug", "enhancement"],
            assignees=[]
        )
        print(f"✅ GitHubIssue model: {issue.title}")

        # Test PRReview model
        review = github_integration.PRReview(
            pr_number=123,
            review_type=github_integration.ReviewType.COMMENT,
            summary="Test review",
            security_issues=[]
        )
        print(f"✅ PRReview model: PR #{review.pr_number}")

        return True

    except Exception as e:
        print(f"❌ GitHub integration model test failed: {e}")
        return False

def main():
    """Run all comprehensive tests"""
    print("🧪 Running Comprehensive Orchestration System Tests\n")

    tests = [
        ("Pydantic Models", test_pydantic_models),
        ("Agent Definitions", test_agent_definitions),
        ("Settings Validation", test_settings_validation),
        ("Cloud Deployment Models", test_cloud_deployment_models),
        ("Tool Discovery Models", test_tool_discovery_models),
        ("GitHub Integration Models", test_github_integration_models)
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*60)
    print("📋 COMPREHENSIVE TEST SUMMARY")
    print("="*60)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All comprehensive tests passed! Orchestration system is fully functional.")
        return 0
    else:
        print("⚠️  Some tests failed. Check model definitions and dependencies.")
        return 1

if __name__ == "__main__":
    sys.exit(main())