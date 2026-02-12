"""
Data models for MT5 Infinite Reliability Agent.

Defines structures for MQL5 optimization, analysis findings, and FTMO compliance.
Follows the awareness_orchestrator pattern for agent coordination.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class OptimizationDimension(Enum):
    """MQL5 code optimization dimensions."""
    PERFORMANCE = "performance"
    MEMORY = "memory"
    RELIABILITY = "reliability"
    FTMO_COMPLIANCE = "ftmo_compliance"
    BACKTEST_ACCURACY = "backtest_accuracy"
    EVENT_DRIVEN = "event_driven"


class Severity(Enum):
    """Issue severity levels for MQL5 analysis."""
    CRITICAL = "critical"  # Compilation errors, memory leaks
    HIGH = "high"  # Performance bottlenecks, unsafe patterns
    MEDIUM = "medium"  # Suboptimal patterns, missing caching
    LOW = "low"  # Style issues, minor optimizations
    INFO = "info"  # Recommendations, best practices


class AgentType(Enum):
    """Specialized MQL5 optimization agent types."""
    PARSER = "parser"  # AST parsing and structure analysis
    OPTIMIZER = "optimizer"  # Performance and efficiency optimization
    FTMO_COMPLIANCE = "ftmo_compliance"  # FTMO rule validation
    VERIFICATION = "verification"  # Mathematical verification and proofs
    DOCUMENTATION = "documentation"  # MQL5 reference documentation lookup


class EscalationTier(Enum):
    """Resolution escalation tiers (from never-fail-build-resolver pattern)."""
    FAST = "fast"  # 2-3 minutes, 90% success rate
    SMART = "smart"  # 5-10 minutes, 99% success rate
    THOROUGH = "thorough"  # 10-20 minutes, 99.9% success rate
    EMERGENCY = "emergency"  # Nuclear reset options


@dataclass
class MQL5Pattern:
    """Detected MQL5 code pattern requiring optimization."""
    pattern_type: str
    description: str
    file_path: str
    line_start: int
    line_end: int
    code_snippet: str
    optimization_potential: float  # 0.0 to 1.0
    category: str  # loop, indicator, event, cache, etc.


@dataclass
class OptimizationIssue:
    """Individual MQL5 optimization issue."""
    title: str
    description: str
    severity: Severity
    dimension: OptimizationDimension
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    fix_suggestion: Optional[str] = None
    mql5_reference: Optional[str] = None  # Citation from MQL5 PDF/docs
    estimated_improvement: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class OptimizationTransformation:
    """Code transformation with proof annotation."""
    transformation_id: str
    issue_id: str
    original_code: str
    optimized_code: str
    proof_annotation: str  # Mathematical justification
    preserves_semantics: bool
    performance_gain: Optional[float] = None  # Percentage improvement
    mql5_documentation_citation: Optional[str] = None


@dataclass
class FTMOComplianceCheck:
    """FTMO compliance validation result."""
    rule_name: str
    passed: bool
    current_value: Optional[float] = None
    threshold: Optional[float] = None
    description: str = ""
    recommendation: Optional[str] = None


@dataclass
class FTMOComplianceReport:
    """Complete FTMO compliance assessment."""
    overall_compliant: bool
    checks: List[FTMOComplianceCheck]
    drawdown_monitoring: bool
    daily_loss_limit_implemented: bool
    max_drawdown_limit_implemented: bool
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AgentFindings:
    """Findings from a single agent execution."""
    agent_type: AgentType
    findings: List[OptimizationIssue]
    patterns_detected: List[MQL5Pattern]
    summary: str
    duration: float
    escalation_tier: EscalationTier = EscalationTier.FAST
    timestamp: datetime = field(default_factory=datetime.now)
    mql5_references_used: List[str] = field(default_factory=list)


@dataclass
class OptimizationContext:
    """Context passed between agents during optimization workflow."""
    file_path: str
    target_directory: str
    original_code: str
    optimization_goals: List[OptimizationDimension]
    previous_findings: List[AgentFindings] = field(default_factory=list)
    preserve_features: bool = True
    ftmo_compliance_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OptimizationResult:
    """Complete optimization workflow result."""
    success: bool
    agent_findings: List[AgentFindings]
    transformations: List[OptimizationTransformation]
    ftmo_compliance: Optional[FTMOComplianceReport]
    optimized_code: Optional[str]
    summary: str
    total_duration: float
    recommendations: List[str]
    errors: List[str] = field(default_factory=list)
    context: Optional[OptimizationContext] = None
    escalation_history: List[EscalationTier] = field(default_factory=list)

    def get_all_issues(self) -> List[OptimizationIssue]:
        """Get all issues from all agents."""
        all_issues = []
        for agent_finding in self.agent_findings:
            all_issues.extend(agent_finding.findings)
        return all_issues

    def get_issues_by_severity(self, severity: Severity) -> List[OptimizationIssue]:
        """Filter issues by severity level."""
        return [
            issue for issue in self.get_all_issues()
            if issue.severity == severity
        ]

    def get_critical_issues(self) -> List[OptimizationIssue]:
        """Get all critical severity issues."""
        return self.get_issues_by_severity(Severity.CRITICAL)

    def get_performance_improvements(self) -> List[OptimizationTransformation]:
        """Get transformations with measured performance improvements."""
        return [t for t in self.transformations if t.performance_gain and t.performance_gain > 0]


@dataclass
class CacheableIndicatorData:
    """Cached indicator data structure for optimization."""
    indicator_handle: int
    symbol: str
    timeframe: str
    buffer_data: List[float]
    last_update_bar: int
    cache_valid: bool = True


@dataclass
class NewBarTrigger:
    """Event-driven new bar detection state."""
    symbol: str
    timeframe: str
    last_bar_time: datetime
    trigger_count: int = 0


@dataclass
class PerformanceMetrics:
    """Performance measurement for optimized code."""
    execution_time_ms: float
    memory_usage_mb: float
    indicator_calls_count: int
    loop_iterations: int
    cache_hit_rate: float
    backtest_accuracy_score: float


@dataclass
class MQL5DocumentationRef:
    """Reference to official MQL5 documentation."""
    section: str
    page_number: Optional[int]
    url: str
    excerpt: str
    relevance_to_optimization: str


@dataclass
class OptimizationProof:
    """Mathematical proof for code transformation."""
    proof_id: str
    transformation_id: str
    proof_type: str  # "semantic_equivalence", "performance_bound", "safety_guarantee"
    preconditions: List[str]
    postconditions: List[str]
    invariants: List[str]
    proof_steps: List[str]
    verification_method: str
    confidence_score: float  # 0.0 to 1.0


@dataclass
class AgentHandoff:
    """Agent collaboration handoff instruction."""
    from_agent: AgentType
    to_agent: AgentType
    reason: str
    context_data: Dict[str, Any]
    priority: str  # "immediate", "after_completion", "conditional"
    escalation_condition: Optional[str] = None
