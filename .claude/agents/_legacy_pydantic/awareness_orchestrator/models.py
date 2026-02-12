"""
Data models for Awareness Orchestrator.

Defines structures for agent findings, orchestration results, and context.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime


class Severity(Enum):
    """Issue severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AgentType(Enum):
    """Orchestrator agent types."""
    ANALYSIS = "analysis"
    ARCHITECTURE = "architecture"
    VALIDATION = "validation"


@dataclass
class Finding:
    """Individual analysis finding."""
    title: str
    description: str
    severity: Severity
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentFindings:
    """Findings from a single agent execution."""
    agent_type: AgentType
    findings: List[Finding]
    summary: str
    duration: float
    timestamp: datetime = field(default_factory=datetime.now)
    context_used: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationContext:
    """Context passed between agents during orchestration."""
    file_path: str
    task_description: str
    previous_findings: List[AgentFindings] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrchestrationResult:
    """Complete orchestration results from all agents."""
    success: bool
    agent_findings: List[AgentFindings]
    summary: str
    total_duration: float
    recommendations: List[str]
    errors: List[str] = field(default_factory=list)
    context: Optional[OrchestrationContext] = None

    def get_all_findings(self) -> List[Finding]:
        """Get all findings from all agents."""
        all_findings = []
        for agent_finding in self.agent_findings:
            all_findings.extend(agent_finding.findings)
        return all_findings

    def get_findings_by_severity(self, severity: Severity) -> List[Finding]:
        """Filter findings by severity level."""
        return [
            finding
            for finding in self.get_all_findings()
            if finding.severity == severity
        ]

    def get_critical_issues(self) -> List[Finding]:
        """Get all critical severity findings."""
        return self.get_findings_by_severity(Severity.CRITICAL)


@dataclass
class BuildResult:
    """Build system execution result."""
    success: bool
    duration: float
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""


@dataclass
class TestResult:
    """Test execution result."""
    total: int
    passed: int
    failed: int
    duration: float
    failed_tests: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if all tests passed."""
        return self.failed == 0


@dataclass
class ValidationResult:
    """Validation pipeline result."""
    build_result: BuildResult
    test_result: Optional[TestResult] = None
    success: bool = False
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Auto-determine success based on build and test results."""
        self.success = self.build_result.success
        if self.test_result:
            self.success = self.success and self.test_result.success


@dataclass
class Pattern:
    """Learned pattern from historical orchestrations."""
    pattern_type: str
    description: str
    occurrences: int
    success_rate: float
    last_seen: datetime
    agent_sequence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Suggestion:
    """Proactive suggestion for code improvement."""
    suggestion_type: str
    title: str
    description: str
    priority: str  # critical, high, medium, low
    file_path: str
    line_number: Optional[int] = None
    code_example: Optional[str] = None
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.suggestion_type,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "code_example": self.code_example,
            "rationale": self.rationale
        }


@dataclass
class Metric:
    """Performance metric for dashboard."""
    name: str
    value: float
    unit: str
    trend: Optional[str] = None  # "up", "down", "stable"
    metadata: Dict[str, Any] = field(default_factory=dict)
