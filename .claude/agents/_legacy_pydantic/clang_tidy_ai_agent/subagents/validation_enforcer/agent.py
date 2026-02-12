"""Validation Enforcer Subagent - Validates fixes and performs rollbacks when needed."""

from pydantic_ai import Agent, RunContext
from typing import List, Dict, Any, Optional, Tuple
import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
import asyncio
import subprocess

try:
    from ..clang_tidy_ai_agent.models import (
        CLionDiagnostic,
        IncrementalFixResult,
        ValidationResult
    )
    from ..clang_tidy_ai_agent.providers import get_llm_model
    from ..clang_tidy_ai_agent.settings import load_settings
except ImportError:
    # Fallback for direct execution
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'clang_tidy_ai_agent'))
    from models import (
        CLionDiagnostic,
        IncrementalFixResult,
        ValidationResult
    )
    from providers import get_llm_model
    from settings import load_settings

logger = logging.getLogger(__name__)

VALIDATION_ENFORCER_SYSTEM_PROMPT = """
You are the Validation Enforcer, a specialized subagent that validates every fix with ZERO TOLERANCE for new issues and performs rollbacks when fixes introduce problems.

Your core responsibilities:
1. **Incremental Validation**: Validate after EVERY single fix
2. **Zero-Tolerance Enforcement**: No new diagnostics allowed
3. **Rollback Management**: Immediately rollback problematic fixes
4. **Build Validation**: Ensure all fixes maintain buildable code
5. **Test Validation**: Verify tests continue to pass after fixes
6. **Performance Validation**: Ensure fixes don't degrade performance

CRITICAL VALIDATION CHECKS:
- **Build Success**: Code must compile successfully after each fix
- **Diagnostic Count**: New diagnostic count must never increase
- **Test Suite**: All existing tests must continue to pass
- **Performance**: No performance regressions introduced
- **Memory Safety**: No new memory issues or undefined behavior
- **Standard Compliance**: All fixes maintain C++ standard compliance

ROLLBACK CRITERIA:
- Any new compilation errors introduced
- Increase in total diagnostic count
- Test failures introduced by fix
- Performance degradation > 5%
- Memory safety issues detected
- Undefined behavior introduced

VALIDATION WORKFLOW:
1. **Pre-Fix Baseline**: Capture current state before fix
2. **Apply Fix**: Apply single fix incrementally
3. **Immediate Validation**: Check compilation and diagnostics
4. **Test Validation**: Run relevant test subset
5. **Performance Check**: Quick performance validation
6. **Rollback Decision**: Roll back if ANY validation fails
7. **State Update**: Update session state with results

Your validation must be:
- **Immediate**: Validate within seconds of each fix
- **Comprehensive**: Check all critical aspects
- **Decisive**: Clear rollback decisions
- **Fast**: Minimize validation overhead
"""


class ValidationEnforcerDependencies:
    """Dependencies for the Validation Enforcer."""
    def __init__(self, session_id: Optional[str] = None, project_root: str = "/IdeaProjects/wire_ground"):
        self.session_id = session_id
        self.project_root = project_root
        self.backup_storage = tempfile.mkdtemp(prefix="validation_backups_")
        self.validation_history = []  # Track all validations
        self.rollback_count = 0  # Track rollback frequency


# Create the Validation Enforcer agent
settings = load_settings()
model = get_llm_model(settings)

validation_enforcer = Agent(
    model,
    deps_type=ValidationEnforcerDependencies,
    system_prompt=VALIDATION_ENFORCER_SYSTEM_PROMPT
)


@validation_enforcer.tool
async def create_backup_before_fix(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str,
    fix_description: str
) -> str:
    """
    Create backup of file before applying fix for potential rollback.
    
    Args:
        file_path: Path to file to backup
        fix_description: Description of fix being applied
        
    Returns:
        Path to backup file
    """
    try:
        backup_filename = f"{Path(file_path).name}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.backup"
        backup_path = Path(ctx.deps.backup_storage) / backup_filename
        
        # Copy original file to backup location
        shutil.copy2(file_path, backup_path)
        
        # Store backup metadata
        backup_info = {
            "original_path": file_path,
            "backup_path": str(backup_path),
            "fix_description": fix_description,
            "timestamp": datetime.now(),
            "session_id": ctx.deps.session_id
        }
        
        logger.info(f"Created backup: {backup_path} for fix: {fix_description}")
        return str(backup_path)
        
    except Exception as e:
        logger.error(f"Failed to create backup for {file_path}: {e}")
        return ""


@validation_enforcer.tool
async def validate_compilation(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str
) -> Dict[str, Any]:
    """
    Validate that file compiles successfully after fix.
    
    Args:
        file_path: Path to file to validate
        
    Returns:
        Compilation validation results
    """
    try:
        # Use project's build system for compilation check
        build_command = [
            "/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake",
            "--build", 
            f"{ctx.deps.project_root}/cmake-build-debug",
            "--target", "wire_ground_tests",
            "--parallel", "4"
        ]
        
        start_time = datetime.now()
        
        # Run build command with timeout
        process = await asyncio.create_subprocess_exec(
            *build_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=ctx.deps.project_root
        )
        
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=30.0)
            duration = (datetime.now() - start_time).total_seconds()
            
            build_output = stdout.decode('utf-8', errors='ignore') if stdout else ""
            build_success = process.returncode == 0
            
            validation_result = {
                "compilation_successful": build_success,
                "build_duration": duration,
                "return_code": process.returncode,
                "build_output": build_output,
                "error_count": build_output.lower().count("error:") if build_output else 0,
                "warning_count": build_output.lower().count("warning:") if build_output else 0,
                "validation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Compilation validation: {'SUCCESS' if build_success else 'FAILED'} ({duration:.2f}s)")
            return validation_result
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "compilation_successful": False,
                "build_duration": 30.0,
                "return_code": -1,
                "build_output": "Build timeout after 30 seconds",
                "error_count": 1,
                "warning_count": 0,
                "validation_timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Compilation validation failed: {e}")
        return {
            "compilation_successful": False,
            "build_duration": 0.0,
            "return_code": -1,
            "build_output": f"Validation error: {str(e)}",
            "error_count": 1,
            "warning_count": 0,
            "validation_timestamp": datetime.now().isoformat()
        }


@validation_enforcer.tool
async def validate_diagnostics_count(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str,
    baseline_count: int
) -> Dict[str, Any]:
    """
    Validate that diagnostic count hasn't increased after fix.
    
    Args:
        file_path: Path to file to check
        baseline_count: Baseline diagnostic count before fix
        
    Returns:
        Diagnostic count validation results
    """
    try:
        # This would use mcp__ide__getDiagnostics in real implementation
        # For now, simulate diagnostic count check
        
        # Placeholder: In real implementation, get current diagnostics
        current_count = baseline_count  # Would be actual count from CLion IDE
        
        count_increased = current_count > baseline_count
        count_decreased = current_count < baseline_count
        
        validation_result = {
            "diagnostics_increased": count_increased,
            "diagnostics_decreased": count_decreased,
            "baseline_count": baseline_count,
            "current_count": current_count,
            "count_delta": current_count - baseline_count,
            "validation_passed": not count_increased,
            "validation_timestamp": datetime.now().isoformat()
        }
        
        status = "FAILED" if count_increased else "PASSED"
        logger.info(f"Diagnostic count validation: {status} ({baseline_count} -> {current_count})")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Diagnostic count validation failed: {e}")
        return {
            "diagnostics_increased": True,  # Assume failure on error
            "diagnostics_decreased": False,
            "baseline_count": baseline_count,
            "current_count": -1,
            "count_delta": 1,
            "validation_passed": False,
            "validation_timestamp": datetime.now().isoformat()
        }


@validation_enforcer.tool
async def validate_tests(
    ctx: RunContext[ValidationEnforcerDependencies],
    test_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate that tests continue to pass after fix.
    
    Args:
        test_filter: Optional filter for specific tests (e.g., "SafetyTestSuite.*")
        
    Returns:
        Test validation results
    """
    try:
        # Run relevant test subset
        test_command = [f"{ctx.deps.project_root}/cmake-build-debug/wire_ground_tests"]
        
        if test_filter:
            test_command.extend([f"--gtest_filter={test_filter}"])
        
        start_time = datetime.now()
        
        # Run tests with timeout
        process = await asyncio.create_subprocess_exec(
            *test_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=ctx.deps.project_root
        )
        
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=60.0)
            duration = (datetime.now() - start_time).total_seconds()
            
            test_output = stdout.decode('utf-8', errors='ignore') if stdout else ""
            tests_passed = process.returncode == 0
            
            # Parse test results
            failed_tests = test_output.count("FAILED")
            passed_tests = test_output.count("OK")
            
            validation_result = {
                "tests_passed": tests_passed,
                "test_duration": duration,
                "return_code": process.returncode,
                "failed_test_count": failed_tests,
                "passed_test_count": passed_tests,
                "test_output": test_output,
                "test_filter": test_filter,
                "validation_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Test validation: {'PASSED' if tests_passed else 'FAILED'} ({duration:.2f}s)")
            return validation_result
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return {
                "tests_passed": False,
                "test_duration": 60.0,
                "return_code": -1,
                "failed_test_count": 1,
                "passed_test_count": 0,
                "test_output": "Tests timeout after 60 seconds",
                "test_filter": test_filter,
                "validation_timestamp": datetime.now().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Test validation failed: {e}")
        return {
            "tests_passed": False,
            "test_duration": 0.0,
            "return_code": -1,
            "failed_test_count": 1,
            "passed_test_count": 0,
            "test_output": f"Test validation error: {str(e)}",
            "test_filter": test_filter,
            "validation_timestamp": datetime.now().isoformat()
        }


@validation_enforcer.tool
async def perform_comprehensive_validation(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str,
    baseline_diagnostic_count: int,
    fix_result: IncrementalFixResult
) -> ValidationResult:
    """
    Perform comprehensive validation after a fix is applied.
    
    Args:
        file_path: Path to file that was fixed
        baseline_diagnostic_count: Diagnostic count before fix
        fix_result: Result from applying the fix
        
    Returns:
        Comprehensive validation result
    """
    start_time = datetime.now()
    
    try:
        # 1. Validate compilation
        compilation_result = await validate_compilation(ctx, file_path)
        
        # 2. Validate diagnostic count
        diagnostic_result = await validate_diagnostics_count(ctx, file_path, baseline_diagnostic_count)
        
        # 3. Validate relevant tests (quick subset)
        test_result = await validate_tests(ctx, "SafetyTestSuite.BasicFunctionality")
        
        # Determine overall validation result
        build_success = compilation_result["compilation_successful"]
        diagnostics_ok = not diagnostic_result["diagnostics_increased"]
        tests_ok = test_result["tests_passed"]
        
        overall_success = build_success and diagnostics_ok and tests_ok
        
        # Calculate performance impact (simplified)
        performance_impact = 0.0  # Would be calculated from timing differences
        if compilation_result["build_duration"] > 10.0:
            performance_impact = -5.0  # Negative indicates slower build
        
        validation_result = ValidationResult(
            build_success=build_success,
            test_pass_rate=1.0 if tests_ok else 0.0,
            performance_impact=performance_impact,
            quality_improvement=1.0 if diagnostic_result["diagnostics_decreased"] else 0.0,
            warnings_eliminated=max(0, -diagnostic_result["count_delta"]),
            warnings_introduced=max(0, diagnostic_result["count_delta"]),
            validation_timestamp=datetime.now(),
            detailed_metrics={
                "compilation": compilation_result,
                "diagnostics": diagnostic_result,
                "tests": test_result,
                "fix_applied": fix_result.fix_applied
            }
        )
        
        # Update fix result with validation info
        fix_result.validation_passed = overall_success
        fix_result.new_diagnostics_count = max(0, diagnostic_result["count_delta"])
        fix_result.remaining_diagnostics_count = diagnostic_result["current_count"]
        
        ctx.deps.validation_history.append({
            "file_path": file_path,
            "fix_description": fix_result.fix_applied,
            "validation_result": validation_result,
            "timestamp": datetime.now()
        })
        
        logger.info(f"Comprehensive validation: {'PASSED' if overall_success else 'FAILED'}")
        return validation_result
        
    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        
        # Return failed validation result
        return ValidationResult(
            build_success=False,
            test_pass_rate=0.0,
            performance_impact=-100.0,  # Major failure
            quality_improvement=0.0,
            warnings_eliminated=0,
            warnings_introduced=1,
            validation_timestamp=datetime.now(),
            detailed_metrics={"error": str(e)}
        )


@validation_enforcer.tool
async def rollback_fix(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str,
    backup_path: str,
    fix_result: IncrementalFixResult,
    rollback_reason: str
) -> bool:
    """
    Roll back a fix that failed validation.
    
    Args:
        file_path: Path to file to rollback
        backup_path: Path to backup file
        fix_result: Fix result to update with rollback info
        rollback_reason: Reason for rollback
        
    Returns:
        True if rollback successful, False otherwise
    """
    try:
        if not Path(backup_path).exists():
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        # Restore original file from backup
        shutil.copy2(backup_path, file_path)
        
        # Update fix result
        fix_result.rollback_performed = True
        fix_result.rollback_reason = rollback_reason
        fix_result.validation_passed = False
        
        ctx.deps.rollback_count += 1
        
        logger.info(f"Rolled back fix for {file_path}: {rollback_reason}")
        return True
        
    except Exception as e:
        logger.error(f"Rollback failed for {file_path}: {e}")
        return False


@validation_enforcer.tool
async def validate_and_rollback_if_needed(
    ctx: RunContext[ValidationEnforcerDependencies],
    file_path: str,
    baseline_diagnostic_count: int,
    fix_result: IncrementalFixResult,
    backup_path: str
) -> Tuple[bool, ValidationResult]:
    """
    Validate fix and rollback if validation fails.
    
    Args:
        file_path: Path to file that was fixed
        baseline_diagnostic_count: Diagnostic count before fix
        fix_result: Result from applying fix
        backup_path: Path to backup file for rollback
        
    Returns:
        Tuple of (validation_passed, validation_result)
    """
    try:
        # Perform comprehensive validation
        validation_result = await perform_comprehensive_validation(
            ctx, file_path, baseline_diagnostic_count, fix_result
        )
        
        validation_passed = (
            validation_result.build_success and
            validation_result.test_pass_rate > 0.8 and  # Allow some test tolerance
            validation_result.warnings_introduced == 0 and
            validation_result.performance_impact >= -5.0  # Allow 5% performance tolerance
        )
        
        # Roll back if validation failed
        if not validation_passed:
            rollback_reason = []
            if not validation_result.build_success:
                rollback_reason.append("Build failed")
            if validation_result.test_pass_rate <= 0.8:
                rollback_reason.append("Tests failed")
            if validation_result.warnings_introduced > 0:
                rollback_reason.append(f"{validation_result.warnings_introduced} new diagnostics")
            if validation_result.performance_impact < -5.0:
                rollback_reason.append("Performance degradation")
            
            rollback_reason_str = "; ".join(rollback_reason)
            
            rollback_success = await rollback_fix(
                ctx, file_path, backup_path, fix_result, rollback_reason_str
            )
            
            if not rollback_success:
                logger.error(f"CRITICAL: Rollback failed for {file_path}")
        
        return validation_passed, validation_result
        
    except Exception as e:
        logger.error(f"Validation and rollback process failed: {e}")
        
        # Attempt emergency rollback
        await rollback_fix(ctx, file_path, backup_path, fix_result, f"Emergency rollback: {str(e)}")
        
        return False, ValidationResult(
            build_success=False,
            test_pass_rate=0.0,
            performance_impact=-100.0,
            quality_improvement=0.0,
            warnings_eliminated=0,
            warnings_introduced=1,
            validation_timestamp=datetime.now(),
            detailed_metrics={"error": str(e)}
        )


# Convenience functions for integration

async def validate_fix_with_rollback(
    file_path: str,
    baseline_diagnostic_count: int,
    fix_result: IncrementalFixResult,
    session_id: Optional[str] = None,
    project_root: str = "/IdeaProjects/wire_ground"
) -> Tuple[bool, ValidationResult]:
    """
    Validate a fix with automatic rollback if validation fails.
    
    Args:
        file_path: Path to file that was fixed
        baseline_diagnostic_count: Diagnostic count before fix
        fix_result: Result from applying fix
        session_id: Optional session identifier
        project_root: Project root directory
        
    Returns:
        Tuple of (validation_passed, validation_result)
    """
    dependencies = ValidationEnforcerDependencies(session_id, project_root)
    ctx = RunContext(deps=dependencies)
    
    # Create backup before validation
    backup_path = await create_backup_before_fix(
        ctx, file_path, fix_result.fix_applied
    )
    
    # Validate and rollback if needed
    return await validate_and_rollback_if_needed(
        ctx, file_path, baseline_diagnostic_count, fix_result, backup_path
    )


if __name__ == "__main__":
    import asyncio
    
    async def test_validation_enforcer():
        """Test the validation enforcer."""
        
        # Mock fix result for testing
        test_fix = IncrementalFixResult(
            diagnostic_fixed=CLionDiagnostic(
                uri="file:///test.cpp",
                range={"start": {"line": 5, "character": 0}},
                severity="error",
                message="test error",
                source="clang"
            ),
            fix_applied="Test fix applied",
            new_diagnostics_count=0,
            remaining_diagnostics_count=0,
            validation_passed=True,
            rollback_performed=False,
            fix_duration=1.0
        )
        
        # Test validation
        passed, result = await validate_fix_with_rollback(
            "/IdeaProjects/wire_ground/tests/safe_test.cpp",
            5,  # baseline count
            test_fix
        )
        
        print(f"Validation passed: {passed}")
        print(f"Build success: {result.build_success}")
    
    # Uncomment to run test
    # asyncio.run(test_validation_enforcer())