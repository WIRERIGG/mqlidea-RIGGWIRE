"""Models for Never-Fail Build Resolver Agent."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

class ResolutionTier(str, Enum):
    """Resolution tier levels."""
    PREVENTION = "prevention"
    INTELLIGENT = "intelligent"
    COMPREHENSIVE = "comprehensive"
    NUCLEAR = "nuclear"

class BuildProblemCategory(str, Enum):
    """Categories of build problems."""
    COMPILER_ERROR = "compiler_error"
    LINKER_ERROR = "linker_error"
    CMAKE_ERROR = "cmake_error"
    DEPENDENCY_MISSING = "dependency_missing"
    CONFIGURATION_ERROR = "configuration_error"
    TEST_FAILURE = "test_failure"
    WARNING_AS_ERROR = "warning_as_error"
    UNKNOWN = "unknown"

class BuildProblem(BaseModel):
    """Represents a build problem."""
    category: BuildProblemCategory = Field(description="Problem category")
    severity: Literal["critical", "error", "warning", "info"] = Field(description="Problem severity")
    description: str = Field(description="Problem description")
    file_path: Optional[str] = Field(None, description="Related file path")
    line_number: Optional[int] = Field(None, description="Line number where problem occurs")
    raw_error: str = Field(description="Raw error message from build system")
    suggested_fixes: List[str] = Field(default_factory=list, description="Suggested fix approaches")

class ResolutionAttempt(BaseModel):
    """Represents a resolution attempt."""
    tier: ResolutionTier = Field(description="Resolution tier used")
    problem: BuildProblem = Field(description="Problem being resolved")
    actions_taken: List[str] = Field(description="Actions taken to resolve")
    success: bool = Field(description="Whether resolution succeeded")
    rollback_required: bool = Field(default=False, description="Whether rollback was needed")
    duration_seconds: float = Field(description="Time taken for resolution")
    notes: Optional[str] = Field(None, description="Additional notes")

class BuildState(BaseModel):
    """Represents the current build state."""
    status: Literal["healthy", "degraded", "broken", "unknown"] = Field(description="Overall build status")
    active_problems: List[BuildProblem] = Field(default_factory=list, description="Current problems")
    resolution_history: List[ResolutionAttempt] = Field(default_factory=list, description="Past resolution attempts")
    warnings_count: int = Field(0, description="Number of warnings")
    errors_count: int = Field(0, description="Number of errors")
    last_successful_build: Optional[str] = Field(None, description="Timestamp of last successful build")
    current_tier: Optional[ResolutionTier] = Field(None, description="Current resolution tier in use")

class SystemRequirement(BaseModel):
    """System requirement check."""
    name: str = Field(description="Requirement name")
    required_version: Optional[str] = Field(None, description="Required version")
    current_version: Optional[str] = Field(None, description="Current version")
    is_satisfied: bool = Field(description="Whether requirement is satisfied")
    install_command: Optional[str] = Field(None, description="Command to install/fix")

class BuildConfiguration(BaseModel):
    """Build configuration settings."""
    build_type: Literal["Debug", "Release", "RelWithDebInfo", "MinSizeRel"] = Field("Debug", description="CMake build type")
    compiler: str = Field("clang++", description="Compiler to use")
    cpp_standard: str = Field("c++20", description="C++ standard")
    enable_sanitizers: bool = Field(True, description="Enable sanitizers")
    enable_warnings: bool = Field(True, description="Enable warnings")
    treat_warnings_as_errors: bool = Field(True, description="Treat warnings as errors")
    parallel_jobs: int = Field(4, description="Number of parallel build jobs")
    
class ResolutionStrategy(BaseModel):
    """Resolution strategy for a specific problem."""
    problem_pattern: str = Field(description="Regex pattern to match problem")
    category: BuildProblemCategory = Field(description="Problem category")
    tier: ResolutionTier = Field(description="Recommended resolution tier")
    fix_commands: List[str] = Field(description="Commands to fix the problem")
    verification_command: str = Field(description="Command to verify fix")
    rollback_commands: List[str] = Field(default_factory=list, description="Commands to rollback if fix fails")
    success_rate: float = Field(0.0, description="Historical success rate")

class LearningEntry(BaseModel):
    """Entry in the learning database."""
    problem_signature: str = Field(description="Unique problem signature")
    successful_resolutions: List[ResolutionAttempt] = Field(default_factory=list)
    failed_resolutions: List[ResolutionAttempt] = Field(default_factory=list)
    preferred_strategy: Optional[ResolutionStrategy] = Field(None, description="Most successful strategy")
    last_seen: str = Field(description="Last time this problem was seen")
    frequency: int = Field(1, description="How often this problem occurs")

class BuildAnalysisResult(BaseModel):
    """Result of build analysis."""
    problems_found: List[BuildProblem] = Field(default_factory=list)
    system_requirements: List[SystemRequirement] = Field(default_factory=list)
    suggested_tier: ResolutionTier = Field(description="Suggested resolution tier")
    confidence_score: float = Field(description="Confidence in analysis (0-1)")
    analysis_notes: str = Field(description="Human-readable analysis notes")

class ResolutionPlan(BaseModel):
    """Plan for resolving build issues."""
    tier: ResolutionTier = Field(description="Resolution tier to use")
    problems_to_resolve: List[BuildProblem] = Field(description="Problems to resolve")
    strategies: List[ResolutionStrategy] = Field(description="Strategies to apply")
    estimated_duration_seconds: float = Field(description="Estimated time to complete")
    rollback_plan: List[str] = Field(default_factory=list, description="Rollback steps if needed")
    requires_user_approval: bool = Field(False, description="Whether user approval is needed")

class ValidationResult(BaseModel):
    """Result of build validation."""
    is_valid: bool = Field(description="Whether build is valid")
    compilation_success: bool = Field(description="Whether compilation succeeded")
    tests_passed: bool = Field(description="Whether tests passed")
    warnings_count: int = Field(0, description="Number of warnings")
    errors_count: int = Field(0, description="Number of errors")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    validation_notes: str = Field(description="Validation notes")