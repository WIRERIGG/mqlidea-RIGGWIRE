# Tools for NEVER FAIL BUILD RESOLVER

## Tool Implementation Specifications

Based on the requirements from INITIAL.md, this agent needs 5 essential tools for comprehensive C++ build problem resolution with state machine orchestration.

### Tool 1: problem_analyzer

**Purpose**: Categorize and analyze build problems from error logs with intelligent pattern recognition  
**Pattern**: `@agent.tool` (context-aware, needs project context and error classification)  
**Parameters**:
- `error_log` (str): Complete error log output from failed build attempt
- `project_path` (Path): Path to project root for context analysis

**Implementation Pattern**:
```python
@agent.tool
async def problem_analyzer(
    ctx: RunContext[BuildResolverDependencies],
    error_log: str,
    project_path: Path
) -> Dict[str, Any]:
    """
    Analyze and categorize build problems from error logs.
    
    Args:
        error_log: Complete build error output for analysis
        project_path: Project root path for context
    
    Returns:
        Categorized problems with severity, type, and suggested solutions
    """
```

**Functionality**:
- Parse error logs for compiler, linker, CMake, and system errors
- Classify problems by category: COMPILER, LINKER, CMAKE, GTEST, SYSTEM
- Assess severity levels: CRITICAL, HIGH, MEDIUM, LOW
- Extract affected files, line numbers, and error messages
- Generate initial solution suggestions based on error patterns
- Cross-reference with learned resolution patterns

**Error Handling**:
- Fallback to generic problem classification on parse failure
- Handle malformed or incomplete error logs
- Validate project path existence and accessibility

### Tool 2: cmake_resolver

**Purpose**: Execute CMake commands with intelligent error resolution and retry strategies  
**Pattern**: `@agent.tool` (context-aware, needs file system and command execution)  
**Parameters**:
- `build_command` (str): CMake command to execute (configure, build, clean)
- `working_dir` (Path): Working directory for command execution
- `timeout` (int, default=300): Maximum execution time in seconds

**Implementation Pattern**:
```python
@agent.tool
async def cmake_resolver(
    ctx: RunContext[BuildResolverDependencies],
    build_command: str,
    working_dir: Path,
    timeout: int = 300
) -> Dict[str, Any]:
    """
    Execute CMake commands with intelligent error resolution.
    
    Args:
        build_command: CMake command to execute
        working_dir: Directory to execute command in
        timeout: Maximum execution time in seconds
    
    Returns:
        Command result with success status, output, and resolution actions
    """
```

**Functionality**:
- Execute CMake configure, build, and clean operations
- Parse CMake output for specific error patterns
- Apply automatic fixes: cache clearing, dependency resolution, path corrections
- Progressive fallback strategies: clean cache → reset config → minimal build
- Comprehensive logging of all command executions and modifications

**Error Handling**:
- Timeout protection with graceful process termination
- Automatic retry with cache clearing on configuration failures
- Fallback to minimal CMake configuration on complex errors
- Safe command validation to prevent destructive operations

### Tool 3: clang_tidy_fixer

**Purpose**: Apply clang-tidy fixes with safety validation and comprehensive backup  
**Pattern**: `@agent.tool` (context-aware, needs file modification capabilities)  
**Parameters**:
- `file_path` (Path): Source file to analyze and fix
- `fix_categories` (List[str]): Categories of fixes to apply (performance, readability, etc.)

**Implementation Pattern**:
```python
@agent.tool
async def clang_tidy_fixer(
    ctx: RunContext[BuildResolverDependencies],
    file_path: Path,
    fix_categories: List[str]
) -> Dict[str, Any]:
    """
    Apply clang-tidy fixes with safety validation.
    
    Args:
        file_path: Source file to analyze and fix
        fix_categories: Categories of clang-tidy fixes to apply
    
    Returns:
        Fix results with applied changes and validation status
    """
```

**Functionality**:
- Execute clang-tidy analysis with comprehensive rule sets
- Apply fixes automatically for specified categories
- Create automatic backup before any file modifications
- Validate fixes by test compilation before committing changes
- Roll back changes if validation fails

**Error Handling**:
- Automatic backup and rollback on compilation failure
- Safe application of fixes with incremental validation
- Skip problematic fixes and continue with remaining categories
- Comprehensive logging of all changes made

### Tool 4: gtest_integrator

**Purpose**: Resolve GoogleTest integration conflicts and framework consistency issues  
**Pattern**: `@agent.tool` (context-aware, needs project-wide analysis)  
**Parameters**:
- `test_files` (List[Path]): List of test files to analyze for conflicts
- `target_framework` (str): Target testing framework ("gtest" or "catch2")

**Implementation Pattern**:
```python
@agent.tool
async def gtest_integrator(
    ctx: RunContext[BuildResolverDependencies],
    test_files: List[Path],
    target_framework: str
) -> Dict[str, Any]:
    """
    Resolve GoogleTest integration conflicts.
    
    Args:
        test_files: List of test files to analyze
        target_framework: Target testing framework for consistency
    
    Returns:
        Integration results with resolved conflicts and framework status
    """
```

**Functionality**:
- Detect mixed testing frameworks across project
- Convert test files to consistent GoogleTest format
- Resolve main() function conflicts and illegal instruction errors
- Update CMakeLists.txt for proper GoogleTest integration
- Validate test discovery and execution functionality

**Error Handling**:
- Safe framework migration with backup and rollback
- Handle complex test macro conversions gracefully
- Validate test compilation at each conversion step
- Preserve test functionality during framework migration

### Tool 5: system_validator

**Purpose**: Validate and repair system build environment dependencies  
**Pattern**: `@agent.tool` (context-aware, needs system environment access)  
**Parameters**:
- `validation_type` (str): Type of validation ("compiler", "dependencies", "permissions", "network")
- `repair_mode` (bool, default=False): Whether to attempt automatic repairs

**Implementation Pattern**:
```python
@agent.tool
async def system_validator(
    ctx: RunContext[BuildResolverDependencies],
    validation_type: str,
    repair_mode: bool = False
) -> Dict[str, Any]:
    """
    Validate and repair system build environment.
    
    Args:
        validation_type: Type of system validation to perform
        repair_mode: Whether to attempt automatic environment repairs
    
    Returns:
        Validation results with environment status and repair actions
    """
```

**Functionality**:
- Validate compiler availability and version compatibility
- Check library dependencies and linking paths
- Verify file permissions and directory accessibility
- Test network connectivity for dependency fetching
- Apply automatic environment repairs when safe and possible

**Error Handling**:
- Non-destructive validation with optional repair mode
- Safe environment modifications with rollback capability
- Comprehensive reporting of environment issues found
- Fallback configurations for system compatibility

## State Management Utilities

### State Transition Controller
```python
async def transition_state(
    ctx: RunContext[BuildResolverDependencies], 
    new_state: str,
    checkpoint_data: Dict[str, Any] = None
) -> bool:
    """Manage state machine transitions with checkpoint creation."""
```

### Backup and Rollback System
```python
async def create_backup_checkpoint(
    ctx: RunContext[BuildResolverDependencies],
    files_to_backup: List[Path]
) -> str:
    """Create comprehensive backup checkpoint before modifications."""

async def rollback_to_checkpoint(
    ctx: RunContext[BuildResolverDependencies],
    checkpoint_id: str
) -> bool:
    """Rollback all changes to previous checkpoint state."""
```

### Resolution Pattern Learning
```python
async def record_resolution_pattern(
    ctx: RunContext[BuildResolverDependencies],
    problem_signature: str,
    solution_applied: Dict[str, Any],
    success_metrics: Dict[str, Any]
) -> None:
    """Record successful resolution patterns for future learning."""
```

## Parameter Validation

All tools include comprehensive validation for:
- File path existence and accessibility
- Command parameter safety (no destructive operations without backup)
- Timeout values within reasonable bounds (5-3600 seconds)
- Error log size limits to prevent memory issues
- Project path validation and write permission verification

## Performance and Safety Considerations

- **Backup System**: Automatic backup before ANY file modifications
- **Timeout Protection**: All command executions have configurable timeouts
- **Resource Limits**: Memory and CPU usage monitoring during analysis
- **Rollback Capability**: Complete restoration of previous state on failure
- **State Persistence**: Checkpoint system for complex multi-step resolutions

## Dependencies Required

```python
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from pydantic_ai import RunContext
import subprocess
import asyncio
import shutil
import json
import logging
import tempfile
from dataclasses import dataclass
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
```

## Integration with Wire_ground Project

- Tools specifically designed for wire_ground CMake structure
- Integration with existing `scripts/` directory workflows
- Compatibility with current build targets: `wire_ground_tests`, `safe_test`
- Support for existing clang-tidy configurations and warning suppressions
- Respect for current GoogleTest setup and test discovery patterns

## Resolution Mode Optimization

### Fast Mode Tool Behavior
- Use cached resolution patterns for immediate application
- Skip comprehensive analysis in favor of proven quick fixes
- Limit tool execution time with aggressive timeouts
- Focus on highest-probability solutions first

### Emergency Mode Tool Behavior
- Nuclear reset capabilities with minimal viable build targets
- Disable non-essential features and optimizations
- Create minimal test executables to verify basic compilation
- Apply emergency fallback configurations for system compatibility

### Thorough Mode Tool Behavior
- Comprehensive analysis with detailed logging
- Multi-phase validation of all resolution steps
- Cross-reference multiple solution strategies
- Generate detailed reports for long-term problem prevention

## Testing Strategy

- **Unit Tests**: Individual tool parameter validation and core logic
- **Integration Tests**: End-to-end build problem resolution scenarios
- **State Machine Tests**: Validation of state transitions and rollback
- **Performance Tests**: Resolution time benchmarking across modes
- **Safety Tests**: Backup and rollback functionality validation

This tool specification provides the complete set of functions needed for the NEVER FAIL BUILD RESOLVER agent, following Pydantic AI best practices with comprehensive error handling, safety protocols, and integration with the existing wire_ground build infrastructure.