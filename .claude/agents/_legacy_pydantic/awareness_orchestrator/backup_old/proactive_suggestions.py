"""
Proactive Suggestions Engine
Analyzes code and patterns to provide proactive recommendations before issues occur
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pattern_recognition import PatternRecognitionSystem, Pattern, PatternType, Severity


class SuggestionType(str, Enum):
    """Types of proactive suggestions."""
    CODE_SMELL = "code_smell"
    OPTIMIZATION = "optimization"
    SAFETY_IMPROVEMENT = "safety_improvement"
    MAINTENANCE = "maintenance"
    REFACTORING = "refactoring"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    PERFORMANCE = "performance"


class Priority(str, Enum):
    """Suggestion priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Suggestion:
    """Proactive suggestion for code improvement."""
    suggestion_id: str
    suggestion_type: SuggestionType
    priority: Priority
    title: str
    description: str
    file_path: str
    line_range: Optional[tuple] = None  # (start_line, end_line)
    rationale: str = ""
    recommended_action: str = ""
    estimated_effort: str = ""  # "5 minutes", "30 minutes", "2 hours", etc.
    potential_impact: str = ""
    related_patterns: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """Human-readable string representation."""
        location = f"{self.file_path}"
        if self.line_range:
            location += f":{self.line_range[0]}-{self.line_range[1]}"

        return f"[{self.priority.value.upper()}] {self.title}\n  Location: {location}\n  {self.description}"


class ProactiveSuggestionsEngine:
    """
    Proactive suggestions engine that analyzes code and patterns to provide
    recommendations before issues occur.

    Features:
    - Code smell detection
    - Predictive issue identification
    - Optimization opportunity analysis
    - Risk assessment
    - Pattern-based recommendations
    """

    def __init__(self, pattern_system: Optional[PatternRecognitionSystem] = None):
        """
        Initialize proactive suggestions engine.

        Args:
            pattern_system: Optional PatternRecognitionSystem for historical data
        """
        self.pattern_system = pattern_system or PatternRecognitionSystem()
        self.suggestions: List[Suggestion] = []

        # Code smell patterns
        self.code_smell_patterns = {
            "magic_numbers": {
                "pattern": r'\b\d{3,}\b(?!\s*[;,)])',  # Numbers with 3+ digits not in obvious contexts
                "title": "Magic Number Detected",
                "description": "Hard-coded numeric literal without explanation",
                "recommended_action": "Extract to named constant with descriptive name",
                "priority": Priority.MEDIUM
            },
            "long_function": {
                "lines_threshold": 100,
                "title": "Long Function",
                "description": "Function exceeds recommended length (100 lines)",
                "recommended_action": "Consider breaking into smaller, focused functions",
                "priority": Priority.LOW
            },
            "deep_nesting": {
                "depth_threshold": 4,
                "title": "Deep Nesting",
                "description": "Code nesting exceeds recommended depth (4 levels)",
                "recommended_action": "Extract nested logic into separate functions or use early returns",
                "priority": Priority.MEDIUM
            },
            "duplicate_code": {
                "similarity_threshold": 0.8,
                "title": "Duplicate Code",
                "description": "Similar code block detected in multiple locations",
                "recommended_action": "Extract common logic into reusable function",
                "priority": Priority.MEDIUM
            },
            "commented_code": {
                "pattern": r'^\s*//.*\{|^\s*//.*\}|^\s*//.*return|^\s*//.*if\s*\(',
                "title": "Commented-Out Code",
                "description": "Code commented out instead of removed",
                "recommended_action": "Remove commented code (use version control for history)",
                "priority": Priority.LOW
            },
            "todo_fixme": {
                "pattern": r'(TODO|FIXME|HACK|XXX):',
                "title": "Technical Debt Marker",
                "description": "TODO/FIXME comment indicates incomplete work",
                "recommended_action": "Address technical debt or create tracking issue",
                "priority": Priority.MEDIUM
            }
        }

        # Performance warning patterns
        self.performance_patterns = {
            "string_concatenation_loop": {
                "pattern": r'for\s*\([^)]+\)\s*\{[^}]*\+\=\s*["\']',
                "title": "String Concatenation in Loop",
                "description": "String concatenation inside loop can be inefficient",
                "recommended_action": "Use std::ostringstream or reserve capacity",
                "priority": Priority.MEDIUM
            },
            "unnecessary_copy": {
                "pattern": r'for\s*\(\s*auto\s+\w+\s*:',  # range-for without reference
                "title": "Potential Unnecessary Copy",
                "description": "Range-based for loop may be copying elements",
                "recommended_action": "Use const auto& if elements don't need modification",
                "priority": Priority.MEDIUM
            },
            "endl_usage": {
                "pattern": r'std::endl',
                "title": "Using std::endl Instead of \\n",
                "description": "std::endl flushes buffer, reducing performance",
                "recommended_action": "Use '\\n' instead unless explicit flush needed",
                "priority": Priority.LOW
            }
        }

        # Safety warning patterns
        self.safety_patterns = {
            "raw_pointer": {
                "pattern": r'\bnew\s+\w+',
                "title": "Raw Pointer Allocation",
                "description": "Raw pointer allocation without smart pointer",
                "recommended_action": "Use std::unique_ptr or std::shared_ptr",
                "priority": Priority.HIGH
            },
            "c_style_cast": {
                "pattern": r'\(\s*\w+\s*\*?\s*\)',
                "title": "C-Style Cast",
                "description": "C-style cast is less safe than C++ casts",
                "recommended_action": "Use static_cast, dynamic_cast, or reinterpret_cast",
                "priority": Priority.MEDIUM
            },
            "unsafe_array_access": {
                "pattern": r'\w+\[\w+\](?!\s*=)',
                "title": "Unchecked Array Access",
                "description": "Array access without bounds checking",
                "recommended_action": "Use gsl::span or .at() for bounds checking",
                "priority": Priority.HIGH
            }
        }

    def analyze_file(self, file_path: Path) -> List[Suggestion]:
        """
        Analyze file and generate proactive suggestions.

        Args:
            file_path: Path to file to analyze

        Returns:
            List of suggestions for the file
        """
        self.suggestions = []

        if not file_path.exists():
            return self.suggestions

        try:
            content = file_path.read_text()
            lines = content.split('\n')

            # Analyze for code smells
            self._detect_code_smells(file_path, content, lines)

            # Analyze for performance issues
            self._detect_performance_issues(file_path, content, lines)

            # Analyze for safety issues
            self._detect_safety_issues(file_path, content, lines)

            # Pattern-based suggestions
            self._generate_pattern_based_suggestions(file_path)

            # Risk assessment
            self._assess_risk(file_path)

            return self.suggestions

        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")
            return []

    def _detect_code_smells(self, file_path: Path, content: str, lines: List[str]):
        """Detect code smells in the file."""

        # Magic numbers
        for i, line in enumerate(lines, 1):
            if match := re.search(self.code_smell_patterns["magic_numbers"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"smell_magic_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.CODE_SMELL,
                    priority=self.code_smell_patterns["magic_numbers"]["priority"],
                    title=self.code_smell_patterns["magic_numbers"]["title"],
                    description=f"{self.code_smell_patterns['magic_numbers']['description']}: {match.group()}",
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="Magic numbers reduce code readability and maintainability",
                    recommended_action=self.code_smell_patterns["magic_numbers"]["recommended_action"],
                    estimated_effort="5 minutes",
                    potential_impact="Improved code clarity",
                    tags=["code_smell", "readability"]
                ))

        # Commented code
        for i, line in enumerate(lines, 1):
            if re.search(self.code_smell_patterns["commented_code"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"smell_commented_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.CODE_SMELL,
                    priority=self.code_smell_patterns["commented_code"]["priority"],
                    title=self.code_smell_patterns["commented_code"]["title"],
                    description=self.code_smell_patterns["commented_code"]["description"],
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="Commented code creates confusion and clutter",
                    recommended_action=self.code_smell_patterns["commented_code"]["recommended_action"],
                    estimated_effort="2 minutes",
                    potential_impact="Cleaner codebase",
                    tags=["code_smell", "maintenance"]
                ))

        # TODO/FIXME markers
        for i, line in enumerate(lines, 1):
            if match := re.search(self.code_smell_patterns["todo_fixme"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"smell_todo_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.MAINTENANCE,
                    priority=self.code_smell_patterns["todo_fixme"]["priority"],
                    title=self.code_smell_patterns["todo_fixme"]["title"],
                    description=f"{self.code_smell_patterns['todo_fixme']['description']}: {line.strip()}",
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="Unaddressed technical debt accumulates over time",
                    recommended_action=self.code_smell_patterns["todo_fixme"]["recommended_action"],
                    estimated_effort="Varies",
                    potential_impact="Reduced technical debt",
                    tags=["technical_debt", "maintenance"]
                ))

        # Long functions
        self._detect_long_functions(file_path, lines)

        # Deep nesting
        self._detect_deep_nesting(file_path, lines)

    def _detect_long_functions(self, file_path: Path, lines: List[str]):
        """Detect functions exceeding length threshold."""
        in_function = False
        function_start = 0
        function_name = ""
        brace_count = 0

        for i, line in enumerate(lines, 1):
            # Detect function start (simplified)
            if re.search(r'^\s*\w+.*\([^)]*\)\s*\{', line) or re.search(r'^\s*\w+.*\([^)]*\)\s*$', line):
                if not in_function:
                    in_function = True
                    function_start = i
                    # Extract function name
                    if match := re.search(r'(\w+)\s*\(', line):
                        function_name = match.group(1)

            # Count braces
            if in_function:
                brace_count += line.count('{') - line.count('}')

                # Function ended
                if brace_count <= 0 and i > function_start:
                    function_length = i - function_start

                    if function_length > self.code_smell_patterns["long_function"]["lines_threshold"]:
                        self.suggestions.append(Suggestion(
                            suggestion_id=f"smell_long_func_{file_path.name}_{function_start}",
                            suggestion_type=SuggestionType.REFACTORING,
                            priority=self.code_smell_patterns["long_function"]["priority"],
                            title=self.code_smell_patterns["long_function"]["title"],
                            description=f"{self.code_smell_patterns['long_function']['description']} ({function_length} lines): {function_name}",
                            file_path=str(file_path),
                            line_range=(function_start, i),
                            rationale="Long functions are harder to understand, test, and maintain",
                            recommended_action=self.code_smell_patterns["long_function"]["recommended_action"],
                            estimated_effort="30-60 minutes",
                            potential_impact="Better code organization and testability",
                            tags=["refactoring", "maintainability"]
                        ))

                    in_function = False
                    brace_count = 0

    def _detect_deep_nesting(self, file_path: Path, lines: List[str]):
        """Detect code with excessive nesting depth."""
        max_depth = 0
        current_depth = 0
        depth_line = 0

        for i, line in enumerate(lines, 1):
            # Track nesting depth (simplified)
            depth_change = line.count('{') - line.count('}')
            current_depth += depth_change

            if current_depth > max_depth:
                max_depth = current_depth
                depth_line = i

            if max_depth > self.code_smell_patterns["deep_nesting"]["depth_threshold"]:
                self.suggestions.append(Suggestion(
                    suggestion_id=f"smell_deep_nest_{file_path.name}_{depth_line}",
                    suggestion_type=SuggestionType.REFACTORING,
                    priority=self.code_smell_patterns["deep_nesting"]["priority"],
                    title=self.code_smell_patterns["deep_nesting"]["title"],
                    description=f"{self.code_smell_patterns['deep_nesting']['description']} (depth: {max_depth})",
                    file_path=str(file_path),
                    line_range=(depth_line, depth_line),
                    rationale="Deep nesting reduces code readability and increases complexity",
                    recommended_action=self.code_smell_patterns["deep_nesting"]["recommended_action"],
                    estimated_effort="20-40 minutes",
                    potential_impact="Improved code readability",
                    tags=["refactoring", "complexity"]
                ))
                # Reset to avoid duplicate suggestions
                max_depth = self.code_smell_patterns["deep_nesting"]["depth_threshold"]

    def _detect_performance_issues(self, file_path: Path, content: str, lines: List[str]):
        """Detect potential performance issues."""

        # std::endl usage
        for i, line in enumerate(lines, 1):
            if re.search(self.performance_patterns["endl_usage"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"perf_endl_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.PERFORMANCE,
                    priority=self.performance_patterns["endl_usage"]["priority"],
                    title=self.performance_patterns["endl_usage"]["title"],
                    description=self.performance_patterns["endl_usage"]["description"],
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="std::endl forces buffer flush, reducing I/O performance",
                    recommended_action=self.performance_patterns["endl_usage"]["recommended_action"],
                    estimated_effort="2 minutes",
                    potential_impact="Improved I/O performance (BLITZFIRE optimization)",
                    tags=["performance", "blitzfire"]
                ))

        # Unnecessary copies in range-for
        for i, line in enumerate(lines, 1):
            if re.search(self.performance_patterns["unnecessary_copy"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"perf_copy_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.PERFORMANCE,
                    priority=self.performance_patterns["unnecessary_copy"]["priority"],
                    title=self.performance_patterns["unnecessary_copy"]["title"],
                    description=self.performance_patterns["unnecessary_copy"]["description"],
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="Copying large objects in loops impacts performance",
                    recommended_action=self.performance_patterns["unnecessary_copy"]["recommended_action"],
                    estimated_effort="5 minutes",
                    potential_impact="Reduced memory allocations and copies",
                    tags=["performance", "optimization"]
                ))

    def _detect_safety_issues(self, file_path: Path, content: str, lines: List[str]):
        """Detect potential safety issues."""

        # Raw pointer allocations
        for i, line in enumerate(lines, 1):
            if re.search(self.safety_patterns["raw_pointer"]["pattern"], line):
                self.suggestions.append(Suggestion(
                    suggestion_id=f"safety_raw_ptr_{file_path.name}_{i}",
                    suggestion_type=SuggestionType.SAFETY_IMPROVEMENT,
                    priority=self.safety_patterns["raw_pointer"]["priority"],
                    title=self.safety_patterns["raw_pointer"]["title"],
                    description=self.safety_patterns["raw_pointer"]["description"],
                    file_path=str(file_path),
                    line_range=(i, i),
                    rationale="Raw pointers can leak memory if exceptions occur",
                    recommended_action=self.safety_patterns["raw_pointer"]["recommended_action"],
                    estimated_effort="10 minutes",
                    potential_impact="Improved memory safety and exception safety",
                    tags=["safety", "memory_management"]
                ))

    def _generate_pattern_based_suggestions(self, file_path: Path):
        """Generate suggestions based on historical patterns."""
        if not self.pattern_system:
            return

        # Get patterns for this file
        file_patterns = self.pattern_system.get_patterns_for_file(str(file_path))

        # Error patterns
        error_patterns = [p for p in file_patterns if p.pattern_type == PatternType.ERROR_PATTERN]

        if error_patterns:
            # Most common error for this file
            most_common = max(error_patterns, key=lambda p: p.occurrences)

            self.suggestions.append(Suggestion(
                suggestion_id=f"pattern_error_{file_path.name}",
                suggestion_type=SuggestionType.MAINTENANCE,
                priority=Priority.HIGH if most_common.occurrences > 3 else Priority.MEDIUM,
                title=f"Recurring Error Pattern: {most_common.name}",
                description=f"This file has experienced {most_common.name} {most_common.occurrences} times",
                file_path=str(file_path),
                rationale="Recurring errors indicate underlying structural issues",
                recommended_action=f"Review root cause and apply preventive fixes. Known agents: {', '.join(most_common.agents_involved)}",
                estimated_effort="1-2 hours",
                potential_impact="Prevent recurring build failures",
                related_patterns=[most_common.pattern_id],
                tags=["pattern", "recurring_issue"]
            ))

        # Recurring issues
        recurring_patterns = [p for p in file_patterns if p.pattern_type == PatternType.RECURRING_ISSUE]

        if recurring_patterns:
            for pattern in recurring_patterns:
                self.suggestions.append(Suggestion(
                    suggestion_id=f"pattern_recurring_{file_path.name}",
                    suggestion_type=SuggestionType.MAINTENANCE,
                    priority=Priority.HIGH,
                    title="File Requires Attention",
                    description=f"This file has had {pattern.metadata.get('recent_failures', 0)} failures recently",
                    file_path=str(file_path),
                    rationale="Multiple recent failures suggest code needs refactoring",
                    recommended_action="Consider comprehensive code review and refactoring",
                    estimated_effort="2-4 hours",
                    potential_impact="Improved code stability",
                    related_patterns=[pattern.pattern_id],
                    tags=["pattern", "high_risk"]
                ))

        # Performance patterns
        perf_patterns = [p for p in file_patterns if p.pattern_type == PatternType.PERFORMANCE_PATTERN]

        if perf_patterns:
            for pattern in perf_patterns:
                self.suggestions.append(Suggestion(
                    suggestion_id=f"pattern_perf_{file_path.name}",
                    suggestion_type=SuggestionType.OPTIMIZATION,
                    priority=Priority.MEDIUM,
                    title="Slow Orchestration History",
                    description=f"Orchestration for this file takes longer than average",
                    file_path=str(file_path),
                    rationale=f"Average slowdown: {pattern.metadata.get('slowdown_factor', 1.0):.1f}x",
                    recommended_action="Optimize code or simplify test logic",
                    estimated_effort="1-2 hours",
                    potential_impact="Faster development iteration",
                    related_patterns=[pattern.pattern_id],
                    tags=["pattern", "performance"]
                ))

    def _assess_risk(self, file_path: Path):
        """Assess overall risk level for file."""
        if not self.pattern_system:
            return

        file_patterns = self.pattern_system.get_patterns_for_file(str(file_path))

        # Calculate risk score
        risk_score = 0

        for pattern in file_patterns:
            if pattern.pattern_type == PatternType.ERROR_PATTERN:
                risk_score += pattern.occurrences * 2
            elif pattern.pattern_type == PatternType.RECURRING_ISSUE:
                risk_score += pattern.occurrences * 5

        # High-risk file warning
        if risk_score > 10:
            self.suggestions.append(Suggestion(
                suggestion_id=f"risk_high_{file_path.name}",
                suggestion_type=SuggestionType.MAINTENANCE,
                priority=Priority.CRITICAL,
                title="HIGH-RISK FILE DETECTED",
                description=f"This file has a risk score of {risk_score} (threshold: 10)",
                file_path=str(file_path),
                rationale="High frequency of errors and recurring issues",
                recommended_action="Prioritize comprehensive review and refactoring of this file",
                estimated_effort="4-8 hours",
                potential_impact="Significantly improved code stability",
                tags=["risk", "high_priority"]
            ))

    def get_suggestions_by_priority(self, priority: Priority) -> List[Suggestion]:
        """Get all suggestions of specific priority."""
        return [s for s in self.suggestions if s.priority == priority]

    def get_suggestions_by_type(self, suggestion_type: SuggestionType) -> List[Suggestion]:
        """Get all suggestions of specific type."""
        return [s for s in self.suggestions if s.suggestion_type == suggestion_type]

    def get_critical_suggestions(self) -> List[Suggestion]:
        """Get all critical priority suggestions."""
        return self.get_suggestions_by_priority(Priority.CRITICAL)

    def get_high_priority_suggestions(self) -> List[Suggestion]:
        """Get all high priority suggestions."""
        return self.get_suggestions_by_priority(Priority.HIGH)

    def get_actionable_suggestions(self, max_effort_minutes: int = 30) -> List[Suggestion]:
        """
        Get suggestions that can be completed quickly.

        Args:
            max_effort_minutes: Maximum estimated effort in minutes

        Returns:
            List of quick-win suggestions
        """
        actionable = []

        for suggestion in self.suggestions:
            effort = suggestion.estimated_effort.lower()

            # Parse effort estimate
            if "minute" in effort:
                if match := re.search(r'(\d+)', effort):
                    minutes = int(match.group(1))
                    if minutes <= max_effort_minutes:
                        actionable.append(suggestion)

        return sorted(actionable, key=lambda s: s.priority.value)

    def generate_report(self) -> str:
        """Generate comprehensive suggestions report."""
        if not self.suggestions:
            return "No suggestions available."

        report = ["=" * 80, "Proactive Suggestions Report", "=" * 80, ""]

        # Summary statistics
        priority_counts = {p: 0 for p in Priority}
        type_counts = {t: 0 for t in SuggestionType}

        for suggestion in self.suggestions:
            priority_counts[suggestion.priority] += 1
            type_counts[suggestion.suggestion_type] += 1

        report.append(f"Total Suggestions: {len(self.suggestions)}")
        report.append("")

        report.append("📊 Priority Distribution:")
        for priority, count in sorted(priority_counts.items(), key=lambda x: x[0].value):
            if count > 0:
                report.append(f"  {priority.value.upper()}: {count}")
        report.append("")

        report.append("📈 Type Distribution:")
        for stype, count in sorted(type_counts.items(), key=lambda x: x[0].value):
            if count > 0:
                report.append(f"  {stype.value}: {count}")
        report.append("")

        # Critical and high priority suggestions
        critical = self.get_critical_suggestions()
        high = self.get_high_priority_suggestions()

        if critical:
            report.append("🚨 CRITICAL PRIORITY SUGGESTIONS:")
            report.append("=" * 80)
            for i, suggestion in enumerate(critical, 1):
                report.append(f"\n{i}. {suggestion.title}")
                report.append(f"   File: {suggestion.file_path}")
                if suggestion.line_range:
                    report.append(f"   Lines: {suggestion.line_range[0]}-{suggestion.line_range[1]}")
                report.append(f"   Description: {suggestion.description}")
                report.append(f"   Action: {suggestion.recommended_action}")
                report.append(f"   Effort: {suggestion.estimated_effort}")
                report.append(f"   Impact: {suggestion.potential_impact}")
            report.append("")

        if high:
            report.append("⚠️  HIGH PRIORITY SUGGESTIONS:")
            report.append("=" * 80)
            for i, suggestion in enumerate(high, 1):
                report.append(f"\n{i}. {suggestion.title}")
                report.append(f"   File: {suggestion.file_path}")
                if suggestion.line_range:
                    report.append(f"   Lines: {suggestion.line_range[0]}-{suggestion.line_range[1]}")
                report.append(f"   Description: {suggestion.description}")
                report.append(f"   Action: {suggestion.recommended_action}")
                report.append(f"   Effort: {suggestion.estimated_effort}")
            report.append("")

        # Quick wins
        quick_wins = self.get_actionable_suggestions(max_effort_minutes=15)
        if quick_wins:
            report.append("⚡ QUICK WINS (< 15 minutes):")
            report.append("=" * 80)
            for i, suggestion in enumerate(quick_wins, 1):
                report.append(f"\n{i}. {suggestion.title}")
                report.append(f"   File: {suggestion.file_path}")
                report.append(f"   Action: {suggestion.recommended_action}")
                report.append(f"   Effort: {suggestion.estimated_effort}")
            report.append("")

        report.append("=" * 80)
        return "\n".join(report)


def main():
    """Test proactive suggestions engine."""
    print("=" * 80)
    print("Proactive Suggestions Engine - Test")
    print("=" * 80)

    # Initialize with pattern system
    pattern_system = PatternRecognitionSystem()
    engine = ProactiveSuggestionsEngine(pattern_system)

    # Create test file
    test_file = Path("test_suggestions.cpp")

    test_code = """
// Test file for suggestions engine
#include <iostream>
#include <vector>

// TODO: Refactor this function
void processData() {
    int threshold = 1000;  // Magic number

    for (auto item : items) {  // Unnecessary copy
        std::cout << item << std::endl;  // Using endl
    }

    // Old implementation
    // if (condition) {
    //     return result;
    // }

    int* data = new int[100];  // Raw pointer

    for (int i = 0; i < 100; i++) {
        if (data[i] > threshold) {  // Unchecked access
            if (data[i] < 2000) {
                if (data[i] % 2 == 0) {
                    if (data[i] > 1500) {  // Deep nesting
                        std::cout << "Found!" << std::endl;
                    }
                }
            }
        }
    }
}

// FIXME: This needs optimization
void longFunction() {
    // Simulating long function with many lines
"""

    # Add many lines to trigger long function detection
    for i in range(120):
        test_code += f"    // Line {i}\n"

    test_code += "}\n"

    test_file.write_text(test_code)

    print(f"\n📁 Analyzing file: {test_file}")
    print("=" * 80)

    # Analyze file
    suggestions = engine.analyze_file(test_file)

    print(f"\n✅ Analysis complete: {len(suggestions)} suggestions generated")
    print("")

    # Generate report
    report = engine.generate_report()
    print(report)

    # Clean up
    test_file.unlink()

    print("\n" + "=" * 80)
    print("Test Complete")
    print("=" * 80)


if __name__ == "__main__":
    main()