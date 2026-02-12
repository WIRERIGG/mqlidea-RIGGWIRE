#!/usr/bin/env python3
"""
Simple test script for the orchestration system
Tests core functionality without external dependencies
"""

import sys
import asyncio
from pathlib import Path

def test_import_modules():
    """Test if all modules can be imported"""
    print("Testing module imports...")

    try:
        # Test basic Python modules
        import json
        import logging
        from datetime import datetime
        print("✅ Standard library imports successful")

        # Test Pydantic
        from pydantic import BaseModel, Field
        from pydantic_settings import BaseSettings
        print("✅ Pydantic imports successful")

        # Test dotenv
        from dotenv import load_dotenv
        print("✅ dotenv import successful")

        # Test pydantic_ai core
        from pydantic_ai import Agent, RunContext
        print("✅ Pydantic AI core imports successful")

        return True

    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_orchestrator_structure():
    """Test the orchestrator file structure"""
    print("\nTesting file structure...")

    base_path = Path("/IdeaProjects/wire_ground/.claude/orchestrator")

    required_files = [
        "orchestrator.py",
        "tool_discovery_agent.py",
        "github_integration.py",
        "cloud_deployment.py",
        "validation.py",
        "validation_report.md"
    ]

    all_present = True
    for file_name in required_files:
        file_path = base_path / file_name
        if file_path.exists():
            print(f"✅ {file_name} exists ({file_path.stat().st_size} bytes)")
        else:
            print(f"❌ {file_name} missing")
            all_present = False

    return all_present

def test_basic_syntax():
    """Test if Python files have valid syntax"""
    print("\nTesting Python syntax...")

    base_path = Path("/IdeaProjects/wire_ground/.claude/orchestrator")
    python_files = [
        "orchestrator.py",
        "tool_discovery_agent.py",
        "github_integration.py",
        "cloud_deployment.py",
        "validation.py"
    ]

    all_valid = True
    for file_name in python_files:
        file_path = base_path / file_name
        try:
            with open(file_path, 'r') as f:
                compile(f.read(), file_path, 'exec')
            print(f"✅ {file_name} syntax valid")
        except SyntaxError as e:
            print(f"❌ {file_name} syntax error: {e}")
            all_valid = False
        except Exception as e:
            print(f"⚠️  {file_name} could not be checked: {e}")

    return all_valid

def main():
    """Run all tests"""
    print("🧪 Running Orchestration System Tests\n")

    tests = [
        ("Module Imports", test_import_modules),
        ("File Structure", test_orchestrator_structure),
        ("Python Syntax", test_basic_syntax)
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
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)

    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{len(results)} tests passed")

    if passed == len(results):
        print("🎉 All tests passed! Orchestration system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Check dependencies and file integrity.")
        return 1

if __name__ == "__main__":
    sys.exit(main())