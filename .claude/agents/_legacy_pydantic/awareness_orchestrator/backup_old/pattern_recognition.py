"""
Advanced Pattern Recognition System
Learns from historical orchestration runs to identify patterns and improve future performance
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, Counter
from enum import Enum


class PatternType(str, Enum):
    """Types of patterns that can be recognized."""
    ERROR_PATTERN = "error_pattern"
    SUCCESS_PATTERN = "success_pattern"
    PERFORMANCE_PATTERN = "performance_pattern"
    AGENT_BEHAVIOR = "agent_behavior"
    CODE_SMELL = "code_smell"
    RECURRING_ISSUE = "recurring_issue"


class Severity(str, Enum):
    """Pattern severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class Pattern:
    """Represents a recognized pattern."""
    pattern_id: str
    pattern_type: PatternType
    severity: Severity
    name: str
    description: str
    occurrences: int = 1
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    files_affected: List[str] = field(default_factory=list)
    agents_involved: List[str] = field(default_factory=list)
    error_messages: List[str] = field(default_factory=list)
    resolution_strategies: List[Dict[str, Any]] = field(default_factory=list)
    success_rate: float = 0.0
    avg_resolution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["first_seen"] = self.first_seen.isoformat()
        data["last_seen"] = self.last_seen.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        """Create Pattern from dictionary."""
        data = data.copy()
        data["first_seen"] = datetime.fromisoformat(data["first_seen"])
        data["last_seen"] = datetime.fromisoformat(data["last_seen"])
        data["pattern_type"] = PatternType(data["pattern_type"])
        data["severity"] = Severity(data["severity"])
        return cls(**data)


@dataclass
class OrchestrationRun:
    """Record of a single orchestration run."""
    run_id: str
    timestamp: datetime
    target_file: str
    agents_executed: List[str]
    duration: float
    success: bool
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)
    fixes_applied: int = 0
    tests_passed: bool = False
    build_success: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "OrchestrationRun":
        """Create OrchestrationRun from dictionary."""
        data = data.copy()
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


class PatternRecognitionSystem:
    """
    Advanced pattern recognition and learning system.

    Features:
    - Historical error pattern analysis
    - Success pattern identification
    - Agent performance tracking
    - Recommendation generation
    - Pattern-based optimization
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize pattern recognition system.

        Args:
            storage_path: Path to store pattern database (defaults to .claude/agents/awareness_orchestrator/patterns/)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent / "patterns"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.patterns_file = self.storage_path / "patterns.json"
        self.runs_file = self.storage_path / "orchestration_runs.json"

        # Load existing data
        self.patterns: Dict[str, Pattern] = self._load_patterns()
        self.orchestration_runs: List[OrchestrationRun] = self._load_runs()

        # Performance tracking
        self.agent_performance: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "total_runs": 0,
            "success_count": 0,
            "failure_count": 0,
            "avg_duration": 0.0,
            "issues_found": 0,
            "issues_fixed": 0
        })

        self._update_agent_performance()

    def _load_patterns(self) -> Dict[str, Pattern]:
        """Load patterns from storage."""
        if not self.patterns_file.exists():
            return {}

        try:
            with open(self.patterns_file, 'r') as f:
                data = json.load(f)
                return {
                    pid: Pattern.from_dict(pdata)
                    for pid, pdata in data.items()
                }
        except Exception as e:
            print(f"Warning: Failed to load patterns: {e}")
            return {}

    def _load_runs(self) -> List[OrchestrationRun]:
        """Load orchestration runs from storage."""
        if not self.runs_file.exists():
            return []

        try:
            with open(self.runs_file, 'r') as f:
                data = json.load(f)
                return [OrchestrationRun.from_dict(run) for run in data]
        except Exception as e:
            print(f"Warning: Failed to load runs: {e}")
            return []

    def _save_patterns(self):
        """Save patterns to storage."""
        try:
            data = {
                pid: pattern.to_dict()
                for pid, pattern in self.patterns.items()
            }
            with open(self.patterns_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save patterns: {e}")

    def _save_runs(self):
        """Save orchestration runs to storage."""
        try:
            data = [run.to_dict() for run in self.orchestration_runs]
            with open(self.runs_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Warning: Failed to save runs: {e}")

    def _update_agent_performance(self):
        """Update agent performance metrics from historical runs."""
        for run in self.orchestration_runs:
            for agent in run.agents_executed:
                perf = self.agent_performance[agent]
                perf["total_runs"] += 1

                if run.success:
                    perf["success_count"] += 1
                else:
                    perf["failure_count"] += 1

                # Update rolling average duration
                total = perf["total_runs"]
                perf["avg_duration"] = (
                    (perf["avg_duration"] * (total - 1) + run.duration) / total
                )

    def record_orchestration_run(self, run: OrchestrationRun):
        """
        Record a new orchestration run and analyze for patterns.

        Args:
            run: OrchestrationRun instance with execution details
        """
        self.orchestration_runs.append(run)
        self._save_runs()

        # Update agent performance
        for agent in run.agents_executed:
            perf = self.agent_performance[agent]
            perf["total_runs"] += 1

            if run.success:
                perf["success_count"] += 1
            else:
                perf["failure_count"] += 1

            # Update rolling average
            total = perf["total_runs"]
            perf["avg_duration"] = (
                (perf["avg_duration"] * (total - 1) + run.duration) / total
            )

        # Analyze for patterns
        self._analyze_run_for_patterns(run)

    def _analyze_run_for_patterns(self, run: OrchestrationRun):
        """Analyze orchestration run to identify patterns."""

        # Error pattern analysis
        for error in run.errors:
            self._identify_error_pattern(error, run)

        # Success pattern analysis
        if run.success and run.build_success and run.tests_passed:
            self._identify_success_pattern(run)

        # Performance pattern analysis
        if run.duration > 0:
            self._identify_performance_pattern(run)

        # Recurring issue detection
        self._detect_recurring_issues(run)

    def _identify_error_pattern(self, error: Dict[str, Any], run: OrchestrationRun):
        """Identify and record error patterns."""
        error_msg = error.get("message", "")
        file_path = error.get("file", "")

        # Extract error type (compiler error, linker error, runtime error, etc.)
        error_type = self._classify_error(error_msg)

        # Create pattern ID from error characteristics
        pattern_id = f"error_{error_type}_{hash(error_msg[:100]) % 10000}"

        if pattern_id in self.patterns:
            # Update existing pattern
            pattern = self.patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_seen = datetime.now()

            if file_path and file_path not in pattern.files_affected:
                pattern.files_affected.append(file_path)

            for agent in run.agents_executed:
                if agent not in pattern.agents_involved:
                    pattern.agents_involved.append(agent)

            if error_msg not in pattern.error_messages:
                pattern.error_messages.append(error_msg)
        else:
            # Create new pattern
            severity = self._determine_severity(error_type, error_msg)

            pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type=PatternType.ERROR_PATTERN,
                severity=severity,
                name=f"{error_type.title()} Error",
                description=f"Recurring {error_type} error pattern",
                files_affected=[file_path] if file_path else [],
                agents_involved=run.agents_executed,
                error_messages=[error_msg]
            )

            self.patterns[pattern_id] = pattern

        self._save_patterns()

    def _identify_success_pattern(self, run: OrchestrationRun):
        """Identify successful resolution patterns."""
        pattern_id = f"success_{run.target_file}_{len(run.agents_executed)}_agents"

        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.occurrences += 1
            pattern.last_seen = datetime.now()
            pattern.success_rate = (
                (pattern.success_rate * (pattern.occurrences - 1) + 1.0) / pattern.occurrences
            )
            pattern.avg_resolution_time = (
                (pattern.avg_resolution_time * (pattern.occurrences - 1) + run.duration) / pattern.occurrences
            )
        else:
            pattern = Pattern(
                pattern_id=pattern_id,
                pattern_type=PatternType.SUCCESS_PATTERN,
                severity=Severity.INFO,
                name=f"Successful Resolution: {len(run.agents_executed)} Agents",
                description=f"Successfully resolved issues using {', '.join(run.agents_executed)}",
                files_affected=[run.target_file],
                agents_involved=run.agents_executed,
                success_rate=1.0,
                avg_resolution_time=run.duration,
                metadata={
                    "agent_sequence": run.agents_executed,
                    "fixes_applied": run.fixes_applied
                }
            )
            self.patterns[pattern_id] = pattern

        self._save_patterns()

    def _identify_performance_pattern(self, run: OrchestrationRun):
        """Identify performance-related patterns."""
        # Detect slow runs
        avg_duration = sum(r.duration for r in self.orchestration_runs) / max(len(self.orchestration_runs), 1)

        if run.duration > avg_duration * 2:
            pattern_id = f"perf_slow_{run.target_file}"

            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                pattern.occurrences += 1
                pattern.last_seen = datetime.now()
            else:
                pattern = Pattern(
                    pattern_id=pattern_id,
                    pattern_type=PatternType.PERFORMANCE_PATTERN,
                    severity=Severity.MEDIUM,
                    name=f"Slow Orchestration: {run.target_file}",
                    description=f"Orchestration taking longer than average ({run.duration:.1f}s vs {avg_duration:.1f}s avg)",
                    files_affected=[run.target_file],
                    agents_involved=run.agents_executed,
                    metadata={
                        "duration": run.duration,
                        "avg_duration": avg_duration,
                        "slowdown_factor": run.duration / avg_duration
                    }
                )
                self.patterns[pattern_id] = pattern

            self._save_patterns()

    def _detect_recurring_issues(self, run: OrchestrationRun):
        """Detect recurring issues in the same file."""
        # Count recent failures for this file
        recent_runs = [
            r for r in self.orchestration_runs[-20:]  # Last 20 runs
            if r.target_file == run.target_file and not r.success
        ]

        if len(recent_runs) >= 3:  # 3+ failures in last 20 runs
            pattern_id = f"recurring_{run.target_file}"

            if pattern_id in self.patterns:
                pattern = self.patterns[pattern_id]
                pattern.occurrences += 1
                pattern.last_seen = datetime.now()
            else:
                pattern = Pattern(
                    pattern_id=pattern_id,
                    pattern_type=PatternType.RECURRING_ISSUE,
                    severity=Severity.HIGH,
                    name=f"Recurring Issues: {run.target_file}",
                    description=f"File has {len(recent_runs)} failures in recent history",
                    files_affected=[run.target_file],
                    metadata={
                        "recent_failures": len(recent_runs),
                        "total_runs": len([r for r in self.orchestration_runs if r.target_file == run.target_file])
                    }
                )
                self.patterns[pattern_id] = pattern

            self._save_patterns()

    def _classify_error(self, error_msg: str) -> str:
        """Classify error type from error message."""
        error_msg_lower = error_msg.lower()

        if "syntax error" in error_msg_lower or "expected" in error_msg_lower:
            return "syntax"
        elif "undefined reference" in error_msg_lower or "linker" in error_msg_lower:
            return "linker"
        elif "segmentation fault" in error_msg_lower or "segfault" in error_msg_lower:
            return "runtime_memory"
        elif "type" in error_msg_lower and "mismatch" in error_msg_lower:
            return "type_mismatch"
        elif "warning" in error_msg_lower:
            return "warning"
        elif "template" in error_msg_lower:
            return "template"
        elif "conflict marker" in error_msg_lower:
            return "version_control"
        else:
            return "general"

    def _determine_severity(self, error_type: str, error_msg: str) -> Severity:
        """Determine severity level for error pattern."""
        critical_keywords = ["segfault", "crash", "abort", "fatal"]
        high_keywords = ["error", "failed", "undefined reference"]

        error_msg_lower = error_msg.lower()

        if any(kw in error_msg_lower for kw in critical_keywords):
            return Severity.CRITICAL
        elif any(kw in error_msg_lower for kw in high_keywords):
            return Severity.HIGH
        elif "warning" in error_msg_lower:
            return Severity.LOW
        else:
            return Severity.MEDIUM

    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type."""
        return [
            p for p in self.patterns.values()
            if p.pattern_type == pattern_type
        ]

    def get_patterns_by_severity(self, severity: Severity) -> List[Pattern]:
        """Get all patterns of a specific severity."""
        return [
            p for p in self.patterns.values()
            if p.severity == severity
        ]

    def get_patterns_for_file(self, file_path: str) -> List[Pattern]:
        """Get all patterns affecting a specific file."""
        return [
            p for p in self.patterns.values()
            if file_path in p.files_affected
        ]

    def get_most_common_patterns(self, limit: int = 10) -> List[Pattern]:
        """Get most frequently occurring patterns."""
        return sorted(
            self.patterns.values(),
            key=lambda p: p.occurrences,
            reverse=True
        )[:limit]

    def get_agent_performance(self, agent_name: str) -> Dict[str, Any]:
        """Get performance metrics for specific agent."""
        return self.agent_performance.get(agent_name, {})

    def get_best_performing_agents(self, limit: int = 5) -> List[Tuple[str, float]]:
        """Get agents ranked by success rate."""
        agent_scores = []

        for agent, perf in self.agent_performance.items():
            if perf["total_runs"] > 0:
                success_rate = perf["success_count"] / perf["total_runs"]
                agent_scores.append((agent, success_rate))

        return sorted(agent_scores, key=lambda x: x[1], reverse=True)[:limit]

    def recommend_agent_sequence(self, file_path: str, error_context: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Recommend agent execution sequence based on historical patterns.

        Args:
            file_path: Target file path
            error_context: Optional error context for better recommendations

        Returns:
            List of agent names in recommended execution order
        """
        # Get successful patterns for this file
        file_patterns = [
            p for p in self.get_patterns_for_file(file_path)
            if p.pattern_type == PatternType.SUCCESS_PATTERN
        ]

        if file_patterns:
            # Use most successful pattern's agent sequence
            best_pattern = max(file_patterns, key=lambda p: p.success_rate)
            return best_pattern.metadata.get("agent_sequence", [])

        # Fallback: use best performing agents globally
        best_agents = self.get_best_performing_agents(limit=5)
        return [agent for agent, _ in best_agents]

    def get_resolution_strategies(self, pattern_id: str) -> List[Dict[str, Any]]:
        """Get known resolution strategies for a pattern."""
        if pattern_id in self.patterns:
            return self.patterns[pattern_id].resolution_strategies
        return []

    def add_resolution_strategy(
        self,
        pattern_id: str,
        strategy: Dict[str, Any]
    ):
        """Add successful resolution strategy to pattern."""
        if pattern_id in self.patterns:
            pattern = self.patterns[pattern_id]
            pattern.resolution_strategies.append(strategy)
            self._save_patterns()

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive pattern recognition statistics."""
        total_patterns = len(self.patterns)
        total_runs = len(self.orchestration_runs)

        successful_runs = sum(1 for r in self.orchestration_runs if r.success)
        success_rate = (successful_runs / total_runs) if total_runs > 0 else 0.0

        pattern_counts = Counter(p.pattern_type for p in self.patterns.values())
        severity_counts = Counter(p.severity for p in self.patterns.values())

        avg_duration = sum(r.duration for r in self.orchestration_runs) / max(total_runs, 1)

        return {
            "total_patterns": total_patterns,
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "success_rate": success_rate,
            "pattern_counts": dict(pattern_counts),
            "severity_counts": dict(severity_counts),
            "avg_orchestration_duration": avg_duration,
            "total_agents_tracked": len(self.agent_performance),
            "most_common_pattern": self.get_most_common_patterns(limit=1)[0].name if self.patterns else "N/A"
        }


def main():
    """Test pattern recognition system."""
    print("=" * 80)
    print("Pattern Recognition System - Test")
    print("=" * 80)

    # Initialize system
    system = PatternRecognitionSystem()

    print(f"\n📊 Loaded {len(system.patterns)} existing patterns")
    print(f"📊 Loaded {len(system.orchestration_runs)} historical runs")

    # Simulate orchestration run
    print("\n🧪 Simulating orchestration run...")

    run = OrchestrationRun(
        run_id="test-001",
        timestamp=datetime.now(),
        target_file="tests/safe_test.cpp",
        agents_executed=["clang-tidy-analyzer", "clang-tidy-critical-fixer", "zero-warnings-enforcer"],
        duration=45.2,
        success=True,
        errors=[],
        warnings=[{"message": "unused variable 'x'", "file": "tests/safe_test.cpp"}],
        fixes_applied=3,
        tests_passed=True,
        build_success=True
    )

    system.record_orchestration_run(run)
    print("✅ Run recorded")

    # Simulate error pattern
    print("\n🧪 Simulating error pattern...")

    error_run = OrchestrationRun(
        run_id="test-002",
        timestamp=datetime.now(),
        target_file="tests/safe_test.cpp",
        agents_executed=["clang-tidy-analyzer"],
        duration=12.5,
        success=False,
        errors=[{
            "message": "error: version control conflict marker in file",
            "file": "tests/safe_test.cpp",
            "line": 1
        }],
        warnings=[],
        fixes_applied=0,
        tests_passed=False,
        build_success=False
    )

    system.record_orchestration_run(error_run)
    print("✅ Error pattern recorded")

    # Get statistics
    print("\n📊 Pattern Recognition Statistics:")
    print("=" * 80)

    stats = system.get_statistics()
    print(f"Total Patterns: {stats['total_patterns']}")
    print(f"Total Runs: {stats['total_runs']}")
    print(f"Success Rate: {stats['success_rate']:.1%}")
    print(f"Avg Duration: {stats['avg_orchestration_duration']:.1f}s")

    print("\n📈 Pattern Distribution:")
    for pattern_type, count in stats['pattern_counts'].items():
        print(f"  {pattern_type}: {count}")

    print("\n⚠️  Severity Distribution:")
    for severity, count in stats['severity_counts'].items():
        print(f"  {severity}: {count}")

    # Most common patterns
    print("\n🔥 Most Common Patterns:")
    print("=" * 80)

    for i, pattern in enumerate(system.get_most_common_patterns(limit=5), 1):
        print(f"\n{i}. {pattern.name}")
        print(f"   Type: {pattern.pattern_type.value}")
        print(f"   Severity: {pattern.severity.value}")
        print(f"   Occurrences: {pattern.occurrences}")
        print(f"   Files: {', '.join(pattern.files_affected[:3])}")
        if pattern.agents_involved:
            print(f"   Agents: {', '.join(pattern.agents_involved[:3])}")

    # Agent performance
    print("\n🏆 Best Performing Agents:")
    print("=" * 80)

    for i, (agent, success_rate) in enumerate(system.get_best_performing_agents(), 1):
        perf = system.get_agent_performance(agent)
        print(f"\n{i}. {agent}")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Total Runs: {perf['total_runs']}")
        print(f"   Avg Duration: {perf['avg_duration']:.1f}s")

    # Recommendations
    print("\n💡 Agent Sequence Recommendation for 'tests/safe_test.cpp':")
    print("=" * 80)

    recommended_agents = system.recommend_agent_sequence("tests/safe_test.cpp")
    for i, agent in enumerate(recommended_agents, 1):
        print(f"{i}. {agent}")

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()