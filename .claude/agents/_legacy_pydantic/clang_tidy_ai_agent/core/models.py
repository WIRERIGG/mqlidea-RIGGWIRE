"""Pydantic models for structured data in the Clang-Tidy AI Agent."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class Warning(BaseModel):
    """Represents a clang-tidy warning."""
    line_number: int = Field(..., description="Line number where warning occurs")
    column_number: int = Field(..., description="Column number where warning occurs") 
    rule_id: str = Field(..., description="Clang-tidy rule identifier")
    severity: str = Field(..., description="Warning severity level (CRITICAL, HIGH, MEDIUM, LOW)")
    category: str = Field(..., description="Warning category (critical, safety, quality)")
    message: str = Field(..., description="Warning message")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix from clang-tidy")
    context_lines: List[str] = Field(default_factory=list, description="Surrounding code context")
    fix_complexity: int = Field(default=1, ge=1, le=10, description="Fix complexity score 1-10")
    batch_group: Optional[str] = Field(None, description="Batch processing group identifier")

class ClangTidyAnalysis(BaseModel):
    """Results from clang-tidy analysis of a file."""
    file_path: str = Field(..., description="Path to analyzed file")
    warnings: List[Warning] = Field(default_factory=list, description="List of warnings found")
    total_warnings: int = Field(..., description="Total number of warnings")
    analysis_timestamp: datetime = Field(default_factory=datetime.now, description="When analysis was performed")
    clang_tidy_version: str = Field(default="unknown", description="Version of clang-tidy used")

class FixStrategy(BaseModel):
    """Represents a strategy for fixing code issues."""
    name: str = Field(..., description="Name of the fix strategy")
    description: str = Field(..., description="Detailed description of the strategy")
    implementation_steps: List[str] = Field(default_factory=list, description="Step-by-step implementation")
    pros: List[str] = Field(default_factory=list, description="Advantages of this approach")
    cons: List[str] = Field(default_factory=list, description="Disadvantages of this approach")
    recommended: bool = Field(default=False, description="Whether this is the recommended approach")

class CodeExamples(BaseModel):
    """Before/after code examples."""
    problematic_code: str = Field(..., description="Code that triggers the warning")
    fixed_code: str = Field(..., description="Code after applying the fix")
    explanation: str = Field(..., description="Explanation of what changed and why")

class WarningExplanation(BaseModel):
    """Detailed explanation of a clang-tidy warning."""
    rule_id: str = Field(..., description="Clang-tidy rule identifier")
    rule_category: str = Field(..., description="Category of the rule (readability, performance, etc.)")
    problem_description: str = Field(..., description="What the problem is")
    why_it_matters: str = Field(..., description="Why this issue is important to fix")
    fix_strategies: List[FixStrategy] = Field(default_factory=list, description="Possible fix strategies")
    code_examples: CodeExamples = Field(..., description="Before/after code examples")
    related_concepts: List[str] = Field(default_factory=list, description="Related C++ concepts")
    severity_justification: str = Field(..., description="Why this has the given severity level")

class AlternativeApproach(BaseModel):
    """Alternative approach to fixing an issue."""
    strategy_name: str = Field(..., description="Name of the alternative strategy")
    description: str = Field(..., description="Description of this approach")
    when_to_use: str = Field(..., description="When this approach is most appropriate")
    complexity_rating: str = Field(..., description="Complexity rating (simple, moderate, complex)")

class FixRecommendation(BaseModel):
    """AI-powered recommendation for fixing code issues."""
    recommended_strategy: str = Field(..., description="The recommended fix strategy")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendation (0-1)")
    rationale: str = Field(..., description="Why this strategy is recommended")
    implementation_plan: List[str] = Field(default_factory=list, description="Step-by-step implementation plan")
    alternative_approaches: List[AlternativeApproach] = Field(default_factory=list, description="Alternative approaches")
    estimated_complexity: str = Field(..., description="Estimated complexity of the fix")
    potential_side_effects: List[str] = Field(default_factory=list, description="Potential side effects to consider")

class PreferenceUpdate(BaseModel):
    """Result of updating user preferences."""
    success: bool = Field(..., description="Whether the update was successful")
    message: str = Field(..., description="Status message")
    preferences_count: int = Field(..., description="Total number of stored preferences")

class ProjectAnalysis(BaseModel):
    """Results from analyzing multiple files in a project."""
    total_files_analyzed: int = Field(..., description="Total number of files analyzed")
    total_warnings: int = Field(..., description="Total warnings across all files")
    warnings_by_category: dict[str, int] = Field(default_factory=dict, description="Warnings grouped by category")
    top_issues: List[Warning] = Field(default_factory=list, description="Most important issues to address")
    analysis_summary: str = Field(..., description="High-level summary of the analysis")
    recommendations: List[str] = Field(default_factory=list, description="Top-level recommendations")
    estimated_fix_time: str = Field(..., description="Estimated time to fix all issues")

class ConversationContext(BaseModel):
    """Context for conversational interactions."""
    session_id: str = Field(..., description="Unique session identifier")
    current_file: Optional[str] = Field(None, description="Currently discussed file")
    active_warnings: List[Warning] = Field(default_factory=list, description="Warnings being discussed")
    conversation_history: List[str] = Field(default_factory=list, description="Recent conversation points")
    user_expertise_level: str = Field(default="intermediate", description="User's expertise level")
    preferred_explanation_style: str = Field(default="detailed", description="User's preferred explanation style")


# Enhanced models for Factory Orchestrator workflow

class FixStrategy(BaseModel):
    """Represents a comprehensive fix strategy from clang-tidy-strategist."""
    total_phases: int = Field(..., description="Total number of fixing phases")
    estimated_duration: int = Field(..., description="Estimated duration in minutes")
    phase_details: Dict[str, Any] = Field(default_factory=dict, description="Details for each phase")
    validation_checkpoints: List[str] = Field(default_factory=list, description="Validation checkpoint descriptions")
    rollback_strategy: Dict[str, Any] = Field(default_factory=dict, description="Rollback plan details")
    batch_groups: List[str] = Field(default_factory=list, description="Batch processing group identifiers")
    dependency_order: List[str] = Field(default_factory=list, description="Fix dependency ordering")


class ValidationResult(BaseModel):
    """Results from comprehensive validation testing."""
    build_success: bool = Field(..., description="Whether build completed successfully")
    test_pass_rate: float = Field(..., ge=0.0, le=1.0, description="Percentage of tests passing")
    performance_impact: float = Field(..., description="Performance change (positive = improvement)")
    quality_improvement: float = Field(..., description="Code quality improvement percentage")
    warnings_eliminated: int = Field(default=0, description="Number of warnings eliminated")
    warnings_introduced: int = Field(default=0, description="Number of new warnings introduced")
    validation_timestamp: datetime = Field(default_factory=datetime.now, description="When validation was performed")
    detailed_metrics: Dict[str, Any] = Field(default_factory=dict, description="Detailed validation metrics")


class FactoryWorkflowStatus(BaseModel):
    """Status of a factory workflow session."""
    session_id: str = Field(..., description="Unique session identifier")
    current_phase: str = Field(..., description="Current workflow phase")
    progress_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall progress percentage")
    phases_completed: List[str] = Field(default_factory=list, description="Completed phases")
    active_subagents: List[str] = Field(default_factory=list, description="Currently active subagents")
    issues_discovered: int = Field(default=0, description="Total issues discovered")
    issues_resolved: int = Field(default=0, description="Total issues resolved")
    estimated_time_remaining: int = Field(default=0, description="Estimated minutes remaining")
    last_update: datetime = Field(default_factory=datetime.now, description="Last status update time")


class SubagentResult(BaseModel):
    """Result from a specialized subagent execution."""
    subagent_name: str = Field(..., description="Name of the subagent")
    execution_time: float = Field(..., description="Execution time in seconds")
    success: bool = Field(..., description="Whether execution was successful")
    issues_processed: int = Field(default=0, description="Number of issues processed")
    fixes_applied: int = Field(default=0, description="Number of fixes applied")
    output_summary: str = Field(..., description="Summary of subagent output")
    detailed_results: Dict[str, Any] = Field(default_factory=dict, description="Detailed results data")
    warnings_or_errors: List[str] = Field(default_factory=list, description="Any warnings or errors encountered")


class FactoryReport(BaseModel):
    """Comprehensive report from a completed factory workflow."""
    session_id: str = Field(..., description="Session identifier")
    target_files: List[str] = Field(default_factory=list, description="Files processed")
    total_duration: float = Field(..., description="Total duration in seconds")
    workflow_phases: Dict[str, SubagentResult] = Field(default_factory=dict, description="Results from each phase")
    
    # Summary metrics
    total_issues_discovered: int = Field(default=0, description="Total issues found")
    total_issues_resolved: int = Field(default=0, description="Total issues fixed")
    build_status: str = Field(..., description="Final build status")
    test_status: str = Field(..., description="Final test suite status")
    
    # Quality improvements
    performance_improvement: float = Field(default=0.0, description="Performance improvement percentage")
    code_quality_improvement: float = Field(default=0.0, description="Code quality improvement percentage")
    technical_debt_reduction: float = Field(default=0.0, description="Technical debt reduction percentage")
    
    # Recommendations and next steps
    maintenance_recommendations: List[str] = Field(default_factory=list, description="Ongoing maintenance recommendations")
    quality_gates_suggestions: List[str] = Field(default_factory=list, description="Suggested quality gates")
    future_improvement_opportunities: List[str] = Field(default_factory=list, description="Future improvement opportunities")
    
    # Detailed metrics
    before_after_metrics: Dict[str, Any] = Field(default_factory=dict, description="Before/after comparison metrics")
    subagent_performance: Dict[str, float] = Field(default_factory=dict, description="Performance metrics for each subagent")
    
    report_generation_time: datetime = Field(default_factory=datetime.now, description="When report was generated")


# CLion Integration Models for Zero Diagnostics System

class CLionDiagnostic(BaseModel):
    """Represents a CLion IDE diagnostic (error, warning, info)."""
    uri: str = Field(..., description="File URI from CLion")
    range: Dict[str, Any] = Field(..., description="Diagnostic range in file")
    severity: str = Field(..., description="Diagnostic severity (error, warning, info)")
    code: Optional[str] = Field(None, description="Diagnostic code identifier")
    source: Optional[str] = Field(None, description="Diagnostic source (clang, clang-tidy, etc.)")
    message: str = Field(..., description="Diagnostic message")
    related_information: List[Dict[str, Any]] = Field(default_factory=list, description="Related diagnostic information")
    tags: List[str] = Field(default_factory=list, description="Diagnostic tags")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional diagnostic data")

class DiagnosticCategory(BaseModel):
    """Categorizes diagnostics for prioritized fixing."""
    category_name: str = Field(..., description="Category name (compilation_errors, warnings, info_suggestions)")
    priority: int = Field(..., description="Fix priority (1=highest, 10=lowest)")
    diagnostics: List[CLionDiagnostic] = Field(default_factory=list, description="Diagnostics in this category")
    fix_order: List[str] = Field(default_factory=list, description="Order to fix diagnostics to avoid cascades")

class IncrementalFixResult(BaseModel):
    """Result from applying a single incremental fix."""
    diagnostic_fixed: CLionDiagnostic = Field(..., description="Diagnostic that was fixed")
    fix_applied: str = Field(..., description="Description of fix applied")
    new_diagnostics_count: int = Field(default=0, description="Number of new diagnostics introduced")
    remaining_diagnostics_count: int = Field(..., description="Number of diagnostics remaining")
    validation_passed: bool = Field(..., description="Whether validation passed after fix")
    rollback_performed: bool = Field(default=False, description="Whether fix was rolled back")
    rollback_reason: Optional[str] = Field(None, description="Reason for rollback if performed")
    fix_duration: float = Field(..., description="Time taken to apply and validate fix")

class ZeroDiagnosticsSession(BaseModel):
    """Session tracking for achieving zero CLion diagnostics."""
    session_id: str = Field(..., description="Unique session identifier")
    target_files: List[str] = Field(..., description="Files being processed for zero diagnostics")
    initial_diagnostic_count: int = Field(..., description="Initial number of diagnostics")
    current_diagnostic_count: int = Field(..., description="Current number of diagnostics")
    fixes_applied: List[IncrementalFixResult] = Field(default_factory=list, description="All fixes applied")
    rollbacks_performed: int = Field(default=0, description="Number of rollbacks performed")
    session_start_time: datetime = Field(default_factory=datetime.now, description="Session start time")
    last_validation_time: datetime = Field(default_factory=datetime.now, description="Last validation timestamp")
    zero_diagnostics_achieved: bool = Field(default=False, description="Whether zero diagnostics was achieved")

class CLionConnectionStatus(BaseModel):
    """Status of connection to CLion IDE."""
    connected: bool = Field(..., description="Whether connection to CLion is active")
    mcp_available: bool = Field(..., description="Whether mcp__ide__getDiagnostics is available")
    last_connection_attempt: datetime = Field(default_factory=datetime.now, description="Last connection attempt")
    connection_error: Optional[str] = Field(None, description="Connection error message if any")
    ide_version: Optional[str] = Field(None, description="CLion IDE version if available")