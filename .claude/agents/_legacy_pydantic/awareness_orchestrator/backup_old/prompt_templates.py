"""
Context-Rich Prompting System
Template-based prompt generation with agent-specific context
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class TemplateType(str, Enum):
    """Types of prompt templates."""
    ANALYSIS = "analysis"
    FIXING = "fixing"
    VALIDATION = "validation"
    OPTIMIZATION = "optimization"


class PromptTemplate:
    """
    Template system for generating context-rich agent prompts.

    Features:
    - Multiple template types (analysis, fixing, validation, optimization)
    - Agent-specific role descriptions
    - Context integration from previous agents
    - Focus areas highlighting
    - Structured output expectations
    - Safety guidelines
    """

    # Agent role descriptions
    AGENT_ROLES = {
        "multi-agent-debugging-system": {
            "role": "Comprehensive debugging and issue discovery across all code quality dimensions",
            "expertise": ["bug detection", "code smells", "architectural issues", "best practices"],
            "output_focus": "Structured findings with severity levels and actionable recommendations"
        },
        "clang-tidy-analyzer": {
            "role": "Static code analysis for C++ quality, safety, and best practices",
            "expertise": ["C++ standards compliance", "memory safety", "performance issues", "modern C++ idioms"],
            "output_focus": "Specific violations with file:line locations and fix suggestions"
        },
        "clang-tidy-fixer": {
            "role": "Apply intelligent fixes for clang-tidy findings",
            "expertise": ["automated refactoring", "safe transformations", "incremental fixes"],
            "output_focus": "Applied fixes with before/after comparisons and validation status"
        },
        "valgrind-safety-analyzer": {
            "role": "Runtime memory safety and threading analysis",
            "expertise": ["memory leaks", "invalid access", "race conditions", "heap profiling"],
            "output_focus": "Runtime issues with stack traces and recommended mitigations"
        },
        "blitzfire-cpp-optimizer": {
            "role": "Performance optimization and SIMD/cache optimization",
            "expertise": ["algorithmic optimization", "SIMD vectorization", "cache optimization", "profiling"],
            "output_focus": "Performance bottlenecks with optimization opportunities and expected speedups"
        },
        "passive-code-analyzer": {
            "role": "Continuous background analysis with automatic fixing",
            "expertise": ["incremental analysis", "automatic fixes", "quality monitoring"],
            "output_focus": "Issues found and auto-fixed, remaining manual fixes needed"
        },
        "zero-warnings-enforcer": {
            "role": "Eliminate and prevent compiler warnings",
            "expertise": ["warning elimination", "prevention systems", "quality gates"],
            "output_focus": "Warning analysis with elimination strategies and prevention measures"
        },
        "never-fail-build-resolver": {
            "role": "Intelligent build problem resolution with never-fail approach",
            "expertise": ["build failures", "dependency issues", "systematic debugging"],
            "output_focus": "Root cause analysis with step-by-step resolution plan"
        }
    }

    # Template definitions
    TEMPLATES = {
        TemplateType.ANALYSIS: """# Task: {task_description}

## Target: {target}

{context_section}

## Your Role

As the **{agent_name}** agent, your role is:
**{agent_role}**

### Expertise Areas:
{expertise_list}

### Expected Output:
{output_focus}

## Analysis Focus

{focus_areas}

## Directives

1. **Build on Previous Work**: Don't duplicate analysis already done by previous agents
2. **Cross-Reference**: Validate findings against issues already identified
3. **Prioritize**: Focus on critical and high-severity issues first
4. **Be Specific**: Include file:line locations for all findings
5. **Be Actionable**: Provide concrete recommendations, not just observations
6. **Validate**: Check if previously reported issues have been fixed

## Output Format

Provide structured findings with:

- **Severity**: critical | high | medium | low | info
- **Category**: bug | performance | security | quality | documentation
- **Location**: File:line reference (e.g., safe_test.cpp:868)
- **Title**: Brief description of the issue
- **Description**: Detailed explanation of the problem
- **Recommendation**: Specific fix suggestion with code examples if applicable
- **Confidence**: Your confidence level (0.0-1.0)

Example:
```
Severity: critical
Category: bug
Location: safe_test.cpp:868
Title: Memory pool prefetch bug
Description: Unreachable code due to misplaced closing brace. The prefetch operation will never execute, potentially causing out-of-bounds access.
Recommendation: Move the closing brace after the prefetch call to ensure it executes within the bounds check.
Confidence: 0.95
```

{additional_guidelines}
""",

        TemplateType.FIXING: """# Task: {task_description}

## Target: {target}

{context_section}

## Your Role

As the **{agent_name}** agent, your role is:
**{agent_role}**

### Expertise Areas:
{expertise_list}

## Fixes Required

{fixes_required}

## Safety Guidelines

1. **Incremental Application**: Apply fixes in small batches (3-5 changes at a time)
2. **Preserve Functionality**: Maintain existing behavior unless explicitly changing it
3. **Style Consistency**: Follow existing code style and conventions
4. **Documentation**: Add comments for non-obvious changes
5. **Testing**: Each batch of fixes must pass validation (build + tests)
6. **Rollback Ready**: Changes will be automatically rolled back if validation fails

## Fix Priority

Apply fixes in this order:
1. **Critical**: Issues causing crashes, UB, or security vulnerabilities
2. **High**: Issues affecting correctness or causing warnings-as-errors
3. **Medium**: Code quality and maintainability improvements
4. **Low**: Style and documentation improvements

## Output Format

For each fix applied, provide:

- **File**: Path to modified file
- **Lines**: Line range modified (e.g., 868-872)
- **Change Type**: fix | refactor | optimization | style
- **Description**: What was changed and why
- **Before**: Code before the change (relevant excerpt)
- **After**: Code after the change
- **Validation**: Test to run for verification
- **Risk Level**: low | medium | high

Example:
```
File: tests/safe_test.cpp
Lines: 868-870
Change Type: fix
Description: Fixed memory pool prefetch bug by moving closing brace
Before:
  if (next_free_ < PoolSize) {{
  }}
      blitzfire_prefetch<...>(&pool_[next_free_]);

After:
  if (next_free_ < PoolSize) {{
      blitzfire_prefetch<...>(&pool_[next_free_]);
  }}

Validation: Run SafetyTestSuite.MemoryPool
Risk Level: low
```

{additional_guidelines}
""",

        TemplateType.VALIDATION: """# Task: {task_description}

## Target: {target}

{context_section}

## Your Role

As the **{agent_name}** agent, your role is:
**{agent_role}**

### Expertise Areas:
{expertise_list}

## Validation Checklist

{validation_checklist}

## Success Criteria

### Build Validation:
- ✅ Build completes without errors
- ✅ Zero new warnings introduced
- ✅ All targets build successfully

### Test Validation:
- ✅ All tests pass (100% pass rate)
- ✅ No test regressions
- ✅ Coverage maintained or improved

### Quality Validation:
- ✅ No new clang-tidy issues
- ✅ Code style consistent
- ✅ Documentation adequate

### Performance Validation:
- ✅ No performance regressions
- ✅ Build time not significantly increased
- ✅ Test execution time stable

### Safety Validation:
- ✅ No memory leaks (Valgrind)
- ✅ No race conditions (Helgrind)
- ✅ No undefined behavior

## Output Format

Provide comprehensive validation report:

### Build Status
- Status: pass | fail
- Duration: X.Xs
- Warnings: N warnings (list if any)
- Errors: N errors (list if any)

### Test Results
- Status: pass | fail
- Total Tests: N
- Passed: N (X%)
- Failed: N (list failed test names)
- Duration: X.Xs

### Quality Metrics
- Clang-tidy: pass | fail (N issues)
- Code Coverage: X%
- Style Check: pass | fail

### Performance Metrics
- Build Time: X.Xs (vs baseline: ΔX.Xs)
- Test Time: X.Xs (vs baseline: ΔX.Xs)
- Binary Size: XMB (vs baseline: ΔX.XMB)

### Safety Verification
- Memory Leaks: N leaks found
- Race Conditions: N races found
- Issues: list if any

### Overall Assessment
- **Result**: PASS | FAIL
- **Recommendation**: proceed | revert | fix_issues
- **Blocking Issues**: list if any

{additional_guidelines}
""",

        TemplateType.OPTIMIZATION: """# Task: {task_description}

## Target: {target}

{context_section}

## Your Role

As the **{agent_name}** agent, your role is:
**{agent_role}**

### Expertise Areas:
{expertise_list}

## Optimization Focus

{optimization_focus}

## Optimization Opportunities

Analyze and identify optimization opportunities in these categories:

### 1. Algorithmic Optimization
- Time complexity improvements
- Space complexity improvements
- Better data structures

### 2. Low-Level Optimization
- SIMD vectorization (SSE2/AVX2/AVX-512)
- Cache optimization
- Branch prediction
- Memory alignment

### 3. Compiler Optimization
- Inlining opportunities
- Const correctness
- Move semantics
- Template specialization

### 4. I/O Optimization
- Buffered I/O
- Async I/O
- Batch operations
- Memory-mapped files

## Output Format

For each optimization opportunity, provide:

- **Category**: algorithmic | low_level | compiler | io
- **Location**: File:line reference
- **Current State**: Description of current implementation
- **Bottleneck**: What makes it slow
- **Proposed Optimization**: Specific optimization technique
- **Expected Speedup**: Estimated improvement (e.g., "10-50x faster")
- **Implementation Effort**: trivial | easy | medium | hard
- **Risk Level**: low | medium | high
- **Dependencies**: Required libraries/features
- **Code Example**: Before/after code snippets

Example:
```
Category: low_level
Location: safe_test.cpp:1200
Current State: Sequential data processing loop
Bottleneck: No SIMD vectorization, processes 1 element at a time
Proposed Optimization: AVX2 vectorization with 256-bit registers
Expected Speedup: 4-8x faster (processing 4-8 elements simultaneously)
Implementation Effort: medium
Risk Level: low
Dependencies: AVX2 support (already present)
Code Example:
  Before: for (i = 0; i < size; ++i) sum += data[i];
  After: Use _mm256_add_ps for SIMD parallel addition
```

{additional_guidelines}
"""
    }

    @classmethod
    def generate(
        cls,
        template_type: TemplateType,
        agent_name: str,
        task_description: str,
        target: str,
        context: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        Generate context-rich prompt from template.

        Args:
            template_type: Type of template to use
            agent_name: Name of agent receiving the prompt
            task_description: Description of the task
            target: Target file or component
            context: Context dictionary with previous findings
            **kwargs: Additional template variables

        Returns:
            Generated prompt string
        """
        template = cls.TEMPLATES.get(template_type, cls.TEMPLATES[TemplateType.ANALYSIS])

        # Build context section
        context_section = cls._build_context_section(context)

        # Get agent information
        agent_info = cls.AGENT_ROLES.get(agent_name, {
            "role": "Specialized analysis and improvement",
            "expertise": ["code analysis"],
            "output_focus": "Detailed findings with recommendations"
        })

        agent_role = agent_info["role"]
        expertise_list = "- " + "\n- ".join(agent_info["expertise"])
        output_focus = agent_info["output_focus"]

        # Build focus areas
        focus_areas = cls._build_focus_areas(context, kwargs.get("focus_areas"))

        # Build template-specific sections
        specific_sections = {}

        if template_type == TemplateType.FIXING:
            specific_sections["fixes_required"] = cls._build_fixes_section(context)
        elif template_type == TemplateType.VALIDATION:
            specific_sections["validation_checklist"] = cls._build_validation_checklist(context)
        elif template_type == TemplateType.OPTIMIZATION:
            specific_sections["optimization_focus"] = cls._build_optimization_focus(context)

        # Additional guidelines
        additional_guidelines = kwargs.get("additional_guidelines", "")

        return template.format(
            task_description=task_description,
            target=target,
            agent_name=agent_name,
            context_section=context_section,
            agent_role=agent_role,
            expertise_list=expertise_list,
            output_focus=output_focus,
            focus_areas=focus_areas,
            additional_guidelines=additional_guidelines,
            **specific_sections,
            **kwargs
        )

    @classmethod
    def _build_context_section(cls, context: Dict[str, Any]) -> str:
        """Build context section from previous agent findings."""
        if not context.get("previous_findings_summary"):
            return "## Context\n\nThis is the first agent in the workflow."

        parts = ["## Context from Previous Agents\n"]

        summary = context["previous_findings_summary"]
        parts.append(f"**Total agents executed**: {context.get('total_agents_executed', 0)}")
        parts.append(f"**Total findings**: {summary.get('total', 0)}")
        parts.append("")

        # Critical issues
        if critical_issues := context.get("critical_issues"):
            parts.append("### Critical Issues Identified:\n")
            for i, issue in enumerate(critical_issues[:5], 1):
                parts.append(f"{i}. **{issue['title']}** ({issue['location']})")
                parts.append(f"   {issue['description']}")
            parts.append("")

        # High priority areas
        if high_priority_areas := context.get("high_priority_areas"):
            parts.append("### High-Priority Code Areas:\n")
            for area in high_priority_areas[:10]:
                parts.append(f"- {area}")
            parts.append("")

        # Validated safe areas
        if validated_areas := context.get("validated_safe_areas"):
            parts.append("### Areas Validated as Safe:\n")
            for area in validated_areas[:5]:
                parts.append(f"- {area}")
            parts.append("")

        # Previous recommendations
        if prev_recommendations := context.get("recommendations_from_previous_agents"):
            parts.append("### Recommendations from Previous Agents:\n")
            for rec in prev_recommendations[:3]:
                parts.append(f"\n**{rec['agent']}**:")
                for r in rec['recommendations'][:3]:
                    parts.append(f"- {r}")
            parts.append("")

        return "\n".join(parts)

    @classmethod
    def _build_focus_areas(
        cls,
        context: Dict[str, Any],
        explicit_areas: Optional[List[str]]
    ) -> str:
        """Build focus areas section."""
        areas = explicit_areas or context.get("high_priority_areas", [])

        if not areas:
            return "Focus on comprehensive analysis of the entire target."

        parts = ["Priority focus areas based on previous findings:\n"]
        for area in areas[:10]:
            parts.append(f"- {area}")

        return "\n".join(parts)

    @classmethod
    def _build_fixes_section(cls, context: Dict[str, Any]) -> str:
        """Build fixes required section."""
        critical_issues = context.get("critical_issues", [])

        if not critical_issues:
            return "No critical issues identified. Focus on code quality improvements."

        parts = ["The following critical issues need fixing:\n"]
        for i, issue in enumerate(critical_issues[:10], 1):
            parts.append(f"{i}. **{issue['title']}** ({issue['location']})")
            parts.append(f"   - Problem: {issue['description']}")
            if issue.get('recommendation'):
                parts.append(f"   - Suggested Fix: {issue['recommendation']}")
            parts.append("")

        return "\n".join(parts)

    @classmethod
    def _build_validation_checklist(cls, context: Dict[str, Any]) -> str:
        """Build validation checklist."""
        parts = []

        # Add context-specific validation items
        if context.get("total_findings", 0) > 0:
            parts.append("- ✅ Verify all identified issues have been addressed")

        if context.get("critical_issues"):
            parts.append("- ✅ Confirm critical issues are fixed")

        if context.get("warnings_count", 0) > 0:
            parts.append(f"- ✅ Ensure warning count did not increase (baseline: {context['warnings_count']})")

        # Standard checklist
        parts.extend([
            "- ✅ Build completes successfully",
            "- ✅ All tests pass",
            "- ✅ No new warnings introduced",
            "- ✅ Code quality maintained or improved"
        ])

        return "\n".join(parts)

    @classmethod
    def _build_optimization_focus(cls, context: Dict[str, Any]) -> str:
        """Build optimization focus section."""
        parts = []

        # Add context-based focus
        if perf_issues := context.get("performance_issues", []):
            parts.append("### Performance Issues Identified:\n")
            for issue in perf_issues[:5]:
                parts.append(f"- {issue['location']}: {issue['description']}")
            parts.append("")

        # Standard focus
        parts.append("### General Optimization Targets:")
        parts.append("- Hot paths and frequently executed code")
        parts.append("- I/O operations and data processing loops")
        parts.append("- Memory-intensive operations")
        parts.append("- Cache-unfriendly access patterns")

        return "\n".join(parts)


def main():
    """Test prompt template generation."""
    print("=" * 80)
    print("Prompt Template System - Test")
    print("=" * 80)

    # Simulate context from previous agent
    context = {
        "total_agents_executed": 1,
        "previous_findings_summary": {
            "total": 47,
            "by_severity": {"critical": 3, "high": 5}
        },
        "critical_issues": [
            {
                "title": "Memory pool prefetch bug",
                "location": "safe_test.cpp:868",
                "description": "Unreachable code due to misplaced closing brace",
                "recommendation": "Move prefetch inside conditional block"
            }
        ],
        "high_priority_areas": [
            "safe_test.cpp:868",
            "safe_test.cpp:188",
            "safe_test.cpp:201"
        ]
    }

    # Generate analysis prompt
    print("\n" + "=" * 80)
    print("ANALYSIS PROMPT")
    print("=" * 80)

    prompt = PromptTemplate.generate(
        template_type=TemplateType.ANALYSIS,
        agent_name="clang-tidy-analyzer",
        task_description="Analyze safe_test.cpp for code quality issues",
        target="tests/unit/core/safe_test.cpp",
        context=context
    )

    print(prompt)

    print("\n" + "=" * 80)
    print("FIXING PROMPT")
    print("=" * 80)

    # Generate fixing prompt
    fixing_prompt = PromptTemplate.generate(
        template_type=TemplateType.FIXING,
        agent_name="clang-tidy-fixer",
        task_description="Fix critical issues in safe_test.cpp",
        target="tests/unit/core/safe_test.cpp",
        context=context
    )

    # Show first 50 lines
    print("\n".join(fixing_prompt.split('\n')[:50]))
    print("\n... (truncated for brevity)")


if __name__ == "__main__":
    main()