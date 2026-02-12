"""Pydantic models for structured data in the Never Fail Build Resolver Agent."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pathlib import Path

# ============================================================================
# Enums and Type Definitions
# ============================================================================

class BuildErrorSeverity(str, Enum):
    """Build error severity levels."""
    CRITICAL = "critical"      # Prevents any build progress
    HIGH = "high"             # Major functionality broken
    MEDIUM = "medium"         # Some functionality affected
    LOW = "low"               # Minor issues, build still works
    WARNING = "warning"       # Just warnings, no functional impact

class BuildErrorCategory(str, Enum):
    """Categories of build errors."""
    COMPILATION = "compilation"           # C++ compilation errors
    LINKING = "linking"                  # Linker errors
    DEPENDENCY = "dependency"            # Missing or incompatible dependencies
    CONFIGURATION = "configuration"     # CMake/build system configuration
    TOOLCHAIN = "toolchain"             # Compiler/tool issues
    ENVIRONMENT = "environment"         # Environment variable/path issues
    PERMISSION = "permission"           # File/directory permission issues
    DISK_SPACE = "disk_space"          # Disk space issues
    NETWORK = "network"                 # Network/download issues
    UNKNOWN = "unknown"                 # Unclassified errors

class ResolutionTier(str, Enum):
    """4-tier resolution system levels."""
    PREVENTION = "prevention"           # Tier 1: Proactive prevention
    INTELLIGENT = "intelligent"         # Tier 2: Smart resolution
    COMPREHENSIVE = "comprehensive"     # Tier 3: Comprehensive analysis
    NUCLEAR = "nuclear"                 # Tier 4: Nuclear options

class ResolutionStatus(str, Enum):
    """Status of resolution attempts."""
    PENDING = "pending"                 # Not yet attempted
    IN_PROGRESS = "in_progress"         # Currently being applied
    SUCCESS = "success"                 # Successfully resolved
    PARTIAL = "partial"                 # Partially resolved
    FAILED = "failed"                   # Resolution failed
    ROLLED_BACK = "rolled_back"         # Had to rollback changes

class BuildSystem(str, Enum):
    """Supported build systems."""
    CMAKE = "cmake"
    MAKE = "make"
    NINJA = "ninja"
    AUTOTOOLS = "autotools"
    CUSTOM = "custom"

# ============================================================================
# Core Problem Models
# ============================================================================

class BuildError(BaseModel):
    """Represents a single build error."""
    line_number: Optional[int] = Field(None, description="Line number where error occurs")
    column_number: Optional[int] = Field(None, description="Column number where error occurs")
    file_path: Optional[Path] = Field(None, description="File where error occurs")
    error_code: Optional[str] = Field(None, description="Error code from compiler/tool")
    message: str = Field(..., description="Error message")
    raw_output: str = Field(..., description="Raw error output from build tool")
    severity: BuildErrorSeverity = Field(..., description="Error severity level")
    category: BuildErrorCategory = Field(..., description="Error category")
    tool_name: str = Field(..., description="Tool that generated the error")
    context_lines: List[str] = Field(default_factory=list, description="Surrounding context")

class BuildProblem(BaseModel):
    """Comprehensive analysis of a build problem."""
    problem_id: str = Field(..., description="Unique identifier for this problem")
    timestamp: datetime = Field(default_factory=datetime.now, description="When problem was detected")
    build_errors: List[BuildError] = Field(default_factory=list, description="Individual build errors")
    root_cause: Optional[str] = Field(None, description="Identified root cause")
    affected_targets: List[str] = Field(default_factory=list, description="Build targets affected")
    build_system: BuildSystem = Field(..., description="Build system used")
    build_command: str = Field(..., description="Build command that failed")
    working_directory: Path = Field(..., description="Directory where build was attempted")
    environment_snapshot: Dict[str, str] = Field(default_factory=dict, description="Environment variables at failure")
    system_info: Dict[str, Any] = Field(default_factory=dict, description="System information")
    similar_problems_count: int = Field(default=0, description="Number of similar problems seen before")

class SystemDiagnostics(BaseModel):
    """System-level diagnostic information."""
    os_info: Dict[str, str] = Field(default_factory=dict, description="Operating system information")
    disk_space: Dict[str, Any] = Field(default_factory=dict, description="Disk space information")
    memory_info: Dict[str, Any] = Field(default_factory=dict, description="Memory information")
    compiler_versions: Dict[str, str] = Field(default_factory=dict, description="Compiler version information")
    tool_versions: Dict[str, str] = Field(default_factory=dict, description="Build tool versions")
    dependency_status: Dict[str, Any] = Field(default_factory=dict, description="Dependency status")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Relevant environment variables")
    recent_system_changes: List[str] = Field(default_factory=list, description="Recent system changes that might affect builds")

class BuildConfiguration(BaseModel):
    """Build system configuration analysis."""
    cmake_version: Optional[str] = Field(None, description="CMake version")
    cmake_cache_vars: Dict[str, str] = Field(default_factory=dict, description="CMake cache variables")
    compiler_flags: Dict[str, List[str]] = Field(default_factory=dict, description="Compiler flags by language")
    linker_flags: List[str] = Field(default_factory=list, description="Linker flags")
    target_definitions: List[Dict[str, Any]] = Field(default_factory=list, description="Build target definitions")
    dependencies: List[Dict[str, Any]] = Field(default_factory=list, description="Project dependencies")
    include_paths: List[Path] = Field(default_factory=list, description="Include search paths")
    library_paths: List[Path] = Field(default_factory=list, description="Library search paths")
    configuration_issues: List[str] = Field(default_factory=list, description="Configuration issues detected")

# ============================================================================
# Resolution Strategy Models
# ============================================================================

class ResolutionStep(BaseModel):
    """Individual step in a resolution strategy."""
    step_id: int = Field(..., description="Step number in sequence")
    description: str = Field(..., description="Human-readable description of step")
    command: Optional[str] = Field(None, description="Command to execute (if applicable)")
    expected_outcome: str = Field(..., description="Expected outcome of this step")
    validation_method: str = Field(..., description="How to validate this step succeeded")
    rollback_command: Optional[str] = Field(None, description="Command to rollback this step if needed")
    estimated_duration_seconds: int = Field(..., description="Estimated time to complete step")
    risk_level: str = Field(..., description="Risk level (low/medium/high)")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites for this step")

class ResolutionStrategy(BaseModel):
    """Comprehensive resolution strategy for a build problem."""
    strategy_id: str = Field(..., description="Unique identifier for this strategy")
    strategy_name: str = Field(..., description="Human-readable strategy name")
    tier: ResolutionTier = Field(..., description="Resolution tier (prevention/intelligent/comprehensive/nuclear)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in strategy success (0-1)")
    estimated_success_rate: float = Field(..., ge=0.0, le=1.0, description="Historical success rate for this strategy")
    description: str = Field(..., description="Detailed description of the strategy")
    target_problems: List[BuildErrorCategory] = Field(default_factory=list, description="Problem types this strategy addresses")
    resolution_steps: List[ResolutionStep] = Field(default_factory=list, description="Step-by-step resolution plan")
    estimated_total_time_seconds: int = Field(..., description="Total estimated time for resolution")
    risk_assessment: str = Field(..., description="Overall risk assessment")
    backup_required: bool = Field(default=True, description="Whether backup is required before applying")
    alternative_strategies: List[str] = Field(default_factory=list, description="Alternative strategy IDs if this fails")
    success_criteria: List[str] = Field(default_factory=list, description="Criteria to determine success")
    side_effects: List[str] = Field(default_factory=list, description="Potential side effects")

class PreventionRule(BaseModel):
    """Rule for preventing future build failures."""
    rule_id: str = Field(..., description="Unique rule identifier")
    rule_name: str = Field(..., description="Human-readable rule name")
    description: str = Field(..., description="Description of what this rule prevents")
    trigger_conditions: List[str] = Field(default_factory=list, description="Conditions that trigger this rule")
    prevention_actions: List[str] = Field(default_factory=list, description="Actions to take to prevent the problem")
    monitoring_command: Optional[str] = Field(None, description="Command to monitor for this issue")
    alert_threshold: Optional[str] = Field(None, description="Threshold for alerting about this issue")
    enabled: bool = Field(default=True, description="Whether this prevention rule is active")

# ============================================================================
# Analysis and Results Models
# ============================================================================

class BuildAnalysis(BaseModel):
    """Comprehensive analysis of a build problem."""
    analysis_id: str = Field(..., description="Unique identifier for this analysis")
    timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    build_problem: BuildProblem = Field(..., description="The build problem being analyzed")
    system_diagnostics: SystemDiagnostics = Field(..., description="System diagnostic information")
    build_configuration: BuildConfiguration = Field(..., description="Build configuration analysis")
    root_cause_analysis: str = Field(..., description="Detailed root cause analysis")
    contributing_factors: List[str] = Field(default_factory=list, description="Factors contributing to the problem")
    severity_assessment: BuildErrorSeverity = Field(..., description="Overall severity assessment")
    impact_analysis: str = Field(..., description="Analysis of the impact of this problem")
    recommended_tier: ResolutionTier = Field(..., description="Recommended resolution tier")
    recommended_strategies: List[str] = Field(default_factory=list, description="Recommended strategy IDs")
    prevention_opportunities: List[str] = Field(default_factory=list, description="Opportunities to prevent future occurrences")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in analysis accuracy")

class ResolutionAttempt(BaseModel):
    """Record of a resolution attempt."""
    attempt_id: str = Field(..., description="Unique identifier for this attempt")
    timestamp: datetime = Field(default_factory=datetime.now, description="When attempt was made")
    strategy_used: str = Field(..., description="Strategy ID that was attempted")
    status: ResolutionStatus = Field(..., description="Status of the resolution attempt")
    steps_completed: int = Field(..., description="Number of resolution steps completed")
    total_steps: int = Field(..., description="Total number of steps in the strategy")
    duration_seconds: int = Field(..., description="Time taken for this attempt")
    output_log: str = Field(..., description="Output log from the resolution attempt")
    error_log: str = Field(default="", description="Error log if attempt failed")
    rollback_performed: bool = Field(default=False, description="Whether rollback was performed")
    lessons_learned: List[str] = Field(default_factory=list, description="Lessons learned from this attempt")

class ResolutionResult(BaseModel):
    """Final result of build problem resolution."""
    result_id: str = Field(..., description="Unique identifier for this result")
    problem_id: str = Field(..., description="ID of the problem that was resolved")
    final_status: ResolutionStatus = Field(..., description="Final resolution status")
    successful_strategy: Optional[str] = Field(None, description="Strategy that ultimately succeeded")
    total_attempts: int = Field(..., description="Total number of resolution attempts")
    total_duration_seconds: int = Field(..., description="Total time spent on resolution")
    attempts_history: List[ResolutionAttempt] = Field(default_factory=list, description="History of all attempts")
    final_validation: Dict[str, Any] = Field(default_factory=dict, description="Final validation results")
    post_resolution_tests: List[str] = Field(default_factory=list, description="Tests that passed after resolution")
    effectiveness_score: float = Field(..., ge=0.0, le=1.0, description="Effectiveness score for this resolution")
    prevention_rules_created: List[str] = Field(default_factory=list, description="Prevention rules created from this resolution")
    documentation_updates: List[str] = Field(default_factory=list, description="Documentation updates made")

# ============================================================================
# Context and Session Models
# ============================================================================

class BuildContext(BaseModel):
    """Context information for build resolution sessions."""
    session_id: str = Field(..., description="Unique session identifier")
    project_root: Path = Field(..., description="Project root directory")
    current_working_directory: Path = Field(..., description="Current working directory")
    build_system: BuildSystem = Field(..., description="Primary build system")
    active_build_configuration: str = Field(default="Debug", description="Active build configuration")
    user_preferences: Dict[str, Any] = Field(default_factory=dict, description="User preferences for resolution")
    previous_problems: List[str] = Field(default_factory=list, description="Previous problem IDs in this session")
    session_start_time: datetime = Field(default_factory=datetime.now, description="When session started")
    environment_backup: Dict[str, str] = Field(default_factory=dict, description="Backup of original environment")
    files_modified: List[Path] = Field(default_factory=list, description="Files modified in this session")

class ConversationContext(BaseModel):
    """Context for conversational interactions with the build resolver."""
    session_id: str = Field(..., description="Session identifier")
    current_problem: Optional[str] = Field(None, description="Currently discussed problem ID")
    active_resolution: Optional[str] = Field(None, description="Currently active resolution strategy")
    conversation_history: List[Dict[str, str]] = Field(default_factory=list, description="Recent conversation")
    user_expertise_level: str = Field(default="intermediate", description="User's technical expertise level")
    preferred_resolution_style: str = Field(default="detailed", description="User's preferred resolution approach")
    urgent_mode: bool = Field(default=False, description="Whether we're in urgent resolution mode")

# ============================================================================
# Monitoring and Learning Models
# ============================================================================

class BuildMonitoringEvent(BaseModel):
    """Event from continuous build monitoring."""
    event_id: str = Field(..., description="Unique event identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When event occurred")
    event_type: str = Field(..., description="Type of monitoring event")
    severity: BuildErrorSeverity = Field(..., description="Event severity")
    message: str = Field(..., description="Event message")
    build_context: Dict[str, Any] = Field(default_factory=dict, description="Build context when event occurred")
    action_taken: Optional[str] = Field(None, description="Automatic action taken (if any)")
    requires_attention: bool = Field(default=False, description="Whether human attention is required")

class LearningUpdate(BaseModel):
    """Update to the learning system from successful resolutions."""
    update_id: str = Field(..., description="Unique update identifier")
    problem_pattern: str = Field(..., description="Pattern of the problem that was solved")
    successful_strategy: str = Field(..., description="Strategy that succeeded")
    confidence_improvement: float = Field(..., description="How much this improves confidence in the strategy")
    generalization_score: float = Field(..., ge=0.0, le=1.0, description="How well this generalizes to other problems")
    context_factors: List[str] = Field(default_factory=list, description="Context factors that influenced success")
    timestamp: datetime = Field(default_factory=datetime.now, description="When learning update was recorded")

# ============================================================================
# Utility Models
# ============================================================================

class ValidationResult(BaseModel):
    """Result of validating a resolution."""
    is_valid: bool = Field(..., description="Whether validation passed")
    validation_tests: List[str] = Field(default_factory=list, description="Tests that were run")
    passed_tests: List[str] = Field(default_factory=list, description="Tests that passed")
    failed_tests: List[str] = Field(default_factory=list, description="Tests that failed")
    validation_message: str = Field(..., description="Summary of validation results")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in validation results")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations based on validation")

class BackupInfo(BaseModel):
    """Information about a backup created before resolution."""
    backup_id: str = Field(..., description="Unique backup identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="When backup was created")
    backup_path: Path = Field(..., description="Path to backup location")
    backed_up_items: List[str] = Field(default_factory=list, description="Items that were backed up")
    size_bytes: int = Field(..., description="Size of backup in bytes")
    restore_command: str = Field(..., description="Command to restore from this backup")
    expiry_date: Optional[datetime] = Field(None, description="When this backup expires")

class PerformanceMetrics(BaseModel):
    """Performance metrics for build resolution operations."""
    operation_name: str = Field(..., description="Name of the operation measured")
    duration_seconds: float = Field(..., description="Duration in seconds")
    memory_usage_mb: float = Field(..., description="Peak memory usage in MB")
    cpu_usage_percent: float = Field(..., description="Average CPU usage percentage")
    success_rate: float = Field(..., ge=0.0, le=1.0, description="Success rate for this operation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When metrics were recorded")
    additional_metrics: Dict[str, float] = Field(default_factory=dict, description="Additional custom metrics")