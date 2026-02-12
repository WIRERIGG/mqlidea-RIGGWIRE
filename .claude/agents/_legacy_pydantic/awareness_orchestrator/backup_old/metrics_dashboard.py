"""
Metrics Dashboard
Real-time metrics display and historical trend analysis for orchestration performance
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

from pattern_recognition import PatternRecognitionSystem, OrchestrationRun
from proactive_suggestions import ProactiveSuggestionsEngine, Priority as SuggestionPriority


class MetricType(str, Enum):
    """Types of metrics tracked."""
    SUCCESS_RATE = "success_rate"
    DURATION = "duration"
    ERROR_COUNT = "error_count"
    WARNING_COUNT = "warning_count"
    FIXES_APPLIED = "fixes_applied"
    TESTS_PASSED = "tests_passed"
    BUILD_SUCCESS = "build_success"
    AGENT_EFFICIENCY = "agent_efficiency"


class TrendDirection(str, Enum):
    """Trend direction indicators."""
    IMPROVING = "improving"
    DECLINING = "declining"
    STABLE = "stable"


@dataclass
class Metric:
    """Individual metric data point."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_type: MetricType
    direction: TrendDirection
    change_percentage: float
    current_value: float
    previous_value: float
    period_days: int
    confidence: float  # 0.0 to 1.0


@dataclass
class AgentMetrics:
    """Metrics for a specific agent."""
    agent_name: str
    total_runs: int
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration: float
    issues_found: int
    issues_fixed: int
    fix_rate: float
    last_run: Optional[datetime] = None


class MetricsDashboard:
    """
    Real-time metrics dashboard for orchestration performance tracking.

    Features:
    - Real-time metric calculation
    - Historical trend analysis
    - Agent performance comparison
    - Success rate tracking
    - Efficiency metrics
    - Visual dashboard generation
    """

    def __init__(
        self,
        pattern_system: Optional[PatternRecognitionSystem] = None,
        suggestions_engine: Optional[ProactiveSuggestionsEngine] = None
    ):
        """
        Initialize metrics dashboard.

        Args:
            pattern_system: Optional PatternRecognitionSystem for historical data
            suggestions_engine: Optional ProactiveSuggestionsEngine for proactive metrics
        """
        self.pattern_system = pattern_system or PatternRecognitionSystem()
        self.suggestions_engine = suggestions_engine or ProactiveSuggestionsEngine(self.pattern_system)

        # Real-time metrics
        self.current_metrics: Dict[str, Metric] = {}

        # Historical data
        self.metric_history: Dict[MetricType, List[Tuple[datetime, float]]] = defaultdict(list)

        # Refresh metrics from pattern system
        self._refresh_metrics()

    def _refresh_metrics(self):
        """Refresh all metrics from historical data."""
        if not self.pattern_system.orchestration_runs:
            return

        # Calculate success rate
        total_runs = len(self.pattern_system.orchestration_runs)
        successful_runs = sum(1 for r in self.pattern_system.orchestration_runs if r.success)
        success_rate = (successful_runs / total_runs) if total_runs > 0 else 0.0

        self.current_metrics["success_rate"] = Metric(
            name="Overall Success Rate",
            value=success_rate,
            unit="%",
            timestamp=datetime.now()
        )

        # Average duration
        avg_duration = sum(r.duration for r in self.pattern_system.orchestration_runs) / total_runs

        self.current_metrics["avg_duration"] = Metric(
            name="Average Duration",
            value=avg_duration,
            unit="seconds",
            timestamp=datetime.now()
        )

        # Total errors
        total_errors = sum(len(r.errors) for r in self.pattern_system.orchestration_runs)

        self.current_metrics["total_errors"] = Metric(
            name="Total Errors",
            value=total_errors,
            unit="count",
            timestamp=datetime.now()
        )

        # Total warnings
        total_warnings = sum(len(r.warnings) for r in self.pattern_system.orchestration_runs)

        self.current_metrics["total_warnings"] = Metric(
            name="Total Warnings",
            value=total_warnings,
            unit="count",
            timestamp=datetime.now()
        )

        # Total fixes
        total_fixes = sum(r.fixes_applied for r in self.pattern_system.orchestration_runs)

        self.current_metrics["total_fixes"] = Metric(
            name="Total Fixes Applied",
            value=total_fixes,
            unit="count",
            timestamp=datetime.now()
        )

        # Build success rate
        build_success_count = sum(1 for r in self.pattern_system.orchestration_runs if r.build_success)
        build_success_rate = (build_success_count / total_runs) if total_runs > 0 else 0.0

        self.current_metrics["build_success_rate"] = Metric(
            name="Build Success Rate",
            value=build_success_rate,
            unit="%",
            timestamp=datetime.now()
        )

        # Test pass rate
        test_pass_count = sum(1 for r in self.pattern_system.orchestration_runs if r.tests_passed)
        test_pass_rate = (test_pass_count / total_runs) if total_runs > 0 else 0.0

        self.current_metrics["test_pass_rate"] = Metric(
            name="Test Pass Rate",
            value=test_pass_rate,
            unit="%",
            timestamp=datetime.now()
        )

    def get_metric(self, metric_name: str) -> Optional[Metric]:
        """Get current value of specific metric."""
        return self.current_metrics.get(metric_name)

    def calculate_trend(
        self,
        metric_type: MetricType,
        period_days: int = 7
    ) -> Optional[TrendAnalysis]:
        """
        Calculate trend for specific metric over time period.

        Args:
            metric_type: Type of metric to analyze
            period_days: Number of days to analyze

        Returns:
            TrendAnalysis or None if insufficient data
        """
        if not self.pattern_system.orchestration_runs:
            return None

        cutoff_date = datetime.now() - timedelta(days=period_days)

        # Get recent and older runs
        recent_runs = [
            r for r in self.pattern_system.orchestration_runs
            if r.timestamp >= cutoff_date
        ]

        older_runs = [
            r for r in self.pattern_system.orchestration_runs
            if r.timestamp < cutoff_date
        ]

        if not recent_runs or not older_runs:
            return None

        # Calculate metric values
        current_value = self._calculate_metric_value(metric_type, recent_runs)
        previous_value = self._calculate_metric_value(metric_type, older_runs)

        if previous_value == 0:
            return None

        # Calculate change
        change_percentage = ((current_value - previous_value) / previous_value) * 100

        # Determine direction
        if abs(change_percentage) < 5:  # Within 5% = stable
            direction = TrendDirection.STABLE
        elif change_percentage > 0:
            # For success rates, positive is improving
            # For error counts, positive is declining
            if metric_type in [MetricType.SUCCESS_RATE, MetricType.BUILD_SUCCESS, MetricType.TESTS_PASSED]:
                direction = TrendDirection.IMPROVING
            else:
                direction = TrendDirection.DECLINING
        else:
            if metric_type in [MetricType.SUCCESS_RATE, MetricType.BUILD_SUCCESS, MetricType.TESTS_PASSED]:
                direction = TrendDirection.DECLINING
            else:
                direction = TrendDirection.IMPROVING

        # Calculate confidence based on sample size
        confidence = min(1.0, len(recent_runs) / 20.0)  # Max confidence at 20+ runs

        return TrendAnalysis(
            metric_type=metric_type,
            direction=direction,
            change_percentage=change_percentage,
            current_value=current_value,
            previous_value=previous_value,
            period_days=period_days,
            confidence=confidence
        )

    def _calculate_metric_value(self, metric_type: MetricType, runs: List[OrchestrationRun]) -> float:
        """Calculate metric value for list of runs."""
        if not runs:
            return 0.0

        if metric_type == MetricType.SUCCESS_RATE:
            return sum(1 for r in runs if r.success) / len(runs)

        elif metric_type == MetricType.DURATION:
            return sum(r.duration for r in runs) / len(runs)

        elif metric_type == MetricType.ERROR_COUNT:
            return sum(len(r.errors) for r in runs) / len(runs)

        elif metric_type == MetricType.WARNING_COUNT:
            return sum(len(r.warnings) for r in runs) / len(runs)

        elif metric_type == MetricType.FIXES_APPLIED:
            return sum(r.fixes_applied for r in runs) / len(runs)

        elif metric_type == MetricType.TESTS_PASSED:
            return sum(1 for r in runs if r.tests_passed) / len(runs)

        elif metric_type == MetricType.BUILD_SUCCESS:
            return sum(1 for r in runs if r.build_success) / len(runs)

        return 0.0

    def get_agent_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        """Get comprehensive metrics for specific agent."""
        perf = self.pattern_system.agent_performance.get(agent_name)

        if not perf or perf["total_runs"] == 0:
            return None

        success_rate = perf["success_count"] / perf["total_runs"]
        fix_rate = (perf["issues_fixed"] / perf["issues_found"]) if perf["issues_found"] > 0 else 0.0

        # Find last run with this agent
        last_run = None
        for run in reversed(self.pattern_system.orchestration_runs):
            if agent_name in run.agents_executed:
                last_run = run.timestamp
                break

        return AgentMetrics(
            agent_name=agent_name,
            total_runs=perf["total_runs"],
            success_count=perf["success_count"],
            failure_count=perf["failure_count"],
            success_rate=success_rate,
            avg_duration=perf["avg_duration"],
            issues_found=perf["issues_found"],
            issues_fixed=perf["issues_fixed"],
            fix_rate=fix_rate,
            last_run=last_run
        )

    def get_all_agent_metrics(self) -> List[AgentMetrics]:
        """Get metrics for all agents."""
        metrics = []

        for agent_name in self.pattern_system.agent_performance.keys():
            agent_metrics = self.get_agent_metrics(agent_name)
            if agent_metrics:
                metrics.append(agent_metrics)

        return sorted(metrics, key=lambda m: m.success_rate, reverse=True)

    def compare_agents(self, agent1: str, agent2: str) -> Dict[str, Any]:
        """
        Compare performance of two agents.

        Returns:
            Dictionary with comparison results
        """
        metrics1 = self.get_agent_metrics(agent1)
        metrics2 = self.get_agent_metrics(agent2)

        if not metrics1 or not metrics2:
            return {"error": "One or both agents not found"}

        return {
            "agent1": agent1,
            "agent2": agent2,
            "success_rate_diff": metrics1.success_rate - metrics2.success_rate,
            "duration_diff": metrics1.avg_duration - metrics2.avg_duration,
            "fix_rate_diff": metrics1.fix_rate - metrics2.fix_rate,
            "better_success_rate": agent1 if metrics1.success_rate > metrics2.success_rate else agent2,
            "faster": agent1 if metrics1.avg_duration < metrics2.avg_duration else agent2,
            "better_fix_rate": agent1 if metrics1.fix_rate > metrics2.fix_rate else agent2
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive dashboard summary."""
        stats = self.pattern_system.get_statistics()

        # Trend analysis
        trends = {}
        for metric_type in [
            MetricType.SUCCESS_RATE,
            MetricType.DURATION,
            MetricType.ERROR_COUNT
        ]:
            trend = self.calculate_trend(metric_type, period_days=7)
            if trend:
                trends[metric_type.value] = {
                    "direction": trend.direction.value,
                    "change": f"{trend.change_percentage:+.1f}%",
                    "current": trend.current_value,
                    "previous": trend.previous_value
                }

        # Top performers
        all_agents = self.get_all_agent_metrics()
        top_performers = all_agents[:5] if all_agents else []

        # Proactive suggestions summary
        suggestion_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }

        if hasattr(self.suggestions_engine, 'suggestions'):
            for suggestion in self.suggestions_engine.suggestions:
                priority_key = suggestion.priority.value
                if priority_key in suggestion_counts:
                    suggestion_counts[priority_key] += 1

        return {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "total_runs": stats["total_runs"],
                "success_rate": f"{stats['success_rate']:.1%}",
                "avg_duration": f"{stats['avg_orchestration_duration']:.1f}s",
                "total_patterns": stats["total_patterns"]
            },
            "trends": trends,
            "top_performers": [
                {
                    "agent": agent.agent_name,
                    "success_rate": f"{agent.success_rate:.1%}",
                    "runs": agent.total_runs
                }
                for agent in top_performers
            ],
            "suggestions": suggestion_counts,
            "health_indicators": self._calculate_health_indicators()
        }

    def _calculate_health_indicators(self) -> Dict[str, str]:
        """Calculate overall health indicators."""
        stats = self.pattern_system.get_statistics()

        indicators = {}

        # Success rate health
        if stats["success_rate"] >= 0.9:
            indicators["success_rate"] = "🟢 Excellent"
        elif stats["success_rate"] >= 0.7:
            indicators["success_rate"] = "🟡 Good"
        elif stats["success_rate"] >= 0.5:
            indicators["success_rate"] = "🟠 Needs Attention"
        else:
            indicators["success_rate"] = "🔴 Critical"

        # Duration health
        avg_duration = stats["avg_orchestration_duration"]
        if avg_duration < 30:
            indicators["performance"] = "🟢 Fast"
        elif avg_duration < 60:
            indicators["performance"] = "🟡 Acceptable"
        elif avg_duration < 120:
            indicators["performance"] = "🟠 Slow"
        else:
            indicators["performance"] = "🔴 Very Slow"

        # Pattern health (fewer patterns is better)
        if stats["total_patterns"] < 5:
            indicators["code_quality"] = "🟢 Stable"
        elif stats["total_patterns"] < 15:
            indicators["code_quality"] = "🟡 Moderate"
        elif stats["total_patterns"] < 30:
            indicators["code_quality"] = "🟠 Many Issues"
        else:
            indicators["code_quality"] = "🔴 High Complexity"

        return indicators

    def generate_dashboard(self) -> str:
        """Generate visual dashboard display."""
        summary = self.get_dashboard_summary()

        lines = ["=" * 80, "🎯 ORCHESTRATION METRICS DASHBOARD", "=" * 80, ""]

        # Timestamp
        lines.append(f"📅 Generated: {summary['timestamp']}")
        lines.append("")

        # Overview
        lines.append("📊 OVERVIEW")
        lines.append("=" * 80)
        for key, value in summary["overview"].items():
            lines.append(f"  {key.replace('_', ' ').title()}: {value}")
        lines.append("")

        # Health Indicators
        lines.append("🏥 HEALTH INDICATORS")
        lines.append("=" * 80)
        for indicator, status in summary["health_indicators"].items():
            lines.append(f"  {indicator.replace('_', ' ').title()}: {status}")
        lines.append("")

        # Trends
        if summary["trends"]:
            lines.append("📈 TRENDS (Last 7 Days)")
            lines.append("=" * 80)
            for metric, trend_data in summary["trends"].items():
                direction_emoji = {
                    "improving": "📈",
                    "declining": "📉",
                    "stable": "➡️"
                }.get(trend_data["direction"], "")

                lines.append(f"  {metric.replace('_', ' ').title()}")
                lines.append(f"    {direction_emoji} {trend_data['direction'].title()} ({trend_data['change']})")
                lines.append(f"    Current: {trend_data['current']:.2f} | Previous: {trend_data['previous']:.2f}")
            lines.append("")

        # Top Performers
        if summary["top_performers"]:
            lines.append("🏆 TOP PERFORMING AGENTS")
            lines.append("=" * 80)
            for i, agent in enumerate(summary["top_performers"], 1):
                lines.append(f"  {i}. {agent['agent']}")
                lines.append(f"     Success Rate: {agent['success_rate']} ({agent['runs']} runs)")
            lines.append("")

        # Proactive Suggestions
        lines.append("💡 PROACTIVE SUGGESTIONS")
        lines.append("=" * 80)
        total_suggestions = sum(summary["suggestions"].values())
        lines.append(f"  Total: {total_suggestions}")

        if total_suggestions > 0:
            for priority, count in summary["suggestions"].items():
                if count > 0:
                    emoji = {
                        "critical": "🚨",
                        "high": "⚠️",
                        "medium": "🔵",
                        "low": "ℹ️"
                    }.get(priority, "")
                    lines.append(f"    {emoji} {priority.title()}: {count}")
        lines.append("")

        # Current Metrics
        lines.append("📊 CURRENT METRICS")
        lines.append("=" * 80)
        for metric_name, metric in sorted(self.current_metrics.items()):
            lines.append(f"  {metric.name}: {metric.value:.2f} {metric.unit}")
        lines.append("")

        # Agent Comparison
        all_agents = self.get_all_agent_metrics()
        if len(all_agents) >= 2:
            lines.append("⚖️  AGENT PERFORMANCE COMPARISON")
            lines.append("=" * 80)

            # Create comparison table header
            lines.append(f"  {'Agent':<35} {'Success Rate':<15} {'Avg Duration':<15} {'Runs':<10}")
            lines.append("  " + "-" * 75)

            for agent in all_agents:
                lines.append(
                    f"  {agent.agent_name:<35} "
                    f"{agent.success_rate:>13.1%}  "
                    f"{agent.avg_duration:>13.1f}s  "
                    f"{agent.total_runs:>8}"
                )
            lines.append("")

        lines.append("=" * 80)
        lines.append("Dashboard Complete")
        lines.append("=" * 80)

        return "\n".join(lines)

    def export_metrics(self, output_path: Path):
        """Export metrics to JSON file."""
        summary = self.get_dashboard_summary()

        # Add detailed agent metrics
        summary["agents"] = [
            {
                "name": agent.agent_name,
                "success_rate": agent.success_rate,
                "avg_duration": agent.avg_duration,
                "total_runs": agent.total_runs,
                "issues_found": agent.issues_found,
                "issues_fixed": agent.issues_fixed,
                "fix_rate": agent.fix_rate
            }
            for agent in self.get_all_agent_metrics()
        ]

        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)


def main():
    """Test metrics dashboard."""
    print("=" * 80)
    print("Metrics Dashboard - Test")
    print("=" * 80)

    # Initialize with pattern system
    pattern_system = PatternRecognitionSystem()

    # Add some test data if empty
    if not pattern_system.orchestration_runs:
        print("\n📝 Creating test data...")

        # Simulate several orchestration runs
        for i in range(15):
            success = i % 3 != 0  # 66% success rate

            run = OrchestrationRun(
                run_id=f"test-{i:03d}",
                timestamp=datetime.now() - timedelta(days=14 - i),
                target_file=f"tests/test_file_{i % 3}.cpp",
                agents_executed=["clang-tidy-analyzer", "clang-tidy-critical-fixer"]
                if i % 2 == 0
                else ["multi-agent-debugging-system"],
                duration=30.0 + (i * 2.5),
                success=success,
                errors=[{"message": f"Error {i}"}] if not success else [],
                warnings=[{"message": f"Warning {i}"}] if i % 2 == 0 else [],
                fixes_applied=i % 5,
                tests_passed=success,
                build_success=success
            )

            pattern_system.record_orchestration_run(run)

        print(f"✅ Created {len(pattern_system.orchestration_runs)} test runs")

    # Initialize dashboard
    dashboard = MetricsDashboard(pattern_system)

    print("\n" + "=" * 80)
    print("Generating Dashboard...")
    print("=" * 80)

    # Generate and display dashboard
    dashboard_output = dashboard.generate_dashboard()
    print("\n" + dashboard_output)

    # Export metrics
    export_path = Path("dashboard_metrics.json")
    dashboard.export_metrics(export_path)
    print(f"\n✅ Metrics exported to: {export_path}")

    # Test trend analysis
    print("\n" + "=" * 80)
    print("Detailed Trend Analysis")
    print("=" * 80)

    for metric_type in [MetricType.SUCCESS_RATE, MetricType.DURATION, MetricType.ERROR_COUNT]:
        trend = dashboard.calculate_trend(metric_type, period_days=7)
        if trend:
            print(f"\n{metric_type.value.replace('_', ' ').title()}:")
            print(f"  Direction: {trend.direction.value}")
            print(f"  Change: {trend.change_percentage:+.1f}%")
            print(f"  Current: {trend.current_value:.2f}")
            print(f"  Previous: {trend.previous_value:.2f}")
            print(f"  Confidence: {trend.confidence:.0%}")

    # Clean up
    if export_path.exists():
        export_path.unlink()

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()