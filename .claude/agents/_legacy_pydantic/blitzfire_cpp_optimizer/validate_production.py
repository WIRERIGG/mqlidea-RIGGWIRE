#!/usr/bin/env python3
"""
Direct validation script for blitzfire_cpp_optimizer production readiness.
Tests core functionality without relying on complex import structures.
"""

import sys
import os
import subprocess
import tempfile
from pathlib import Path

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

def test_blitzfire_modules_loadable():
    """Test if BLITZFIRE modules can be loaded."""
    agent_dir = Path(__file__).parent
    sys.path.insert(0, str(agent_dir))
    
    tests = {
        'settings': False,
        'models': False,
        'dependencies': False,
        'tools': False,
        'agent': False,
        'providers': False,
        'cli': False
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
        import providers
        tests['providers'] = True
    except Exception as e:
        print(f"Providers import failed: {e}")
    
    try:
        import cli
        tests['cli'] = True
    except Exception as e:
        print(f"CLI import failed: {e}")
    
    try:
        import agent
        tests['agent'] = True
    except Exception as e:
        print(f"Agent import failed: {e}")
    
    return tests

def test_file_structure():
    """Test expected file structure exists."""
    base_dir = Path(__file__).parent
    
    expected_files = [
        'agent.py',
        'tools.py', 
        'models.py',
        'settings.py',
        'dependencies.py',
        'providers.py',
        'cli.py',
        'cli_optimized.py',
        'prompts.py',
        'requirements.txt',
        'README.md',
        '.env',
        '.env.example'
    ]
    
    results = {}
    for file_path in expected_files:
        full_path = base_dir / file_path
        results[file_path] = full_path.exists()
    
    return results

def test_cpp_compiler_available():
    """Test if C++ compiler is available."""
    compilers = ['clang++', 'g++', 'c++']
    
    for compiler in compilers:
        try:
            result = subprocess.run([compiler, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return True, f"{compiler} available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue
    
    return False, "No C++ compiler found"

def create_test_cpp_file():
    """Create a test C++ file for validation."""
    cpp_content = '''
#include <iostream>
#include <vector>
#include <algorithm>

// Performance bottleneck: nested loops
void inefficient_sorting(std::vector<int>& vec) {
    for (size_t i = 0; i < vec.size(); ++i) {
        for (size_t j = i + 1; j < vec.size(); ++j) {
            if (vec[i] > vec[j]) {
                std::swap(vec[i], vec[j]);
            }
        }
    }
}

// Performance bottleneck: string concatenation in loop
std::string build_string(int count) {
    std::string result;
    for (int i = 0; i < count; ++i) {
        result += std::to_string(i) + ",";
    }
    return result;
}

// Performance bottleneck: unnecessary copies
void process_data(std::vector<std::string> data) {
    for (auto item : data) {  // should use const reference
        std::cout << item << std::endl;  // should use newline
    }
}

int main() {
    std::vector<int> numbers = {5, 2, 8, 1, 9};
    inefficient_sorting(numbers);
    
    auto str = build_string(1000);
    
    std::vector<std::string> data = {"hello", "world", "test"};
    process_data(data);
    
    return 0;
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.cpp', delete=False) as f:
        f.write(cpp_content)
        return f.name

def test_basic_cpp_compilation():
    """Test basic C++ compilation functionality."""
    test_file = create_test_cpp_file()
    
    try:
        # Try to compile with common compilers
        compilers = ['clang++', 'g++']
        
        for compiler in compilers:
            try:
                # Use secure temp file for output
                with tempfile.NamedTemporaryFile(mode='w', suffix='_blitzfire_test', delete=False) as temp_output:
                    output_path = temp_output.name
                
                result = subprocess.run([
                    compiler, 
                    test_file,
                    '-o', output_path,
                    '-std=c++17'
                ], capture_output=True, text=True, timeout=10)
                
                # Debug output
                if result.returncode != 0:
                    print(f"    DEBUG: {compiler} failed with stderr: {result.stderr}")
                    print(f"    DEBUG: stdout: {result.stdout}")
                
                if result.returncode == 0:
                    os.unlink(test_file)
                    try:
                        os.unlink(output_path)
                    except:
                        pass
                    return True, f"Compilation successful with {compiler}"
                    
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
        
        os.unlink(test_file)
        return False, "No compiler could compile test file"
        
    except Exception as e:
        try:
            os.unlink(test_file)
        except:
            pass
        return False, str(e)

def test_requirements_file():
    """Test if requirements file exists and is readable."""
    base_dir = Path(__file__).parent
    req_file = base_dir / "requirements.txt"
    
    if not req_file.exists():
        return False, "requirements.txt not found"
    
    try:
        with open(req_file, 'r') as f:
            content = f.read()
            
        # Check for essential dependencies
        required_deps = ['pydantic-ai', 'pydantic', 'structlog']
        found_deps = []
        
        for dep in required_deps:
            if dep in content or dep.replace('-', '_') in content:
                found_deps.append(dep)
        
        return True, f"Found {len(found_deps)}/{len(required_deps)} required dependencies"
        
    except Exception as e:
        return False, str(e)

def main():
    """Run all validation tests and report results."""
    print("🚀 BLITZFIRE C++ Optimizer Production Readiness Validation")
    print("=" * 60)
    
    tests = [
        ("Python Environment", test_python_environment),
        ("C++ Compiler Available", test_cpp_compiler_available),
        ("File Structure", test_file_structure),
        ("BLITZFIRE Modules", test_blitzfire_modules_loadable),
        ("C++ Compilation", test_basic_cpp_compilation),
        ("Requirements File", test_requirements_file)
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
    print(f"🚀 OVERALL BLITZFIRE PRODUCTION READINESS: {percentage:.1f}%")
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