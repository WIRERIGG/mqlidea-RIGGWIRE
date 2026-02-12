"""Tools for build diagnosis, resolution, and validation in Never Fail Build Resolver."""

import asyncio
import subprocess
import re
import time
import shutil
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import hashlib
import json

from pydantic_ai import RunContext

from .dependencies import BuildResolverDependencies
from .models import (
    BuildProblem, BuildError, BuildErrorSeverity, BuildErrorCategory,
    ResolutionStrategy, ResolutionTier, ResolutionStatus, BuildAnalysis,
    ResolutionResult, ResolutionAttempt, SystemDiagnostics, 
    BuildConfiguration, ValidationResult, PreventionRule,
    BuildSystem, PerformanceMetrics
)

# ============================================================================
# Build Diagnosis Tools
# ============================================================================

async def diagnose_build_problems(
    ctx: RunContext[BuildResolverDependencies],
    build_command: str,
    working_directory: str = None,
    timeout_seconds: int = 300
) -> BuildAnalysis:
    """Diagnose build problems by analyzing build failures."""
    
    deps = ctx.deps
    logger = deps.logger
    
    start_time = time.time()
    logger.info(f"Starting build diagnosis for command: {build_command}")
    
    try:
        # Set working directory
        work_dir = Path(working_directory) if working_directory else deps.settings.project_root
        
        # Execute build command and capture output
        build_success, build_output = await _execute_build_command(
            build_command, work_dir, timeout_seconds
        )
        
        # Parse build errors from output
        build_errors = _parse_build_errors(build_output)
        
        # Create build problem
        problem_id = f"build_problem_{int(time.time())}"
        build_problem = BuildProblem(
            problem_id=problem_id,
            build_errors=build_errors,
            build_system=_detect_build_system(build_command),
            build_command=build_command,
            working_directory=work_dir,
            environment_snapshot=dict(os.environ)
        )
        
        # Get system diagnostics
        system_diagnostics = deps.system_monitor.get_system_diagnostics()
        
        # Get build configuration
        build_config = await _analyze_build_configuration(deps, work_dir)
        
        # Perform root cause analysis
        root_cause, contributing_factors = _analyze_root_cause(build_errors, system_diagnostics, build_config)
        
        # Determine severity and recommended tier
        severity = _assess_overall_severity(build_errors)
        recommended_tier = _recommend_resolution_tier(severity, build_errors, system_diagnostics)
        
        # Create analysis
        analysis = BuildAnalysis(
            analysis_id=f"analysis_{problem_id}",
            build_problem=build_problem,
            system_diagnostics=system_diagnostics,
            build_configuration=build_config,
            root_cause_analysis=root_cause,
            contributing_factors=contributing_factors,
            severity_assessment=severity,
            impact_analysis=f"Build failure affects {len(build_problem.affected_targets)} targets",
            recommended_tier=recommended_tier,
            recommended_strategies=_recommend_strategies(build_errors, recommended_tier),
            prevention_opportunities=_identify_prevention_opportunities(build_errors),
            confidence_score=_calculate_confidence_score(build_errors, system_diagnostics)
        )
        
        # Cache analysis if enabled
        if deps.settings.cache_build_analysis:
            problem_hash = hashlib.md5(build_output.encode(), usedforsecurity=False).hexdigest()
            deps.cache_manager.cache_analysis(problem_hash, analysis.dict())
        
        # Record performance metrics
        duration = time.time() - start_time
        deps.performance_tracker.record_metrics(
            "diagnose_build_problems", duration, 
            memory_usage=0, cpu_usage=0
        )
        
        logger.info(f"Build diagnosis completed in {duration:.2f}s. Found {len(build_errors)} errors.")
        
        return analysis
        
    except Exception as e:
        logger.error(f"Build diagnosis failed: {e}")
        raise

async def _execute_build_command(command: str, work_dir: Path, timeout: int) -> Tuple[bool, str]:
    """Execute build command and capture output."""
    try:
        # Split command into parts
        cmd_parts = command.split()
        
        # Execute command
        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            cwd=work_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            env=os.environ.copy()
        )
        
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(), timeout=timeout)
            output = stdout.decode('utf-8', errors='replace')
            success = process.returncode == 0
            return success, output
            
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return False, f"Build command timed out after {timeout} seconds"
            
    except Exception as e:
        return False, f"Failed to execute build command: {e}"

def _parse_build_errors(build_output: str) -> List[BuildError]:
    """Parse build errors from build tool output."""
    errors = []
    
    # Common error patterns
    error_patterns = [
        # GCC/Clang compilation errors
        (r'([^:]+):(\d+):(\d+):\s*(error|warning):\s*(.+)', BuildErrorCategory.COMPILATION),
        # CMake configuration errors  
        (r'CMake Error[^:]*:\s*(.+)', BuildErrorCategory.CONFIGURATION),
        # Linker errors
        (r'(ld|collect2):\s*(error|fatal error):\s*(.+)', BuildErrorCategory.LINKING),
        # Make errors
        (r'make(\[\d+\])?: \*\*\* (.+)', BuildErrorCategory.COMPILATION),
        # Ninja errors
        (r'FAILED:\s*(.+)', BuildErrorCategory.COMPILATION),
        # Generic error patterns
        (r'error:\s*(.+)', BuildErrorCategory.UNKNOWN),
        (r'fatal error:\s*(.+)', BuildErrorCategory.UNKNOWN),
    ]
    
    lines = build_output.split('\n')
    
    for line_num, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        for pattern, category in error_patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                groups = match.groups()
                
                if len(groups) >= 5:  # File:line:col:severity:message format
                    file_path = Path(groups[0]) if groups[0] else None
                    line_number = int(groups[1]) if groups[1].isdigit() else None
                    column_number = int(groups[2]) if groups[2].isdigit() else None
                    severity_str = groups[3].lower()
                    message = groups[4]
                elif len(groups) >= 1:  # Simple message format
                    file_path = None
                    line_number = None
                    column_number = None
                    severity_str = "error"
                    message = groups[-1]
                else:
                    continue
                
                # Map severity
                severity = BuildErrorSeverity.HIGH
                if "warning" in severity_str:
                    severity = BuildErrorSeverity.WARNING
                elif "fatal" in severity_str or "critical" in severity_str:
                    severity = BuildErrorSeverity.CRITICAL
                
                # Get context lines
                context_start = max(0, line_num - 2)
                context_end = min(len(lines), line_num + 3)
                context_lines = lines[context_start:context_end]
                
                # Determine tool name
                tool_name = "unknown"
                if "cmake" in line.lower():
                    tool_name = "cmake"
                elif "make" in line.lower():
                    tool_name = "make"
                elif "ninja" in line.lower():
                    tool_name = "ninja"
                elif any(compiler in line.lower() for compiler in ["gcc", "g++", "clang", "clang++"]):
                    tool_name = "compiler"
                elif "ld" in line.lower() or "collect2" in line.lower():
                    tool_name = "linker"
                
                error = BuildError(
                    line_number=line_number,
                    column_number=column_number,
                    file_path=file_path,
                    message=message,
                    raw_output=line,
                    severity=severity,
                    category=category,
                    tool_name=tool_name,
                    context_lines=context_lines
                )
                
                errors.append(error)
                break
    
    return errors

def _detect_build_system(build_command: str) -> BuildSystem:
    """Detect build system from build command."""
    cmd_lower = build_command.lower()
    
    if "cmake" in cmd_lower:
        return BuildSystem.CMAKE
    elif "ninja" in cmd_lower:
        return BuildSystem.NINJA
    elif "make" in cmd_lower:
        return BuildSystem.MAKE
    else:
        return BuildSystem.CUSTOM

async def _analyze_build_configuration(deps: BuildResolverDependencies, work_dir: Path) -> BuildConfiguration:
    """Analyze build system configuration."""
    
    config = BuildConfiguration()
    
    try:
        # CMake configuration
        if (work_dir / "CMakeLists.txt").exists():
            config.cmake_version = deps.cmake_interface.get_version()
            
            build_dir = work_dir / deps.settings.build_directory
            if build_dir.exists():
                config.cmake_cache_vars = deps.cmake_interface.get_cache_variables(build_dir)
        
        # TODO: Add analysis for other build systems
        
    except Exception as e:
        deps.logger.warning(f"Build configuration analysis failed: {e}")
    
    return config

def _analyze_root_cause(errors: List[BuildError], diagnostics: SystemDiagnostics, config: BuildConfiguration) -> Tuple[str, List[str]]:
    """Analyze root cause of build problems."""
    
    if not errors:
        return "No errors found", []
    
    # Categorize errors
    error_categories = {}
    for error in errors:
        category = error.category
        if category not in error_categories:
            error_categories[category] = []
        error_categories[category].append(error)
    
    # Determine primary root cause
    if BuildErrorCategory.DEPENDENCY in error_categories:
        root_cause = "Missing or incompatible dependencies"
    elif BuildErrorCategory.CONFIGURATION in error_categories:
        root_cause = "Build system configuration issues"
    elif BuildErrorCategory.TOOLCHAIN in error_categories:
        root_cause = "Compiler or toolchain problems"
    elif BuildErrorCategory.COMPILATION in error_categories:
        root_cause = "C++ compilation errors"
    elif BuildErrorCategory.LINKING in error_categories:
        root_cause = "Linker errors"
    else:
        root_cause = "Multiple build system issues"
    
    # Contributing factors
    contributing_factors = []
    
    # Check system resources
    if diagnostics.disk_space.get('percent_used', 0) > 90:
        contributing_factors.append("Low disk space")
    
    if diagnostics.memory_info.get('percent_used', 0) > 90:
        contributing_factors.append("Low memory")
    
    # Check common configuration issues
    if not config.cmake_cache_vars:
        contributing_factors.append("Missing CMake configuration")
    
    return root_cause, contributing_factors

def _assess_overall_severity(errors: List[BuildError]) -> BuildErrorSeverity:
    """Assess overall severity of build problems."""
    if not errors:
        return BuildErrorSeverity.LOW
    
    severities = [error.severity for error in errors]
    
    if BuildErrorSeverity.CRITICAL in severities:
        return BuildErrorSeverity.CRITICAL
    elif BuildErrorSeverity.HIGH in severities:
        return BuildErrorSeverity.HIGH
    elif BuildErrorSeverity.MEDIUM in severities:
        return BuildErrorSeverity.MEDIUM
    else:
        return BuildErrorSeverity.LOW

def _recommend_resolution_tier(severity: BuildErrorSeverity, errors: List[BuildError], diagnostics: SystemDiagnostics) -> ResolutionTier:
    """Recommend resolution tier based on problem analysis."""
    
    # Critical errors or system issues need comprehensive approach
    if severity == BuildErrorSeverity.CRITICAL:
        return ResolutionTier.COMPREHENSIVE
    
    # Check for complex multi-category problems
    categories = set(error.category for error in errors)
    if len(categories) > 2:
        return ResolutionTier.COMPREHENSIVE
    
    # System resource issues need intelligent resolution
    if (diagnostics.disk_space.get('percent_used', 0) > 80 or 
        diagnostics.memory_info.get('percent_used', 0) > 80):
        return ResolutionTier.INTELLIGENT
    
    # Simple problems can use intelligent resolution
    if len(errors) <= 5 and severity in [BuildErrorSeverity.LOW, BuildErrorSeverity.WARNING]:
        return ResolutionTier.INTELLIGENT
    
    return ResolutionTier.INTELLIGENT  # Default to intelligent

def _recommend_strategies(errors: List[BuildError], tier: ResolutionTier) -> List[str]:
    """Recommend resolution strategies based on errors and tier."""
    strategies = []
    
    categories = set(error.category for error in errors)
    
    if BuildErrorCategory.DEPENDENCY in categories:
        strategies.append("resolve_dependency_conflicts")
    
    if BuildErrorCategory.CONFIGURATION in categories:
        strategies.append("reconfigure_build_system")
    
    if BuildErrorCategory.COMPILATION in categories:
        strategies.append("fix_compilation_errors")
    
    if BuildErrorCategory.LINKING in categories:
        strategies.append("resolve_linking_issues")
    
    if tier == ResolutionTier.COMPREHENSIVE:
        strategies.append("comprehensive_rebuild")
    
    if tier == ResolutionTier.NUCLEAR:
        strategies.append("nuclear_clean_rebuild")
    
    return strategies or ["general_build_fix"]

def _identify_prevention_opportunities(errors: List[BuildError]) -> List[str]:
    """Identify prevention opportunities from errors."""
    opportunities = []
    
    categories = set(error.category for error in errors)
    
    if BuildErrorCategory.DEPENDENCY in categories:
        opportunities.append("Implement dependency version monitoring")
    
    if BuildErrorCategory.CONFIGURATION in categories:
        opportunities.append("Add build configuration validation")
    
    if BuildErrorCategory.COMPILATION in categories:
        opportunities.append("Enable continuous compilation checking")
    
    return opportunities

def _calculate_confidence_score(errors: List[BuildError], diagnostics: SystemDiagnostics) -> float:
    """Calculate confidence score for the analysis."""
    base_score = 0.8
    
    # Reduce confidence if no errors found but build failed
    if not errors:
        base_score = 0.3
    
    # Reduce confidence if system diagnostics are incomplete
    if not diagnostics.compiler_versions:
        base_score -= 0.1
    
    if not diagnostics.tool_versions:
        base_score -= 0.1
    
    return max(0.0, min(1.0, base_score))

# ============================================================================
# Resolution Application Tools  
# ============================================================================

async def apply_resolution_strategy(
    ctx: RunContext[BuildResolverDependencies],
    strategy: ResolutionStrategy,
    backup_enabled: bool = True
) -> ResolutionResult:
    """Apply a resolution strategy to fix build problems."""
    
    deps = ctx.deps
    logger = deps.logger
    
    start_time = time.time()
    attempt_id = f"attempt_{int(time.time())}"
    
    logger.info(f"Applying resolution strategy: {strategy.strategy_name}")
    
    # Create backup if required
    backup_info = None
    if backup_enabled and strategy.backup_required:
        try:
            # Backup critical files/directories
            backup_items = [
                deps.settings.project_root / "CMakeLists.txt",
                deps.settings.get_build_directory_path()
            ]
            backup_items = [item for item in backup_items if item.exists()]
            
            if backup_items:
                backup_info = deps.backup_manager.create_backup(backup_items, f"strategy_{strategy.strategy_id}")
                logger.info(f"Created backup: {backup_info.backup_id}")
        except Exception as e:
            logger.warning(f"Backup creation failed: {e}")
    
    # Apply resolution steps
    attempt = ResolutionAttempt(
        attempt_id=attempt_id,
        strategy_used=strategy.strategy_id,
        status=ResolutionStatus.IN_PROGRESS,
        steps_completed=0,
        total_steps=len(strategy.resolution_steps),
        duration_seconds=0,
        output_log="",
        error_log=""
    )
    
    try:
        output_log = []
        error_log = []
        
        for step_idx, step in enumerate(strategy.resolution_steps):
            logger.info(f"Executing step {step.step_id}: {step.description}")
            
            step_start_time = time.time()
            
            # Execute step command if provided
            if step.command:
                try:
                    # Use shell=False for security - split command into list
                    import shlex
                    command_args = shlex.split(step.command) if isinstance(step.command, str) else step.command
                    result = subprocess.run(
                        command_args,
                        shell=False,
                        cwd=deps.build_context.project_root,
                        capture_output=True,
                        text=True,
                        timeout=step.estimated_duration_seconds * 2  # 2x timeout buffer
                    )
                    
                    output_log.append(f"Step {step.step_id}: {result.stdout}")
                    
                    if result.returncode != 0:
                        error_message = f"Step {step.step_id} failed: {result.stderr}"
                        error_log.append(error_message)
                        logger.error(error_message)
                        
                        # If step failed, try rollback
                        if step.rollback_command:
                            logger.info(f"Rolling back step {step.step_id}")
                            # Use shell=False for security - split rollback command
                            rollback_args = shlex.split(step.rollback_command) if isinstance(step.rollback_command, str) else step.rollback_command
                            rollback_result = subprocess.run(
                                rollback_args,
                                shell=False,
                                cwd=deps.build_context.project_root,
                                capture_output=True,
                                text=True
                            )
                            if rollback_result.returncode == 0:
                                logger.info(f"Step {step.step_id} rollback successful")
                            else:
                                logger.error(f"Step {step.step_id} rollback failed")
                        
                        # Strategy failed
                        attempt.status = ResolutionStatus.FAILED
                        break
                    
                    step_duration = time.time() - step_start_time
                    logger.info(f"Step {step.step_id} completed in {step_duration:.2f}s")
                    
                except subprocess.TimeoutExpired:
                    error_message = f"Step {step.step_id} timed out"
                    error_log.append(error_message)
                    logger.error(error_message)
                    attempt.status = ResolutionStatus.FAILED
                    break
                    
                except Exception as e:
                    error_message = f"Step {step.step_id} failed with exception: {e}"
                    error_log.append(error_message)
                    logger.error(error_message)
                    attempt.status = ResolutionStatus.FAILED
                    break
            
            attempt.steps_completed += 1
        
        # Update attempt status
        if attempt.status == ResolutionStatus.IN_PROGRESS:
            attempt.status = ResolutionStatus.SUCCESS
        
        attempt.duration_seconds = int(time.time() - start_time)
        attempt.output_log = '\n'.join(output_log)
        attempt.error_log = '\n'.join(error_log)
        
        # Create result
        result = ResolutionResult(
            result_id=f"result_{attempt_id}",
            problem_id="",  # Will be filled by caller
            final_status=attempt.status,
            successful_strategy=strategy.strategy_id if attempt.status == ResolutionStatus.SUCCESS else None,
            total_attempts=1,
            total_duration_seconds=attempt.duration_seconds,
            attempts_history=[attempt],
            final_validation={},
            effectiveness_score=1.0 if attempt.status == ResolutionStatus.SUCCESS else 0.0
        )
        
        logger.info(f"Resolution strategy {strategy.strategy_name} completed with status: {attempt.status}")
        
        return result
        
    except Exception as e:
        logger.error(f"Resolution strategy application failed: {e}")
        
        # Try to restore from backup
        if backup_info and deps.settings.rollback_on_failure:
            try:
                logger.info("Attempting to restore from backup")
                # Use shell=False for security - split restore command
                restore_args = shlex.split(backup_info.restore_command) if isinstance(backup_info.restore_command, str) else backup_info.restore_command
                subprocess.run(restore_args, shell=False)
                logger.info("Backup restoration completed")
                attempt.rollback_performed = True
                attempt.status = ResolutionStatus.ROLLED_BACK
            except Exception as backup_e:
                logger.error(f"Backup restoration failed: {backup_e}")
        
        raise

# ============================================================================
# Validation Tools
# ============================================================================

async def validate_resolution(
    ctx: RunContext[BuildResolverDependencies],
    original_build_command: str,
    working_directory: str = None
) -> ValidationResult:
    """Validate that a resolution actually fixed the build problems."""
    
    deps = ctx.deps
    logger = deps.logger
    
    logger.info("Starting resolution validation")
    
    try:
        work_dir = Path(working_directory) if working_directory else deps.settings.project_root
        
        # Test basic build
        validation_tests = ["basic_build"]
        passed_tests = []
        failed_tests = []
        
        # Run original build command
        build_success, build_output = await _execute_build_command(
            original_build_command, work_dir, 600  # 10 minute timeout
        )
        
        if build_success:
            passed_tests.append("basic_build")
            logger.info("Basic build validation passed")
        else:
            failed_tests.append("basic_build")
            logger.warning("Basic build validation failed")
        
        # Test specific targets if CMake
        if "cmake" in original_build_command.lower():
            test_targets = ["wire_ground_tests", "all"]
            
            for target in test_targets:
                test_name = f"target_{target}"
                validation_tests.append(test_name)
                
                target_command = f"{deps.cmake_interface.cmake_binary} --build {work_dir / deps.settings.build_directory} --target {target}"
                target_success, target_output = await _execute_build_command(
                    target_command, work_dir, 300
                )
                
                if target_success:
                    passed_tests.append(test_name)
                    logger.info(f"Target {target} validation passed")
                else:
                    failed_tests.append(test_name)
                    logger.warning(f"Target {target} validation failed")
        
        # Calculate validation confidence
        total_tests = len(validation_tests)
        passed_count = len(passed_tests)
        confidence_score = passed_count / total_tests if total_tests > 0 else 0.0
        
        is_valid = confidence_score >= 0.8  # 80% of tests must pass
        
        # Generate validation message
        if is_valid:
            message = f"Resolution validation successful. {passed_count}/{total_tests} tests passed."
        else:
            message = f"Resolution validation failed. Only {passed_count}/{total_tests} tests passed."
        
        # Generate recommendations
        recommendations = []
        if failed_tests:
            recommendations.append(f"Address failed tests: {', '.join(failed_tests)}")
        if confidence_score < 0.9:
            recommendations.append("Consider running additional validation tests")
        
        result = ValidationResult(
            is_valid=is_valid,
            validation_tests=validation_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            validation_message=message,
            confidence_score=confidence_score,
            recommendations=recommendations
        )
        
        logger.info(f"Validation completed: {message}")
        return result
        
    except Exception as e:
        logger.error(f"Resolution validation failed: {e}")
        return ValidationResult(
            is_valid=False,
            validation_message=f"Validation failed due to error: {e}",
            confidence_score=0.0
        )

# ============================================================================
# Prevention Tools
# ============================================================================

async def prevent_future_problems(
    ctx: RunContext[BuildResolverDependencies],
    analysis: BuildAnalysis,
    successful_strategy: str
) -> List[PreventionRule]:
    """Create prevention rules based on successful resolution."""
    
    deps = ctx.deps
    logger = deps.logger
    
    logger.info("Creating prevention rules from successful resolution")
    
    prevention_rules = []
    
    try:
        # Analyze the problem categories that were resolved
        problem_categories = set(error.category for error in analysis.build_problem.build_errors)
        
        for category in problem_categories:
            if category == BuildErrorCategory.DEPENDENCY:
                rule = PreventionRule(
                    rule_id=f"prevent_dependency_{int(time.time())}",
                    rule_name="Dependency Conflict Prevention",
                    description="Monitor for dependency version conflicts before they cause build failures",
                    trigger_conditions=[
                        "Package manager updates detected",
                        "CMakeLists.txt dependency changes",
                        "New external dependencies added"
                    ],
                    prevention_actions=[
                        "Run dependency compatibility check",
                        "Verify all required packages are available",
                        "Test build with new dependencies before committing"
                    ],
                    monitoring_command="./scripts/check_dependencies.sh"
                )
                prevention_rules.append(rule)
            
            elif category == BuildErrorCategory.CONFIGURATION:
                rule = PreventionRule(
                    rule_id=f"prevent_config_{int(time.time())}",
                    rule_name="Build Configuration Validation",
                    description="Validate build configuration before build attempts",
                    trigger_conditions=[
                        "CMakeLists.txt modifications",
                        "Build flag changes",
                        "Compiler version changes"
                    ],
                    prevention_actions=[
                        "Validate CMake configuration",
                        "Check compiler compatibility",
                        "Verify all required tools are available"
                    ],
                    monitoring_command="./scripts/validate_build_config.sh"
                )
                prevention_rules.append(rule)
            
            elif category == BuildErrorCategory.COMPILATION:
                rule = PreventionRule(
                    rule_id=f"prevent_compilation_{int(time.time())}",
                    rule_name="Compilation Error Prevention",
                    description="Run static analysis and incremental builds to catch compilation issues early",
                    trigger_conditions=[
                        "Source code modifications",
                        "Header file changes",
                        "Template modifications"
                    ],
                    prevention_actions=[
                        "Run clang-tidy analysis",
                        "Perform incremental build test",
                        "Check header dependency changes"
                    ],
                    monitoring_command="./scripts/ai_clang_tidy.sh analyze"
                )
                prevention_rules.append(rule)
        
        # Record prevention rules in learning database
        for rule in prevention_rules:
            try:
                deps.learning_database.db.execute("""
                    INSERT OR REPLACE INTO prevention_rules (rule_id, rule_data, effectiveness_score)
                    VALUES (?, ?, ?)
                """, (rule.rule_id, json.dumps(rule.dict()), 0.8))
                
                deps.learning_database.db.commit()
                logger.info(f"Created prevention rule: {rule.rule_name}")
                
            except Exception as e:
                logger.warning(f"Failed to record prevention rule: {e}")
        
        return prevention_rules
        
    except Exception as e:
        logger.error(f"Prevention rule creation failed: {e}")
        return []

# ============================================================================
# Build Configuration Analysis
# ============================================================================

async def analyze_build_configuration(
    ctx: RunContext[BuildResolverDependencies],
    project_directory: str = None
) -> BuildConfiguration:
    """Analyze current build system configuration."""
    
    deps = ctx.deps
    logger = deps.logger
    
    project_dir = Path(project_directory) if project_directory else deps.settings.project_root
    
    logger.info(f"Analyzing build configuration in {project_dir}")
    
    try:
        config = BuildConfiguration()
        
        # CMake analysis
        cmake_lists = project_dir / "CMakeLists.txt"
        if cmake_lists.exists():
            config.cmake_version = deps.cmake_interface.get_version()
            
            build_dir = project_dir / deps.settings.build_directory
            if build_dir.exists():
                config.cmake_cache_vars = deps.cmake_interface.get_cache_variables(build_dir)
        
        # Check for common configuration issues
        issues = []
        
        if not config.cmake_version:
            issues.append("CMake not available or not configured")
        
        if not config.cmake_cache_vars:
            issues.append("No CMake cache found - project may not be configured")
        
        # Check compiler availability
        system_diagnostics = deps.system_monitor.get_system_diagnostics()
        compiler_versions = system_diagnostics.compiler_versions
        
        available_compilers = [name for name, version in compiler_versions.items() 
                             if version != "not available"]
        
        if not available_compilers:
            issues.append("No C++ compilers available")
        
        config.configuration_issues = issues
        
        logger.info(f"Build configuration analysis completed. Found {len(issues)} issues.")
        
        return config
        
    except Exception as e:
        logger.error(f"Build configuration analysis failed: {e}")
        return BuildConfiguration(configuration_issues=[f"Analysis failed: {e}"])

# ============================================================================
# Nuclear Options (Emergency Resolution)
# ============================================================================

async def emergency_nuclear_reset(
    ctx: RunContext[BuildResolverDependencies],
    confirmation_required: bool = True
) -> ResolutionResult:
    """Nuclear option: Complete build system reset and reconstruction."""
    
    deps = ctx.deps
    logger = deps.logger
    
    if confirmation_required:
        logger.warning("Nuclear reset requires explicit confirmation")
        raise ValueError("Nuclear reset requires confirmation_required=False parameter")
    
    logger.warning("Starting NUCLEAR BUILD RESET - This will destroy and rebuild everything")
    
    start_time = time.time()
    
    try:
        # Create comprehensive backup
        backup_items = [
            deps.settings.project_root / "CMakeLists.txt",
            deps.settings.project_root / "src",
            deps.settings.project_root / "include",
            deps.settings.project_root / "tests",
            deps.settings.get_build_directory_path()
        ]
        backup_items = [item for item in backup_items if item.exists()]
        
        backup_info = deps.backup_manager.create_backup(backup_items, "nuclear_reset")
        logger.info(f"Nuclear reset backup created: {backup_info.backup_id}")
        
        # Nuclear reset steps
        nuclear_steps = [
            ("Remove all build directories", f"rm -rf {deps.settings.get_build_directory_path()}"),
            ("Clean CMake cache", f"find {deps.settings.project_root} -name 'CMakeCache.txt' -delete"),
            ("Remove CMake build files", f"find {deps.settings.project_root} -name 'CMakeFiles' -type d -exec rm -rf {{}} +"),
            ("Clear dependency cache", "rm -rf ~/.cmake/packages/*"),
            ("Reconfigure with CMake", f"{deps.cmake_interface.cmake_binary} -S {deps.settings.project_root} -B {deps.settings.get_build_directory_path()} -DCMAKE_BUILD_TYPE=Debug"),
            ("Full rebuild", f"{deps.cmake_interface.cmake_binary} --build {deps.settings.get_build_directory_path()} --target all -j{deps.settings.parallel_analysis_jobs}")
        ]
        
        output_log = []
        error_log = []
        
        for step_name, command in nuclear_steps:
            logger.info(f"Nuclear step: {step_name}")
            
            try:
                # Use shell=False for security - split command
                command_args = shlex.split(command) if isinstance(command, str) else command
                result = subprocess.run(
                    command_args,
                    shell=False,
                    cwd=deps.settings.project_root,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout per step
                )
                
                output_log.append(f"{step_name}: {result.stdout}")
                
                if result.returncode != 0:
                    error_message = f"{step_name} failed: {result.stderr}"
                    error_log.append(error_message)
                    logger.error(error_message)
                    
                    # Nuclear option failure - restore backup
                    logger.critical("Nuclear reset failed - attempting backup restoration")
                    # Use shell=False for security - split restore command
                    restore_args = shlex.split(backup_info.restore_command) if isinstance(backup_info.restore_command, str) else backup_info.restore_command
                    subprocess.run(restore_args, shell=False)
                    
                    return ResolutionResult(
                        result_id=f"nuclear_reset_{int(time.time())}",
                        problem_id="nuclear_reset",
                        final_status=ResolutionStatus.FAILED,
                        total_attempts=1,
                        total_duration_seconds=int(time.time() - start_time),
                        attempts_history=[],
                        effectiveness_score=0.0
                    )
                
                logger.info(f"Nuclear step completed: {step_name}")
                
            except Exception as e:
                error_message = f"{step_name} failed with exception: {e}"
                error_log.append(error_message)
                logger.error(error_message)
                raise
        
        # Nuclear reset successful
        duration = int(time.time() - start_time)
        
        logger.info(f"Nuclear reset completed successfully in {duration}s")
        
        return ResolutionResult(
            result_id=f"nuclear_reset_{int(time.time())}",
            problem_id="nuclear_reset",
            final_status=ResolutionStatus.SUCCESS,
            successful_strategy="emergency_nuclear_reset",
            total_attempts=1,
            total_duration_seconds=duration,
            attempts_history=[],
            effectiveness_score=1.0
        )
        
    except Exception as e:
        logger.critical(f"Nuclear reset failed catastrophically: {e}")
        raise