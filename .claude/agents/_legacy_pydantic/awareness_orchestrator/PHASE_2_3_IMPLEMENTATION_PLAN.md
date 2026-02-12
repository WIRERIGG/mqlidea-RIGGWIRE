# Phase 2 & 3 Implementation Plan

**Date**: 2025-09-29
**Status**: Ready for Implementation
**Based on**: Phase 1 validation success (all tests passed)

---

## 🎯 Overview

This document outlines the implementation plan for **Phase 2 (Intelligence Layer)** and **Phase 3 (Learning System)** enhancements to the Awareness Orchestrator, building on the successful Phase 1 implementation.

---

## Phase 2: Intelligence Layer (10-12 hours)

### Enhancement 1: Build System Integration (4-6 hours)

**Objective**: Direct CMake command execution and comprehensive output parsing

**Implementation**:

```python
class BuildSystemAdapter:
    """Advanced build system integration with CLion compatibility."""

    def __init__(self, project_root: Path, build_dir: Path):
        self.project_root = project_root
        self.build_dir = build_dir
        self.cmake_path = self._find_cmake()

    def _find_cmake(self) -> str:
        """Find CMake binary (CLion or system)."""
        candidates = [
            # CLion's CMake (highest priority)
            str(Path.home() / ".jbdevcontainer/JetBrains/RemoteDev/dist/*/bin/cmake/linux/x64/bin/cmake"),
            # System cmake
            "/usr/bin/cmake",
            "cmake"
        ]

        for candidate in candidates:
            if "*" in candidate:
                import glob
                matches = glob.glob(candidate)
                if matches:
                    return matches[0]
            else:
                from shutil import which
                if which(candidate):
                    return candidate

        return "cmake"  # Fallback

    async def build_target(self, target: str = "wire_ground_tests") -> BuildResult:
        """Build specific target with parallel compilation."""
        cmd = [
            self.cmake_path,
            "--build",
            str(self.build_dir),
            "--target",
            target,
            "--",
            "-j", str(os.cpu_count() or 4)  # Parallel build
        ]

        result = await self._run_command(cmd)

        return BuildResult(
            success=result.returncode == 0 and f"Built target {target}" in result.stdout,
            duration=result.duration,
            warnings=self._parse_warnings(result.stdout + result.stderr),
            errors=self._parse_errors(result.stdout + result.stderr),
            stdout=result.stdout,
            stderr=result.stderr
        )

    async def run_tests(
        self,
        filter: Optional[str] = None,
        test_binary: str = "wire_ground_tests"
    ) -> TestResult:
        """Run GoogleTest suite with optional filtering."""
        test_path = self.build_dir / "tests" / test_binary

        cmd = [str(test_path)]
        if filter:
            cmd.append(f"--gtest_filter={filter}")

        cmd.extend([
            "--gtest_color=yes",
            "--gtest_print_time=1"
        ])

        result = await self._run_command(cmd)

        # Parse GoogleTest output
        total, passed, failed, failed_names = self._parse_gtest_output(result.stdout)

        return TestResult(
            success=result.returncode == 0,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            duration=result.duration,
            failed_test_names=failed_names,
            stdout=result.stdout,
            stderr=result.stderr
        )

    def _parse_warnings(self, output: str) -> List[str]:
        """Parse compiler warnings with improved detection."""
        warnings = []
        for line in output.split('\n'):
            # GCC/Clang warning patterns
            if re.search(r'warning:|⚠️', line, re.IGNORECASE):
                warnings.append(line.strip())
            # CMake warnings
            elif re.search(r'CMake Warning', line):
                warnings.append(line.strip())
        return warnings

    def _parse_errors(self, output: str) -> List[str]:
        """Parse compiler errors with improved detection."""
        errors = []
        for line in output.split('\n'):
            # Error patterns
            if re.search(r'error:|❌|fatal error:', line, re.IGNORECASE):
                if 'warning' not in line.lower():
                    errors.append(line.strip())
            # CMake errors
            elif re.search(r'CMake Error', line):
                errors.append(line.strip())
        return errors

    def _parse_gtest_output(self, output: str) -> tuple[int, int, int, List[str]]:
        """Parse GoogleTest output for test results."""
        total = 0
        passed = 0
        failed = 0
        failed_names = []

        # Look for test summary
        for line in output.split('\n'):
            # [==========] Running 99 tests from 1 test suite.
            if match := re.search(r'\[==========\] Running (\d+) tests', line):
                total = int(match.group(1))

            # [  PASSED  ] 99 tests.
            elif match := re.search(r'\[  PASSED  \] (\d+) tests', line):
                passed = int(match.group(1))

            # [  FAILED  ] TestSuite.TestName
            elif match := re.search(r'\[  FAILED  \]\s+(\S+)', line):
                failed_names.append(match.group(1))

        failed = len(failed_names)
        if total == 0:
            total = passed + failed

        return total, passed, failed, failed_names
```

**Integration with Validation Pipeline**:
- Replace placeholder `_run_build()` with `BuildSystemAdapter.build_target()`
- Replace placeholder `_run_tests()` with `BuildSystemAdapter.run_tests()`
- Add real-time progress callbacks

---

### Enhancement 2: Context-Rich Prompting (1-2 hours)

**Objective**: Template system for generating context-rich agent prompts

**Implementation**:

```python
class PromptTemplate:
    """Template system for context-rich agent prompts."""

    TEMPLATES = {
        "analysis": """
# Task: {task_description}

## Target: {target}

{context_section}

## Your Role
As the **{agent_name}** agent, your role is to:
{agent_role}

## Analysis Focus
{focus_areas}

## Directives
1. Build on previous findings - don't duplicate analysis
2. Cross-reference your findings with previous issues
3. Validate any critical issues at the specific locations mentioned
4. Focus analysis on high-priority areas if they relate to your domain
5. Report if you find issues were already fixed
6. Provide actionable recommendations with specific locations

## Expected Output Format
Provide structured findings with:
- **Severity**: critical/high/medium/low/info
- **Category**: bug/performance/security/quality/documentation
- **Location**: File:line reference
- **Description**: Clear problem statement
- **Recommendation**: Specific fix suggestion
""",

        "fixing": """
# Task: {task_description}

## Target: {target}

{context_section}

## Your Role
As the **{agent_name}** agent, your role is to:
{agent_role}

## Fixes Required
{fixes_required}

## Safety Guidelines
1. Apply fixes incrementally (3-5 changes at a time)
2. Preserve existing functionality
3. Maintain code style consistency
4. Add comments for complex changes
5. Test after each batch of fixes

## Expected Output
For each fix applied:
- File modified
- Lines changed
- Change description
- Reason for change
- Test validation needed
""",

        "validation": """
# Task: {task_description}

## Target: {target}

{context_section}

## Your Role
As the **{agent_name}** agent, your role is to:
{agent_role}

## Validation Checklist
{validation_checklist}

## Success Criteria
- All builds pass (zero errors)
- All tests pass (100% pass rate)
- No new warnings introduced
- Performance not regressed
- Memory safety maintained

## Expected Output
Validation report with:
- Build status (pass/fail)
- Test results (passed/failed/total)
- Performance metrics
- Safety verification
- Issues found (if any)
"""
    }

    @classmethod
    def generate(
        cls,
        template_type: str,
        agent_name: str,
        task_description: str,
        target: str,
        context: Dict[str, Any],
        **kwargs
    ) -> str:
        """Generate context-rich prompt from template."""
        template = cls.TEMPLATES.get(template_type, cls.TEMPLATES["analysis"])

        # Build context section
        context_section = cls._build_context_section(context)

        # Get agent-specific role
        agent_role = cls._get_agent_role(agent_name)

        # Build focus areas
        focus_areas = cls._build_focus_areas(context, kwargs.get("focus_areas"))

        # Build specific sections based on template type
        specific_sections = {}
        if template_type == "fixing":
            specific_sections["fixes_required"] = cls._build_fixes_section(context)
        elif template_type == "validation":
            specific_sections["validation_checklist"] = cls._build_validation_checklist(context)

        return template.format(
            task_description=task_description,
            target=target,
            agent_name=agent_name,
            context_section=context_section,
            agent_role=agent_role,
            focus_areas=focus_areas,
            **specific_sections,
            **kwargs
        )

    @classmethod
    def _build_context_section(cls, context: Dict[str, Any]) -> str:
        """Build context section from previous agent findings."""
        if not context.get("previous_findings_summary"):
            return "## Context\nThis is the first agent in the workflow."

        parts = ["## Context from Previous Agents"]
        parts.append("")

        summary = context["previous_findings_summary"]
        parts.append(f"**Total agents executed**: {context.get('total_agents_executed', 0)}")
        parts.append(f"**Total findings**: {summary.get('total', 0)}")
        parts.append("")

        # Critical issues
        if context.get("critical_issues"):
            parts.append("### Critical Issues Identified:")
            for issue in context["critical_issues"][:5]:  # Top 5
                parts.append(f"- **{issue['title']}** ({issue['location']})")
                parts.append(f"  {issue['description']}")
            parts.append("")

        # High priority areas
        if context.get("high_priority_areas"):
            parts.append("### High-Priority Code Areas:")
            for area in context["high_priority_areas"][:10]:
                parts.append(f"- {area}")
            parts.append("")

        return "\n".join(parts)

    @classmethod
    def _get_agent_role(cls, agent_name: str) -> str:
        """Get role description for specific agent."""
        roles = {
            "multi-agent-debugging-system": "Comprehensive debugging and issue discovery across all code quality dimensions",
            "clang-tidy-analyzer": "Static code analysis for C++ quality, safety, and best practices",
            "valgrind-safety-analyzer": "Runtime memory safety and threading analysis",
            "blitzfire-cpp-optimizer": "Performance optimization and SIMD/cache optimization",
            "passive-code-analyzer": "Continuous background analysis with automatic fixing",
            "zero-warnings-enforcer": "Eliminate and prevent compiler warnings",
            "clang-tidy-fixer": "Apply intelligent fixes for clang-tidy findings"
        }
        return roles.get(agent_name, "Specialized analysis and improvement")

    @classmethod
    def _build_focus_areas(cls, context: Dict[str, Any], explicit_areas: Optional[List[str]]) -> str:
        """Build focus areas section."""
        areas = explicit_areas or context.get("high_priority_areas", [])

        if not areas:
            return "Focus on comprehensive analysis of the entire target."

        parts = ["Priority focus areas based on previous findings:"]
        for area in areas[:10]:
            parts.append(f"- {area}")

        return "\n".join(parts)
```

---

### Enhancement 3: Progress Reporting (1-2 hours)

**Objective**: Real-time streaming progress updates

**Implementation**:

```python
class ProgressReporter:
    """Real-time progress reporting system."""

    def __init__(self):
        self.listeners: List[Callable] = []
        self.current_task: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.milestones: List[Dict[str, Any]] = []

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """Add progress listener callback."""
        self.listeners.append(listener)

    def start_task(self, task_id: str, description: str):
        """Start new task reporting."""
        self.current_task = task_id
        self.start_time = datetime.now()
        self.milestones = []

        self._emit({
            "type": "task_start",
            "task_id": task_id,
            "description": description,
            "timestamp": self.start_time.isoformat()
        })

    def update_progress(
        self,
        stage: str,
        progress: float,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update task progress."""
        update = {
            "type": "progress_update",
            "task_id": self.current_task,
            "stage": stage,
            "progress": progress,  # 0.0 to 1.0
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self._emit(update)

    def milestone(self, name: str, data: Dict[str, Any]):
        """Record milestone achievement."""
        milestone = {
            "name": name,
            "timestamp": datetime.now(),
            "data": data
        }

        self.milestones.append(milestone)

        self._emit({
            "type": "milestone",
            "task_id": self.current_task,
            "milestone": milestone
        })

    def complete_task(self, success: bool, result: Any):
        """Complete task reporting."""
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        self._emit({
            "type": "task_complete",
            "task_id": self.current_task,
            "success": success,
            "duration": duration,
            "milestones_count": len(self.milestones),
            "timestamp": datetime.now().isoformat()
        })

        self.current_task = None
        self.start_time = None

    def _emit(self, event: Dict[str, Any]):
        """Emit event to all listeners."""
        for listener in self.listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Progress listener error: {e}")

    @staticmethod
    def console_listener(event: Dict[str, Any]):
        """Default console progress listener."""
        event_type = event["type"]

        if event_type == "task_start":
            print(f"\n🚀 Starting: {event['description']}")
            print(f"   Task ID: {event['task_id']}")

        elif event_type == "progress_update":
            progress_pct = event['progress'] * 100
            print(f"📊 [{event['stage']}] {progress_pct:.0f}% - {event['message']}")

        elif event_type == "milestone":
            milestone = event['milestone']
            print(f"✅ Milestone: {milestone['name']}")

        elif event_type == "task_complete":
            status = "✅ COMPLETE" if event['success'] else "❌ FAILED"
            print(f"\n{status} - Duration: {event['duration']:.1f}s")
            print(f"   Milestones: {event['milestones_count']}")
```

---

## Phase 3: Learning System (8-10 hours)

### Enhancement 1: Advanced Pattern Recognition (4-5 hours)

**Objective**: Automatic pattern extraction from execution history

**Implementation**:

```python
class PatternRecognizer:
    """Advanced pattern recognition from execution history."""

    def __init__(self, learning_db: Dict[str, Any]):
        self.learning_db = learning_db
        self.patterns_cache: Optional[List[Pattern]] = None

    def extract_patterns(self) -> List[Pattern]:
        """Extract patterns from successful and failed executions."""
        patterns = []

        # Analyze successful patterns
        for success_pattern in self.learning_db["successful_patterns"]:
            patterns.extend(self._extract_from_success(success_pattern))

        # Analyze failed patterns
        for failed_pattern in self.learning_db["failed_patterns"]:
            patterns.extend(self._extract_from_failure(failed_pattern))

        # Deduplicate and rank patterns
        patterns = self._deduplicate_patterns(patterns)
        patterns = self._rank_patterns(patterns)

        self.patterns_cache = patterns
        return patterns

    def _extract_from_success(self, success_data: Dict[str, Any]) -> List[Pattern]:
        """Extract patterns from successful execution."""
        patterns = []

        agent = success_data.get("agent")
        changes_count = success_data.get("changes_count", 0)
        metrics = success_data.get("metrics", {})

        # Pattern: Fast successful changes
        if metrics.get("build_time", 999) < 30 and changes_count <= 5:
            patterns.append(Pattern(
                type="incremental_success",
                description=f"{agent} succeeds with small incremental changes (≤5 changes)",
                confidence=0.9,
                agent=agent,
                conditions={"max_changes": 5, "max_build_time": 30},
                recommendation="Apply changes incrementally in batches of 3-5"
            ))

        # Pattern: Agent efficiency
        if "execution_time" in metrics and "findings" in metrics:
            findings_per_second = metrics["findings"] / metrics["execution_time"]
            if findings_per_second > 1.0:
                patterns.append(Pattern(
                    type="efficient_agent",
                    description=f"{agent} is highly efficient ({findings_per_second:.1f} findings/sec)",
                    confidence=0.85,
                    agent=agent,
                    conditions={"min_findings_per_sec": findings_per_second},
                    recommendation=f"Prioritize {agent} for similar tasks"
                ))

        return patterns

    def _extract_from_failure(self, failure_data: Dict[str, Any]) -> List[Pattern]:
        """Extract patterns from failed execution."""
        patterns = []

        agent = failure_data.get("agent")
        reason = failure_data.get("failure_reason", "")
        changes_count = failure_data.get("changes_count", 0)

        # Pattern: Build failures with many changes
        if "Build failed" in reason and changes_count > 10:
            patterns.append(Pattern(
                type="bulk_change_risk",
                description=f"{agent} build fails with bulk changes (>{changes_count} changes)",
                confidence=0.8,
                agent=agent,
                conditions={"max_safe_changes": 10},
                recommendation="Avoid bulk changes, apply incrementally"
            ))

        # Pattern: Specific failure reasons
        if "error:" in reason.lower():
            # Extract error type
            error_type = self._extract_error_type(reason)
            patterns.append(Pattern(
                type="known_failure",
                description=f"{agent} encounters {error_type}",
                confidence=0.75,
                agent=agent,
                conditions={"error_pattern": error_type},
                recommendation=f"Check for {error_type} before applying changes"
            ))

        return patterns

    def _extract_error_type(self, reason: str) -> str:
        """Extract error type from failure reason."""
        error_patterns = {
            "cannot resolve symbol": "symbol_resolution",
            "undefined reference": "linking_error",
            "no matching function": "overload_resolution",
            "error: expected": "syntax_error",
            "warning as error": "warning_escalation"
        }

        reason_lower = reason.lower()
        for pattern, error_type in error_patterns.items():
            if pattern in reason_lower:
                return error_type

        return "unknown_error"

    def _deduplicate_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """Remove duplicate patterns."""
        seen = {}
        unique = []

        for pattern in patterns:
            key = f"{pattern.type}:{pattern.agent}:{pattern.description}"
            if key not in seen:
                seen[key] = pattern
                unique.append(pattern)
            else:
                # Update confidence if higher
                if pattern.confidence > seen[key].confidence:
                    seen[key].confidence = pattern.confidence

        return unique

    def _rank_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """Rank patterns by confidence and frequency."""
        # Sort by confidence descending
        patterns.sort(key=lambda p: p.confidence, reverse=True)
        return patterns

    def match_patterns(
        self,
        agent: str,
        context: Dict[str, Any]
    ) -> List[Pattern]:
        """Match applicable patterns for current context."""
        if not self.patterns_cache:
            self.extract_patterns()

        matched = []
        for pattern in self.patterns_cache:
            if pattern.agent == agent or pattern.agent == "any":
                if self._pattern_applies(pattern, context):
                    matched.append(pattern)

        return matched

    def _pattern_applies(self, pattern: Pattern, context: Dict[str, Any]) -> bool:
        """Check if pattern applies to current context."""
        conditions = pattern.conditions

        # Check conditions
        for key, value in conditions.items():
            if key.startswith("max_"):
                context_value = context.get(key.replace("max_", ""), float('inf'))
                if context_value > value:
                    return False
            elif key.startswith("min_"):
                context_value = context.get(key.replace("min_", ""), 0)
                if context_value < value:
                    return False

        return True

@dataclass
class Pattern:
    """Learned pattern from execution history."""
    type: str
    description: str
    confidence: float
    agent: str
    conditions: Dict[str, Any]
    recommendation: str
    occurrences: int = 1
```

---

### Enhancement 2: Proactive Suggestions Engine (2-3 hours)

**Objective**: AI-powered fix suggestions based on learned patterns

**Implementation**:

```python
class ProactiveSuggestionEngine:
    """Generate proactive suggestions based on patterns and context."""

    def __init__(
        self,
        pattern_recognizer: PatternRecognizer,
        learning_db: Dict[str, Any]
    ):
        self.pattern_recognizer = pattern_recognizer
        self.learning_db = learning_db

    def generate_suggestions(
        self,
        agent: str,
        task: str,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate proactive suggestions for agent task."""
        suggestions = []

        # Pattern-based suggestions
        patterns = self.pattern_recognizer.match_patterns(agent, context)
        for pattern in patterns[:5]:  # Top 5 patterns
            suggestions.append(Suggestion(
                type="pattern_based",
                agent=agent,
                title=f"Learned Pattern: {pattern.type}",
                description=pattern.description,
                recommendation=pattern.recommendation,
                confidence=pattern.confidence,
                source="pattern_recognition"
            ))

        # Agent metrics-based suggestions
        metrics_suggestions = self._generate_from_metrics(agent, context)
        suggestions.extend(metrics_suggestions)

        # Context-based suggestions
        context_suggestions = self._generate_from_context(agent, task, context)
        suggestions.extend(context_suggestions)

        # Rank and return top suggestions
        suggestions.sort(key=lambda s: s.confidence, reverse=True)
        return suggestions[:10]  # Top 10

    def _generate_from_metrics(
        self,
        agent: str,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate suggestions from agent metrics."""
        suggestions = []

        agent_metrics = self.learning_db.get("agent_metrics", {}).get(agent)
        if not agent_metrics:
            return suggestions

        avg_time = agent_metrics.get("avg_time", 0)
        avg_findings = agent_metrics.get("avg_findings", 0)

        # Suggestion: Expected execution time
        if avg_time > 0:
            suggestions.append(Suggestion(
                type="timing_expectation",
                agent=agent,
                title="Expected Execution Time",
                description=f"Based on {agent_metrics['executions']} executions",
                recommendation=f"Expect ~{avg_time:.0f}s execution time, {avg_findings:.0f} findings",
                confidence=0.8,
                source="agent_metrics"
            ))

        # Suggestion: Agent efficiency
        if avg_time > 60:
            suggestions.append(Suggestion(
                type="efficiency_warning",
                agent=agent,
                title="Long Execution Time",
                description=f"{agent} typically takes {avg_time:.0f}s",
                recommendation="Consider running in background or breaking into smaller tasks",
                confidence=0.75,
                source="agent_metrics"
            ))

        return suggestions

    def _generate_from_context(
        self,
        agent: str,
        task: str,
        context: Dict[str, Any]
    ) -> List[Suggestion]:
        """Generate suggestions from current context."""
        suggestions = []

        # Suggestion: Critical issues from previous agents
        critical_issues = context.get("critical_issues", [])
        if critical_issues:
            suggestions.append(Suggestion(
                type="critical_priority",
                agent=agent,
                title="Critical Issues Detected",
                description=f"{len(critical_issues)} critical issues from previous agents",
                recommendation="Focus on validating and fixing critical issues first",
                confidence=0.95,
                source="context"
            ))

        # Suggestion: High priority areas
        high_priority_areas = context.get("high_priority_areas", [])
        if high_priority_areas:
            suggestions.append(Suggestion(
                type="focus_areas",
                agent=agent,
                title="High-Priority Code Areas",
                description=f"{len(high_priority_areas)} areas need attention",
                recommendation=f"Focus analysis on: {', '.join(high_priority_areas[:3])}",
                confidence=0.85,
                source="context"
            ))

        # Suggestion: Previous agent recommendations
        prev_recommendations = context.get("recommendations_from_previous_agents", [])
        if prev_recommendations:
            suggestions.append(Suggestion(
                type="agent_recommendation",
                agent=agent,
                title="Recommendations from Previous Agents",
                description=f"{len(prev_recommendations)} recommendations available",
                recommendation="Review and act on previous agent recommendations",
                confidence=0.9,
                source="context"
            ))

        return suggestions

@dataclass
class Suggestion:
    """Proactive suggestion for agent."""
    type: str
    agent: str
    title: str
    description: str
    recommendation: str
    confidence: float
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
```

---

### Enhancement 3: Metrics Dashboard (2-3 hours)

**Objective**: Visual metrics tracking and performance monitoring

**Implementation**:

```python
class MetricsDashboard:
    """Comprehensive metrics tracking and visualization."""

    def __init__(self, learning_db: Dict[str, Any]):
        self.learning_db = learning_db

    def generate_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive metrics dashboard."""
        return {
            "summary": self._get_summary_metrics(),
            "agent_performance": self._get_agent_performance(),
            "success_rate": self._get_success_rate(),
            "time_analysis": self._get_time_analysis(),
            "findings_analysis": self._get_findings_analysis(),
            "failure_analysis": self._get_failure_analysis(),
            "trends": self._get_trends()
        }

    def _get_summary_metrics(self) -> Dict[str, Any]:
        """Get high-level summary metrics."""
        return {
            "total_executions": self._count_total_executions(),
            "success_rate": self._calculate_success_rate(),
            "avg_execution_time": self._calculate_avg_execution_time(),
            "total_findings": self._count_total_findings(),
            "critical_issues_fixed": self._count_critical_fixes(),
            "total_agents": len(self.learning_db.get("agent_metrics", {}))
        }

    def _get_agent_performance(self) -> List[Dict[str, Any]]:
        """Get per-agent performance metrics."""
        performance = []

        for agent_name, metrics in self.learning_db.get("agent_metrics", {}).items():
            performance.append({
                "agent": agent_name,
                "executions": metrics.get("executions", 0),
                "avg_time": metrics.get("avg_time", 0),
                "avg_findings": metrics.get("avg_findings", 0),
                "efficiency": metrics.get("avg_findings", 0) / metrics.get("avg_time", 1),
                "total_time": metrics.get("total_time", 0),
                "total_findings": metrics.get("total_findings", 0)
            })

        # Sort by efficiency
        performance.sort(key=lambda x: x["efficiency"], reverse=True)
        return performance

    def _get_success_rate(self) -> Dict[str, Any]:
        """Calculate success rates."""
        successful = len(self.learning_db.get("successful_patterns", []))
        failed = len(self.learning_db.get("failed_patterns", []))
        total = successful + failed

        return {
            "successful": successful,
            "failed": failed,
            "total": total,
            "rate": (successful / total * 100) if total > 0 else 0
        }

    def _get_time_analysis(self) -> Dict[str, Any]:
        """Analyze execution time patterns."""
        times = []

        for metrics in self.learning_db.get("agent_metrics", {}).values():
            if "avg_time" in metrics:
                times.append(metrics["avg_time"])

        if not times:
            return {"min": 0, "max": 0, "avg": 0, "median": 0}

        times.sort()
        return {
            "min": min(times),
            "max": max(times),
            "avg": sum(times) / len(times),
            "median": times[len(times) // 2]
        }

    def _get_findings_analysis(self) -> Dict[str, Any]:
        """Analyze findings patterns."""
        findings = []

        for metrics in self.learning_db.get("agent_metrics", {}).values():
            if "avg_findings" in metrics:
                findings.append(metrics["avg_findings"])

        if not findings:
            return {"min": 0, "max": 0, "avg": 0, "total": 0}

        return {
            "min": min(findings),
            "max": max(findings),
            "avg": sum(findings) / len(findings),
            "total": sum(f * self.learning_db["agent_metrics"][agent]["executions"]
                        for agent, f in zip(self.learning_db["agent_metrics"].keys(), findings))
        }

    def _get_failure_analysis(self) -> Dict[str, Any]:
        """Analyze failure patterns."""
        reasons = {}

        for pattern in self.learning_db.get("failed_patterns", []):
            reason = pattern.get("failure_reason", "Unknown")
            reasons[reason] = reasons.get(reason, 0) + 1

        # Sort by frequency
        top_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "total_failures": len(self.learning_db.get("failed_patterns", [])),
            "unique_reasons": len(reasons),
            "top_reasons": [{"reason": r, "count": c} for r, c in top_reasons]
        }

    def _get_trends(self) -> Dict[str, Any]:
        """Get trend analysis (requires timestamped data)."""
        # Placeholder for trend analysis
        return {
            "execution_time_trend": "stable",
            "success_rate_trend": "improving",
            "findings_trend": "increasing"
        }

    def export_metrics(self, filepath: Path):
        """Export metrics to JSON file."""
        dashboard = self.generate_dashboard()

        with open(filepath, 'w') as f:
            json.dump(dashboard, f, indent=2, default=str)

    def print_summary(self):
        """Print metrics summary to console."""
        dashboard = self.generate_dashboard()

        print("\n" + "="*80)
        print("METRICS DASHBOARD")
        print("="*80)

        summary = dashboard["summary"]
        print(f"\n📊 Summary:")
        print(f"   Total Executions: {summary['total_executions']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Avg Execution Time: {summary['avg_execution_time']:.1f}s")
        print(f"   Total Findings: {summary['total_findings']}")
        print(f"   Critical Issues Fixed: {summary['critical_issues_fixed']}")

        print(f"\n🏆 Top Performing Agents:")
        for i, agent in enumerate(dashboard["agent_performance"][:5], 1):
            print(f"   {i}. {agent['agent']}: {agent['efficiency']:.1f} findings/sec")

        print(f"\n❌ Common Failure Reasons:")
        for reason in dashboard["failure_analysis"]["top_reasons"]:
            print(f"   - {reason['reason']}: {reason['count']} times")

        print("\n" + "="*80 + "\n")
```

---

## 🔧 Integration Strategy

### Step 1: Integrate Build System Adapter
1. Create `build_system_adapter.py`
2. Update `validation_pipeline.py` to use BuildSystemAdapter
3. Test with real builds

### Step 2: Integrate Prompt Templates
1. Create `prompt_templates.py`
2. Update `enhanced_orchestrator.py` to use PromptTemplate
3. Test prompt generation

### Step 3: Integrate Progress Reporting
1. Create `progress_reporter.py`
2. Add progress callbacks to orchestrator
3. Test real-time updates

### Step 4: Integrate Pattern Recognition
1. Create `pattern_recognizer.py`
2. Update orchestrator to extract patterns after each execution
3. Test pattern matching

### Step 5: Integrate Proactive Suggestions
1. Create `proactive_suggestions.py`
2. Generate suggestions before each agent execution
3. Test suggestion quality

### Step 6: Integrate Metrics Dashboard
1. Create `metrics_dashboard.py`
2. Add dashboard generation to orchestrator
3. Test dashboard export

---

## ✅ Success Criteria

### Phase 2
- ✅ Build system can execute CMake and parse output
- ✅ Tests can be run with filtering and results parsed
- ✅ Prompts are context-rich with previous findings
- ✅ Progress updates stream in real-time
- ✅ All Phase 2 tests pass

### Phase 3
- ✅ Patterns extracted from execution history
- ✅ Patterns matched to current context
- ✅ Suggestions generated proactively
- ✅ Metrics dashboard shows comprehensive data
- ✅ All Phase 3 tests pass

---

## 📊 Expected Impact

### Phase 2 Impact
- **Build Integration**: 100% automated validation
- **Context-Rich Prompts**: 30-50% better agent output
- **Progress Reporting**: Real-time visibility

### Phase 3 Impact
- **Pattern Recognition**: Proactive issue prevention
- **Proactive Suggestions**: 20-30% faster workflows
- **Metrics Dashboard**: Data-driven optimization

### Combined Impact
- **Total Efficiency**: 3-5x faster workflows
- **Quality**: 100% automated quality gates
- **Intelligence**: Continuously improving system

---

**Document Created**: 2025-09-29
**Status**: Ready for implementation
**Estimated Time**: Phase 2 (10-12 hours) + Phase 3 (8-10 hours) = 18-22 hours total