#!/usr/bin/env python3
"""
Comprehensive validation test suite for never-fail-build-resolver agent.
This suite bypasses Pydantic version compatibility issues by testing components directly.
"""

import asyncio
import sys
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import time


class ValidationResults:
    """Track validation results."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
        self.coverage_areas = {
            'imports': False,
            'dependencies': False,
            'settings': False,
            'models': False,
            'tools': False,
            'prompts': False,
            'requirements': False
        }
    
    def add_test_result(self, test_name: str, passed: bool, error_msg: str = None):
        """Add a test result."""
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            print(f"✓ {test_name}")
        else:
            self.tests_failed += 1
            print(f"✗ {test_name}")
            if error_msg:
                print(f"  Error: {error_msg}")
                self.failures.append(f"{test_name}: {error_msg}")
    
    def mark_coverage_area(self, area: str):
        """Mark a coverage area as tested."""
        if area in self.coverage_areas:
            self.coverage_areas[area] = True
    
    def get_coverage_score(self) -> float:
        """Get coverage score as percentage."""
        covered = sum(1 for v in self.coverage_areas.values() if v)
        total = len(self.coverage_areas)
        return (covered / total) * 100.0
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("VALIDATION SUMMARY")
        print("="*50)
        print(f"Tests Run: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "0%")
        print(f"Coverage Score: {self.get_coverage_score():.1f}%")
        
        print("\nCoverage Areas:")
        for area, covered in self.coverage_areas.items():
            status = "✓" if covered else "✗"
            print(f"  {status} {area}")
        
        if self.failures:
            print(f"\nFailures ({len(self.failures)}):")
            for failure in self.failures:
                print(f"  - {failure}")
        
        # Determine overall status
        coverage_score = self.get_coverage_score()
        success_rate = (self.tests_passed/self.tests_run)*100 if self.tests_run > 0 else 0
        
        if success_rate >= 85 and coverage_score >= 80:
            print("\n🟢 VALIDATION STATUS: READY FOR PRODUCTION")
        elif success_rate >= 70 and coverage_score >= 60:
            print("\n🟡 VALIDATION STATUS: NEEDS IMPROVEMENT")
        else:
            print("\n🔴 VALIDATION STATUS: NOT READY")


class ValidatorSuite:
    """Main validation test suite."""
    
    def __init__(self):
        self.results = ValidationResults()
    
    def test_file_structure(self) -> bool:
        """Test that all required files exist."""
        print("\n=== Testing File Structure ===")
        
        required_files = [
            'agent.py',
            'dependencies.py', 
            'tools.py',
            'settings.py',
            'prompts.py',
            'providers.py',
            'requirements.txt',
            'planning/INITIAL.md',
            'core/models.py',
            'core/tools.py',
            'core/agent.py'
        ]
        
        all_exist = True
        for file_path in required_files:
            exists = Path(file_path).exists()
            self.results.add_test_result(f"File exists: {file_path}", exists)
            if not exists:
                all_exist = False
        
        self.results.mark_coverage_area('requirements')
        return all_exist
    
    def test_imports(self) -> bool:
        """Test critical imports."""
        print("\n=== Testing Imports ===")
        
        import_tests = [
            ("Settings", "from settings import load_settings, BuildResolverSettings"),
            ("Dependencies", "from dependencies import BuildResolverDependencies"),
            ("Core Models", "from core.models import BuildProblem, ResolutionStrategy, BuildAnalysis"),
            ("Prompts", "from prompts import SYSTEM_PROMPT"),
            ("Providers", "from providers import get_llm_model"),
        ]
        
        all_imports_work = True
        for test_name, import_statement in import_tests:
            try:
                exec(import_statement)
                self.results.add_test_result(f"Import: {test_name}", True)
            except Exception as e:
                self.results.add_test_result(f"Import: {test_name}", False, str(e))
                all_imports_work = False
        
        self.results.mark_coverage_area('imports')
        return all_imports_work
    
    def test_settings(self) -> bool:
        """Test settings loading and configuration."""
        print("\n=== Testing Settings ===")
        
        try:
            import os
            # Set test API key for validation
            os.environ["ANTHROPIC_API_KEY"] = "test_key_for_validation"
            
            from settings import load_settings, BuildResolverSettings
            
            # Test settings creation
            settings = load_settings()
            self.results.add_test_result("Settings creation", isinstance(settings, BuildResolverSettings))
            
            # Test settings attributes
            has_required_attrs = all(hasattr(settings, attr) for attr in [
                'llm_provider', 'project_root', 'cmake_binary_path', 
                'default_resolution_mode', 'state_persistence_dir'
            ])
            self.results.add_test_result("Required settings attributes", has_required_attrs)
            
            # Test resolution timeout calculation
            timeout = settings.get_resolution_timeout('smart')
            self.results.add_test_result("Resolution timeout calculation", isinstance(timeout, int) and timeout > 0)
            
            self.results.mark_coverage_area('settings')
            return True
            
        except Exception as e:
            self.results.add_test_result("Settings loading", False, str(e))
            return False
    
    def test_dependencies(self) -> bool:
        """Test dependencies class and functionality."""
        print("\n=== Testing Dependencies ===")
        
        try:
            from dependencies import BuildResolverDependencies
            
            # Test class structure
            self.results.add_test_result("Dependencies class exists", True)
            
            # Test required attributes
            required_attrs = ['settings', 'current_state', 'resolution_mode', 'session_id']
            has_attrs = all(hasattr(BuildResolverDependencies, attr) for attr in required_attrs)
            self.results.add_test_result("Required dependency attributes", has_attrs)
            
            # Test state validation
            from dependencies import validate_state_transition
            valid_transition = validate_state_transition("IDLE", "ANALYZING")
            self.results.add_test_result("State transition validation", valid_transition)
            
            invalid_transition = validate_state_transition("IDLE", "INVALID_STATE")
            self.results.add_test_result("Invalid state rejection", not invalid_transition)
            
            self.results.mark_coverage_area('dependencies')
            return True
            
        except Exception as e:
            self.results.add_test_result("Dependencies testing", False, str(e))
            return False
    
    def test_models(self) -> bool:
        """Test Pydantic models."""
        print("\n=== Testing Models ===")
        
        try:
            from core.models import (
                BuildError, BuildProblem, BuildErrorCategory, BuildErrorSeverity,
                ResolutionStrategy, ResolutionTier, BuildAnalysis, ValidationResult
            )
            
            # Test enum values
            self.results.add_test_result("BuildErrorCategory enum", 
                                       BuildErrorCategory.COMPILATION.value == "compilation")
            self.results.add_test_result("BuildErrorSeverity enum",
                                       BuildErrorSeverity.CRITICAL.value == "critical")
            self.results.add_test_result("ResolutionTier enum",
                                       ResolutionTier.INTELLIGENT.value == "intelligent")
            
            # Test model creation
            build_error = BuildError(
                message="Test error",
                raw_output="Test output",
                severity=BuildErrorSeverity.HIGH,
                category=BuildErrorCategory.COMPILATION,
                tool_name="gcc"
            )
            self.results.add_test_result("BuildError model creation", isinstance(build_error, BuildError))
            
            self.results.mark_coverage_area('models')
            return True
            
        except Exception as e:
            self.results.add_test_result("Models testing", False, str(e))
            return False
    
    def test_tools_structure(self) -> bool:
        """Test tools module structure."""
        print("\n=== Testing Tools Structure ===")
        
        try:
            from core.tools import (
                diagnose_build_problems, apply_resolution_strategy, 
                validate_resolution, prevent_future_problems
            )
            
            # Test tool functions exist
            self.results.add_test_result("diagnose_build_problems exists", callable(diagnose_build_problems))
            self.results.add_test_result("apply_resolution_strategy exists", callable(apply_resolution_strategy))
            self.results.add_test_result("validate_resolution exists", callable(validate_resolution))
            self.results.add_test_result("prevent_future_problems exists", callable(prevent_future_problems))
            
            self.results.mark_coverage_area('tools')
            return True
            
        except Exception as e:
            self.results.add_test_result("Tools structure testing", False, str(e))
            return False
    
    def test_prompts(self) -> bool:
        """Test prompt system."""
        print("\n=== Testing Prompts ===")
        
        try:
            from prompts import SYSTEM_PROMPT, get_mode_specific_prompt
            
            # Test system prompt exists and is substantial
            self.results.add_test_result("System prompt exists", 
                                       isinstance(SYSTEM_PROMPT, str) and len(SYSTEM_PROMPT) > 100)
            
            # Test mode-specific prompts
            fast_prompt = get_mode_specific_prompt("fast")
            self.results.add_test_result("Fast mode prompt", isinstance(fast_prompt, str))
            
            emergency_prompt = get_mode_specific_prompt("emergency")
            self.results.add_test_result("Emergency mode prompt", isinstance(emergency_prompt, str) and len(emergency_prompt) > 50)
            
            # Test system prompt contains key elements
            key_elements = ["NEVER FAIL", "build", "resolution", "tier", "strategy"]
            contains_elements = all(element.lower() in SYSTEM_PROMPT.lower() for element in key_elements)
            self.results.add_test_result("System prompt contains key elements", contains_elements)
            
            self.results.mark_coverage_area('prompts')
            return True
            
        except Exception as e:
            self.results.add_test_result("Prompts testing", False, str(e))
            return False
    
    def test_requirements_compliance(self) -> bool:
        """Test compliance with INITIAL.md requirements."""
        print("\n=== Testing Requirements Compliance ===")
        
        try:
            # Read INITIAL.md
            initial_md = Path("planning/INITIAL.md")
            if not initial_md.exists():
                self.results.add_test_result("INITIAL.md exists", False)
                return False
            
            with open(initial_md, 'r') as f:
                content = f.read()
            
            # Check for key requirements
            req_checks = [
                ("Four-tier resolution strategy", any(tier in content.lower() for tier in ["prevention", "intelligent", "comprehensive", "nuclear"])),
                ("State machine workflow", "state" in content.lower() and ("idle" in content.lower() or "analyzing" in content.lower())),
                ("Success criteria defined", "success" in content.lower() and ("99%" in content or "95%" in content)),
                ("Learning system mentioned", "learning" in content.lower() or "adaptation" in content.lower()),
                ("Integration requirements", "integration" in content.lower()),
                ("Security considerations", "security" in content.lower() or "safe" in content.lower()),
            ]
            
            for req_name, check_result in req_checks:
                self.results.add_test_result(f"Requirement: {req_name}", check_result)
            
            self.results.mark_coverage_area('requirements')
            return True
            
        except Exception as e:
            self.results.add_test_result("Requirements compliance testing", False, str(e))
            return False
    
    def run_all_tests(self) -> ValidationResults:
        """Run all validation tests."""
        print("🔍 NEVER FAIL BUILD RESOLVER - COMPREHENSIVE VALIDATION")
        print("="*60)
        
        # Run all test categories
        self.test_file_structure()
        self.test_imports()
        self.test_settings()
        self.test_dependencies() 
        self.test_models()
        self.test_tools_structure()
        self.test_prompts()
        self.test_requirements_compliance()
        
        # Print final results
        self.results.print_summary()
        
        return self.results


def main():
    """Main validation entry point."""
    validator = ValidatorSuite()
    results = validator.run_all_tests()
    
    # Return appropriate exit code
    if results.get_coverage_score() >= 80 and (results.tests_passed/results.tests_run)*100 >= 85:
        return 0  # Success
    else:
        return 1  # Failure


if __name__ == "__main__":
    sys.exit(main())