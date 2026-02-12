"""Pydantic models for the Blitzfire Code Agent."""

from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class OptimizationMode(str, Enum):
    """Optimization modes supported by Blitzfire."""
    GENERAL = "general"
    HFT = "hft"
    EMBEDDED = "embedded"
    GAME = "game"


class SafetyLevel(str, Enum):
    """Safety constraint levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Architecture(str, Enum):
    """Target architectures."""
    X86_64 = "x86_64"
    ARM64 = "arm64"
    ARM32 = "arm32"


class CodeIssue(BaseModel):
    """Represents a performance issue found in code analysis."""
    line_number: int = Field(..., description="Line number where issue was found")
    issue_type: str = Field(..., description="Type of performance issue")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    description: str = Field(..., description="Human-readable description of the issue")
    suggestion: str = Field(..., description="Suggested optimization or fix")
    estimated_impact: float = Field(..., description="Estimated performance impact (speedup multiplier)")


class ComplexityAnalysis(BaseModel):
    """Algorithm complexity analysis results."""
    time_complexity: str = Field(..., description="Big-O time complexity")
    space_complexity: str = Field(..., description="Big-O space complexity")
    hotspots: List[int] = Field(default_factory=list, description="Line numbers of computational hotspots")
    loop_nesting_depth: int = Field(default=0, description="Maximum loop nesting depth")
    recursive_calls: int = Field(default=0, description="Number of recursive calls detected")


class OptimizationTier(BaseModel):
    """Represents a single optimization tier with implementation details."""
    tier_number: int = Field(..., description="Tier level (1=simple, higher=advanced)")
    name: str = Field(..., description="Human-readable tier name")
    description: str = Field(..., description="What this tier optimizes")
    estimated_speedup: float = Field(..., description="Expected performance multiplier")
    difficulty: str = Field(..., description="Implementation difficulty (easy, medium, hard)")
    safety_impact: str = Field(..., description="Impact on code safety")
    code_before: str = Field(..., description="Original code snippet")
    code_after: str = Field(..., description="Optimized code snippet")
    explanation: str = Field(..., description="Educational explanation of why this works")


class OptimizationStrategy(BaseModel):
    """Complete multi-tier optimization strategy."""
    total_estimated_speedup: float = Field(..., description="Combined speedup estimate")
    recommended_order: List[int] = Field(..., description="Recommended implementation order")
    tiers: List[OptimizationTier] = Field(..., description="Individual optimization tiers")
    warnings: List[str] = Field(default_factory=list, description="Important warnings or caveats")
    next_steps: List[str] = Field(default_factory=list, description="Suggested next optimizations")


class AssemblyComparison(BaseModel):
    """Assembly code comparison results."""
    original_instructions: int = Field(..., description="Number of instructions in original")
    optimized_instructions: int = Field(..., description="Number of instructions in optimized")
    vectorization_detected: bool = Field(default=False, description="Whether vectorization was detected")
    loop_unrolling_detected: bool = Field(default=False, description="Whether loop unrolling was detected")
    key_differences: List[str] = Field(..., description="Key differences in assembly")
    optimization_artifacts: List[str] = Field(..., description="Compiler optimization artifacts found")


class BenchmarkResult(BaseModel):
    """Performance benchmark measurement results."""
    function_name: str = Field(..., description="Name of benchmarked function")
    input_size: int = Field(..., description="Input size parameter")
    mean_time_ns: float = Field(..., description="Mean execution time in nanoseconds")
    std_dev_ns: float = Field(..., description="Standard deviation in nanoseconds")
    iterations: int = Field(..., description="Number of benchmark iterations")
    speedup_ratio: Optional[float] = Field(None, description="Speedup ratio vs baseline")


class AnalysisResult(BaseModel):
    """Complete code analysis result."""
    # Basic metadata
    timestamp: datetime = Field(default_factory=datetime.now)
    code_hash: str = Field(..., description="Hash of analyzed code for caching")
    architecture: Architecture = Field(default=Architecture.X86_64)
    optimization_mode: OptimizationMode = Field(default=OptimizationMode.GENERAL)

    # Analysis results
    issues: List[CodeIssue] = Field(default_factory=list)
    complexity: ComplexityAnalysis = Field(...)
    optimization_candidates: List[str] = Field(default_factory=list)

    # Performance estimates
    baseline_score: float = Field(..., description="Baseline performance score")
    optimization_potential: float = Field(..., description="Estimated maximum speedup potential")

    # Summary statistics
    total_issues: int = Field(..., description="Total number of issues found")
    critical_issues: int = Field(default=0, description="Number of critical issues")
    lines_analyzed: int = Field(..., description="Total lines of code analyzed")


class BlitzfireResponse(BaseModel):
    """Complete Blitzfire agent response."""
    # Analysis summary
    analysis: AnalysisResult = Field(...)

    # Optimization strategy
    strategy: OptimizationStrategy = Field(...)

    # Validation results (optional)
    assembly_comparison: Optional[AssemblyComparison] = None
    benchmark_results: List[BenchmarkResult] = Field(default_factory=list)

    # Educational content
    personality_message: str = Field(..., description="Enthusiastic response with personality")
    educational_insights: List[str] = Field(default_factory=list, description="Learning points")

    # Follow-up suggestions
    recommended_next_steps: List[str] = Field(default_factory=list)
    additional_resources: List[str] = Field(default_factory=list)

    # Metadata
    blitzfire_score: int = Field(..., description="Overall optimization score (1-10)", ge=1, le=10)
    processing_time_seconds: float = Field(..., description="Time taken to generate response")


class HFTAuditResult(BaseModel):
    """HFT-specific code audit results."""
    overflow_risks: List[CodeIssue] = Field(default_factory=list)
    race_conditions: List[CodeIssue] = Field(default_factory=list)
    determinism_issues: List[CodeIssue] = Field(default_factory=list)
    lock_free_violations: List[CodeIssue] = Field(default_factory=list)
    regulatory_concerns: List[str] = Field(default_factory=list)
    safety_score: int = Field(..., description="HFT safety score (1-10)", ge=1, le=10)
    recommendations: List[str] = Field(default_factory=list)


class ConversationContext(BaseModel):
    """Context for conversational interactions."""
    session_id: str = Field(..., description="Unique session identifier")
    previous_analyses: Dict[str, AnalysisResult] = Field(default_factory=dict)
    conversation_history: List[Dict[str, str]] = Field(default_factory=list)
    user_preferences: Dict[str, Any] = Field(default_factory=dict)
    current_focus: Optional[str] = Field(None, description="Current optimization focus area")