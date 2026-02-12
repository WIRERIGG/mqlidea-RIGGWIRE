#!/usr/bin/env python3
"""
Direct validation script for clang_tidy_ai_agent production readiness.
Tests core functionality without relying on complex import structures.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

def test_clang_tidy_available():
    """Test if clang-tidy is available in the system."""
    try:
        result = subprocess.run(['clang-tidy', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False

def test_python_environment():
    """Test Python environment and basic imports."""
    try:
        import pydantic_ai
        import pydantic
        import structlog
        return True
    except ImportError as e:
        print(f"Import error: {e}")
        return False

def test_core_modules_loadable():
    """Test if core modules can be loaded."""
    core_dir = Path(__file__).parent / "core"
    sys.path.insert(0, str(core_dir))
    
    tests = {
        'settings': False,
        'models': False,
        'dependencies': False,
        'tools': False,
        'agent': False
    }
    
    try:
        import settings
        tests['settings'] = True
    except Exception as e:
        print(f"Settings import failed: {e}")
    
    try:
        import models
        tests['models'] = True
    except Exception as e:
        print(f"Models import failed: {e}")
    
    try:
        import dependencies
        tests['dependencies'] = True
    except Exception as e:
        print(f"Dependencies import failed: {e}")
    
    try:
        import tools
        tests['tools'] = True
    except Exception as e:
        print(f"Tools import failed: {e}")
    
    try:
        import agent
        tests['agent'] = True
    except Exception as e:
        print(f"Agent import failed: {e}")
    
    return tests

def test_legacy_optimized_modules():
    """Test if optimized legacy modules can be loaded."""
    legacy_dir = Path(__file__).parent / "legacy"
    sys.path.insert(0, str(legacy_dir))
    
    tests = {
        'agent_optimized': False,
        'tools_optimized': False,
        'settings_optimized': False,
        'dependencies_optimized': False,
        'providers_optimized': False
    }
    
    try:
        import agent_optimized
        tests['agent_optimized'] = True
    except Exception as e:
        print(f"Optimized agent import failed: {e}")
    
    try:
        import tools_optimized
        tests['tools_optimized'] = True
    except Exception as e:
        print(f"Optimized tools import failed: {e}")
    
    try:
        import settings_optimized
        tests['settings_optimized'] = True
    except Exception as e:
        print(f"Optimized settings import failed: {e}")
    
    try:
        import dependencies_optimized
        tests['dependencies_optimized'] = True
    except Exception as e:
        print(f"Optimized dependencies import failed: {e}")
    
    try:
        import providers_optimized
        tests['providers_optimized'] = True
    except Exception as e:
        print(f"Optimized providers import failed: {e}")
    
    return tests

def test_file_structure():
    """Test expected file structure exists."""
    base_dir = Path(__file__).parent
    
    expected_files = [
        'core/agent.py',
        'core/tools.py', 
        'core/models.py',
        'core/settings.py',
        'core/dependencies.py',
        'legacy/agent_optimized.py',
        'legacy/tools_optimized.py',
        'utils/cli_optimized.py',
        'tests/conftest.py',
        'tests/VALIDATION_REPORT.md',
        'tests/OPTIMIZATION_VALIDATION_REPORT.md'
    ]
    
    results = {}
    for file_path in expected_files:
        full_path = base_dir / file_path
        results[file_path] = full_path.exists()
    
    return results

def create_test_cpp_file():
    """Create a test C++ file for validation."""
    cpp_content = '''
#include <iostream>
#include <memory>

int main() {
    // Potential clang-tidy issues
    int* ptr = new int(42);  // prefer smart pointers
    std::cout << *ptr << std::endl;
    // delete ptr; // commented out to create potential leak
    return 0;
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(cpp_content)
        return f.name

def test_basic_clang_tidy_functionality():
    """Test basic clang-tidy functionality on a test file."""
    if not test_clang_tidy_available():
        return False, "clang-tidy not available"
    
    test_file = create_test_cpp_file()
    try:
        result = subprocess.run([
            'clang-tidy', 
            test_file,
            '--checks=modernize-*,readability-*',
            '--'
        ], capture_output=True, text=True, timeout=10)
        
        # Clean up
        os.unlink(test_file)
        
        # Check if we got some warnings (expected for our test file)
        return len(result.stdout) > 0, f"Output length: {len(result.stdout)}"
        
    except Exception as e:
        os.unlink(test_file)
        return False, str(e)

def main():
    """Run all validation tests and report results."""
    print("🔍 Clang-Tidy AI Agent Production Readiness Validation")
    print("=" * 60)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("Clang-Tidy Available", test_clang_tidy_available),
        ("File Structure", test_file_structure),
        ("Core Modules", test_core_modules_loadable), 
        ("Optimized Modules", test_legacy_optimized_modules),
        ("Basic Clang-Tidy", test_basic_clang_tidy_functionality)
    ]
    
    results = {}
    total_score = 0
    max_score = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 Testing: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            
            if isinstance(result, bool):
                status = "✅ PASS" if result else "❌ FAIL"
                score = 1 if result else 0
                max_score += 1
                total_score += score
                print(f"   {status}")
            elif isinstance(result, dict):
                passed = sum(1 for v in result.values() if v)
                total = len(result)
                max_score += total
                total_score += passed
                print(f"   ✅ PASS: {passed}/{total}")
                for key, value in result.items():
                    status = "✅" if value else "❌"
                    print(f"     {status} {key}")
            elif isinstance(result, tuple):
                success, message = result
                status = "✅ PASS" if success else "❌ FAIL"
                score = 1 if success else 0
                max_score += 1
                total_score += score
                print(f"   {status} - {message}")
                
        except Exception as e:
            results[test_name] = False
            max_score += 1
            print(f"   ❌ ERROR: {e}")
    
    # Calculate final score
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    print("\n" + "=" * 60)
    print(f"📊 OVERALL PRODUCTION READINESS: {percentage:.1f}%")
    print(f"📈 Score: {total_score}/{max_score}")
    
    if percentage >= 95:
        print("🎉 STATUS: PRODUCTION READY ✅")
        return 0
    elif percentage >= 80:
        print("⚠️  STATUS: NEEDS MINOR FIXES")
        return 1
    else:
        print("❌ STATUS: MAJOR ISSUES - NOT PRODUCTION READY")
        return 2

if __name__ == "__main__":
    sys.exit(main())