"""
Pydantic models for Clang-Tidy AI Agent.
Defines data structures for code analysis, warnings, and fix suggestions.
"""

from enum import Enum
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, field_validator, ConfigDict


# Pydantic AI Response Models (TestModel/FunctionModel patterns)
class IssueDiscoveryResponse(BaseModel):
    """Response model for issue discovery analysis."""
    total_issues: int = Field(..., description="Total number of issues found")
    critical_issues: List[str] = Field(default_factory=list, description="Critical compilation/build blockers")
    high_priority_issues: List[str] = Field(default_factory=list, description="Security, safety, performance issues")
    medium_priority_issues: List[str] = Field(default_factory=list, description="Readability, maintainability issues")
    low_priority_issues: List[str] = Field(default_factory=list, description="Style and modernization issues")
    analysis_summary: str = Field(..., description="Summary of discovered issues")
    fix_complexity_estimate: str = Field(..., description="Estimated complexity of fixes")


class FixStrategyResponse(BaseModel):
    """Response model for fix strategy planning."""
    strategy_name: str = Field(..., description="Name of the fix strategy")
    fix_order: List[str] = Field(default_factory=list, description="Ordered list of fixes to apply")
    batch_groups: Dict[str, List[str]] = Field(default_factory=dict, description="Grouped fixes for batch processing")
    validation_checkpoints: List[str] = Field(default_factory=list, description="Validation points between fix stages")
    rollback_plan: str = Field(..., description="Rollback strategy if fixes fail")
    estimated_time: str = Field(..., description="Estimated time to complete all fixes")


class FixApplicationResponse(BaseModel):
    """Response model for fix application results."""
    fixes_applied: int = Field(default=0, description="Number of fixes successfully applied")
    fixes_failed: int = Field(default=0, description="Number of fixes that failed")
    warnings_resolved: int = Field(default=0, description="Number of warnings resolved")
    new_warnings: int = Field(default=0, description="Number of new warnings introduced")
    build_status: str = Field(..., description="Build status after fixes")
    recommendations: List[str] = Field(default_factory=list, description="Next steps or recommendations")


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    validation_passed: bool = Field(..., description="Whether validation passed")
    build_successful: bool = Field(..., description="Whether build was successful")
    test_results: Dict[str, Any] = Field(default_factory=dict, description="Test execution results")
    performance_impact: Optional[str] = Field(None, description="Performance impact assessment")
    quality_metrics: Dict[str, float] = Field(default_factory=dict, description="Code quality metrics")
    final_recommendations: List[str] = Field(default_factory=list, description="Final recommendations")


class ArchonTaskResponse(BaseModel):
    """Response model for Archon MCP integration."""
    task_created: bool = Field(..., description="Whether task was created successfully")
    task_id: Optional[str] = Field(None, description="Created task ID")
    knowledge_retrieved: bool = Field(..., description="Whether knowledge was successfully retrieved")
    recommendations: List[str] = Field(default_factory=list, description="Knowledge-based recommendations")
    next_actions: List[str] = Field(default_factory=list, description="Suggested next actions")


class WarningCategory(str, Enum):
    """Categories of clang-tidy warnings."""
    READABILITY = "readability"
    PERFORMANCE = "performance"
    BUGPRONE = "bugprone"
    MODERNIZE = "modernize"
    CPPCOREGUIDELINES = "cppcoreguidelines"
    CERT = "cert"
    CONCURRENCY = "concurrency"
    MISC = "misc"
    GOOGLE = "google"
    LLVM = "llvm"


class SeverityLevel(str, Enum):
    """Severity levels for warnings."""
    ERROR = "error"
    WARNING = "warning"
    NOTE = "note"
    INFO = "info"


class ClangTidyConfig(BaseModel):
    """Configuration for clang-tidy analysis."""
    checks: str = Field(default="-*,readability-*,performance-*,bugprone-*", description="Clang-tidy checks to run")
    header_filter: str = Field(default=".*", description="Header filter pattern")
    warnings_as_errors: str = Field(default="", description="Treat warnings as errors")
    format_style: str = Field(default="file", description="Code formatting style")
    fix: bool = Field(default=False, description="Apply fixes automatically")
    use_color: bool = Field(default=True, description="Use colored output")
    quiet: bool = Field(default=False, description="Suppress diagnostic messages")


class CodeWarning(BaseModel):
    """Represents a clang-tidy warning."""
    file_path: str = Field(..., description="Path to the file with the warning")
    line_number: int = Field(..., description="Line number of the warning")
    column_number: int = Field(..., description="Column number of the warning")
    check_name: str = Field(..., description="Name of the clang-tidy check")
    category: WarningCategory = Field(..., description="Category of the warning")
    severity: SeverityLevel = Field(..., description="Severity level")
    message: str = Field(..., description="Warning message")
    source_code: Optional[str] = Field(None, description="Source code snippet")
    suggested_fix: Optional[str] = Field(None, description="Suggested fix")
    
    @field_validator('line_number', 'column_number')
    @classmethod
    def validate_positive(cls, v):
        """Validate that line and column numbers are positive."""
        if v <= 0:
            raise ValueError("Line and column numbers must be positive")
        return v


class AnalysisResult(BaseModel):
    """Result from clang-tidy analysis."""
    file_path: str = Field(..., description="Path to analyzed file")
    warnings: List[CodeWarning] = Field(default_factory=list, description="List of warnings found")
    total_warnings: int = Field(default=0, description="Total number of warnings")
    errors: int = Field(default=0, description="Number of errors")
    fixes_applied: int = Field(default=0, description="Number of fixes applied")
    analysis_time: float = Field(default=0.0, description="Time taken for analysis in seconds")


class FixSuggestion(BaseModel):
    """AI-generated fix suggestion for a warning."""
    warning_id: str = Field(..., description="ID of the warning to fix")
    fix_type: str = Field(..., description="Type of fix (replace, insert, remove)")
    original_code: str = Field(..., description="Original problematic code")
    suggested_code: str = Field(..., description="Suggested fixed code")
    explanation: str = Field(..., description="Explanation of the fix")
    confidence: float = Field(..., description="Confidence in fix suggestion (0.0-1.0)")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        """Validate confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        return v


class ProjectAnalysis(BaseModel):
    """Complete project analysis results."""
    project_path: str = Field(..., description="Path to analyzed project")
    files_analyzed: List[str] = Field(default_factory=list, description="List of analyzed files")
    total_warnings: int = Field(default=0, description="Total warnings across all files")
    warning_categories: Dict[str, int] = Field(default_factory=dict, description="Warnings by category")
    severity_breakdown: Dict[str, int] = Field(default_factory=dict, description="Warnings by severity")
    fix_suggestions: List[FixSuggestion] = Field(default_factory=list, description="AI-generated fix suggestions")
    summary: str = Field(default="", description="AI-generated summary of analysis")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")


class ClangTidyDependencies(BaseModel):
    """Dependencies for the Clang-Tidy AI agent."""
    model_config = ConfigDict(protected_namespaces=())
    
    clang_tidy_path: str = Field(default="clang-tidy", description="Path to clang-tidy executable")
    compilation_database_path: Optional[str] = Field(None, description="Path to compile_commands.json")
    config_file_path: Optional[str] = Field(None, description="Path to .clang-tidy config file")
    temp_directory: str = Field(default="/tmp/clang_tidy_analysis", description="Directory for temporary files")
    max_analysis_time: int = Field(default=300, description="Maximum analysis time in seconds")
    enable_ai_suggestions: bool = Field(default=True, description="Enable AI-powered fix suggestions")
    llm_provider: str = Field(default="openai", description="LLM provider for AI analysis")
    llm_model: str = Field(default="gpt-4", description="Model name for AI analysis")
    api_key: Optional[str] = Field(None, description="API key for LLM provider")
    db_connection: Optional[Any] = Field(default=None, description="Database connection")
    settings: Optional[Any] = Field(default=None, description="Settings configuration")
    archon_client: Optional[Any] = Field(default=None, description="Archon MCP client for knowledge integration")
    
    @field_validator('max_analysis_time')
    @classmethod
    def validate_analysis_time(cls, v):
        """Validate analysis time is reasonable."""
        if v <= 0 or v > 3600:  # Max 1 hour
            raise ValueError("Analysis time must be between 1 and 3600 seconds")
        return v