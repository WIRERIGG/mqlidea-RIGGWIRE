"""
Efficient Logical Error Detection Script

Uses awareness_orchestrator → mt5_infinite_reliability_agent integration
to find logical errors in MQL5 files efficiently and accurately.

Usage:
    python detect_logical_errors.py /path/to/file.mq5

Or as a module:
    from detect_logical_errors import detect_logical_errors
    await detect_logical_errors("/path/to/file.mq5")
"""

import asyncio
import re
import sys
import time
from pathlib import Path
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class LogicalErrorCategory(Enum):
    """Categories of logical errors to detect."""
    ARRAY_BOUNDS = "array_bounds"           # Array out-of-bounds access risks
    DIVISION_BY_ZERO = "division_by_zero"   # Division without zero check
    NULL_REFERENCE = "null_reference"       # Null pointer/handle usage
    INFINITE_LOOP = "infinite_loop"         # Loop termination issues
    STATE_INCONSISTENCY = "state_inconsistency"  # State management bugs
    RACE_CONDITION = "race_condition"       # Concurrent access issues
    OFF_BY_ONE = "off_by_one"               # Off-by-one errors in loops/arrays
    WRONG_OPERATOR = "wrong_operator"       # Using = instead of ==, etc.
    MISSING_RETURN = "missing_return"       # Missing return statements
    UNINITIALIZED = "uninitialized"         # Uninitialized variable usage
    BUFFER_MISMATCH = "buffer_mismatch"     # MQL5 buffer index mismatches
    HANDLE_LEAK = "handle_leak"             # Unreleased indicator handles
    TYPE_CONFUSION = "type_confusion"       # Type casting errors


@dataclass
class LogicalError:
    """Represents a detected logical error."""
    category: LogicalErrorCategory
    severity: str  # "critical", "high", "medium", "low"
    line_number: int
    code_snippet: str
    description: str
    recommendation: str


# ============================================================================
# PATTERN-BASED LOGICAL ERROR DETECTION (Fast, No LLM Required)
# ============================================================================

def fast_scan_for_logical_errors(code: str) -> List[LogicalError]:
    """
    Fast pattern-based scan for common logical errors.

    This runs locally without LLM calls for immediate feedback.
    Optimized for MQL5 idioms to reduce false positives.
    """
    errors = []
    lines = code.split('\n')

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments and empty lines
        if stripped.startswith('//') or not stripped:
            continue

        # 1. Array bounds: CopyBuffer without size validation
        # IMPROVED: MQL5 idiom "if(CopyBuffer(...) > 0)" is VALID
        if 'CopyBuffer' in line:
            # Check if it's properly validated with > 0 check
            if '> 0' in line or '>0' in line:
                continue  # This is the correct MQL5 idiom
            # Check for assignment to a variable that's checked later
            if 'copied' in line.lower() or '=' in line:
                context = '\n'.join(lines[max(0, i-1):min(len(lines), i+10)])
                if 'copied' in context.lower() or '> 0' in context or '>0' in context or '< 2' in context:
                    continue  # Validated later
            errors.append(LogicalError(
                category=LogicalErrorCategory.ARRAY_BOUNDS,
                severity="high",
                line_number=i,
                code_snippet=stripped,
                description="CopyBuffer without validating return value. May cause array out-of-bounds.",
                recommendation="Store CopyBuffer return in 'copied' and check 'if(copied < required) return;'"
            ))

        # 2. Division by zero risk
        if '/' in line and '0' not in line:
            # Look for division patterns
            div_match = re.search(r'/\s*(\w+)', line)
            if div_match:
                divisor = div_match.group(1)
                # Check if divisor is validated before
                context_before = '\n'.join(lines[max(0, i-5):i])
                if f'{divisor} == 0' not in context_before and f'{divisor} != 0' not in context_before:
                    if divisor not in ['100', '1000', '10000', '2', '3', '4', '5', '10']:  # Skip obvious constants
                        if not divisor.startswith('_'):  # Skip system variables
                            pass  # Too many false positives, skip this check

        # 3. Assignment in condition (= instead of ==)
        # IMPROVED: Skip Print statements and string literals
        if 'if' in line and '(' in line:
            # Skip if line contains Print (likely a Print with string containing '=')
            if 'Print' in line or '"' in line:
                pass  # Skip - likely a Print statement or string literal
            elif re.search(r'if\s*\(\s*[a-zA-Z_]\w*\s*=[^=]', line):
                # Pattern: if(varname = value) - likely an accidental assignment
                if '==' not in line and '!=' not in line and '<=' not in line and '>=' not in line:
                    errors.append(LogicalError(
                        category=LogicalErrorCategory.WRONG_OPERATOR,
                        severity="critical",
                        line_number=i,
                        code_snippet=stripped,
                        description="Assignment '=' found inside if condition. Should this be '=='?",
                        recommendation="Use '==' for comparison, not '=' (assignment)."
                    ))

        # 4. Array access without bounds check
        # IMPROVED: Check for loop guards and continue statements
        if re.search(r'\[\s*\w+\s*-\s*\d+\s*\]', line):
            # Negative offset array access
            match = re.search(r'(\w+)\[\s*(\w+)\s*-\s*(\d+)\s*\]', line)
            if match:
                array_name, index_var, offset = match.groups()
                offset_val = int(offset)
                # Check for bounds validation in surrounding context
                context_before = '\n'.join(lines[max(0, i-15):i])

                # MQL5 idioms to skip:
                # 1. Direct comparison: if(i >= 1), if(index >= 2)
                # 2. Loop guard: for(...; i >= 1; ...)
                # 3. Continue guard: if(i < 1) continue;
                # 4. EMPTY_VALUE check on same array access

                has_guard = False

                # Check for if(var >= offset) or if(var > offset-1)
                if re.search(rf'{index_var}\s*>=\s*{offset_val}', context_before):
                    has_guard = True
                elif re.search(rf'{index_var}\s*>\s*{offset_val - 1}', context_before):
                    has_guard = True
                # Check for continue guard: if(var < offset) continue;
                elif re.search(rf'if\s*\(\s*{index_var}\s*<\s*{offset_val}\s*\)\s*continue', context_before):
                    has_guard = True
                # Check for loop condition: for(...; var >= offset; ...)
                elif re.search(rf'for\s*\([^;]*;\s*{index_var}\s*>=\s*{offset_val}\s*;', context_before):
                    has_guard = True
                # Check for EMPTY_VALUE validation on [i-1] access
                elif f'{array_name}[{index_var}-{offset}] == EMPTY_VALUE' in context_before:
                    has_guard = True
                elif f'{array_name}[{index_var} - {offset}] == EMPTY_VALUE' in context_before:
                    has_guard = True

                if not has_guard:
                    errors.append(LogicalError(
                        category=LogicalErrorCategory.ARRAY_BOUNDS,
                        severity="high",
                        line_number=i,
                        code_snippet=stripped,
                        description=f"Array {array_name}[{index_var}-{offset}] accessed without visible bounds check.",
                        recommendation=f"Add: if({index_var} >= {offset}) before array access, or use 'if({index_var} < {offset}) continue;'"
                    ))

        # 5. Infinite loop detection (for loop without increment modification)
        if re.search(r'for\s*\([^;]*;[^;]*;\s*\)', line):
            errors.append(LogicalError(
                category=LogicalErrorCategory.INFINITE_LOOP,
                severity="critical",
                line_number=i,
                code_snippet=stripped,
                description="For loop with empty increment section. Potential infinite loop.",
                recommendation="Add loop variable modification in the for statement."
            ))

        # 6. Missing break in switch/case (MQL5 specific)
        if stripped.startswith('case ') and ':' in stripped:
            # Look ahead for break
            context_after = '\n'.join(lines[i:min(len(lines), i+15)])
            next_case = context_after.find('case ', 1)
            break_pos = context_after.find('break;')
            return_pos = context_after.find('return')

            if next_case > 0 and (break_pos < 0 or break_pos > next_case):
                if return_pos < 0 or return_pos > next_case:
                    pass  # Fall-through may be intentional, skip this

        # 7. INDICATOR_DATA vs INDICATOR_CALCULATIONS buffer mismatch
        if 'SetIndexBuffer' in line:
            match = re.search(r'SetIndexBuffer\s*\(\s*(\d+)', line)
            if match:
                buffer_index = int(match.group(1))
                # Check for INDICATOR_DATA usage
                if 'INDICATOR_CALCULATIONS' not in line and 'INDICATOR_COLOR_INDEX' not in line:
                    if 'INDICATOR_DATA' not in line:
                        errors.append(LogicalError(
                            category=LogicalErrorCategory.BUFFER_MISMATCH,
                            severity="medium",
                            line_number=i,
                            code_snippet=stripped,
                            description=f"SetIndexBuffer({buffer_index}) without explicit buffer type.",
                            recommendation="Specify buffer type: INDICATOR_DATA for plotted, INDICATOR_CALCULATIONS for internal."
                        ))

        # 8. Handle not released in OnDeinit
        if 'IndicatorRelease' in line:
            # Good - handles are being released
            pass
        elif 'OnDeinit' in line:
            # Check if this is the start of OnDeinit function
            context_after = '\n'.join(lines[i:min(len(lines), i+50)])
            if 'IndicatorRelease' not in context_after:
                # Check if there are indicator handles in the file
                full_code_before = '\n'.join(lines[:i])
                if 'iCustom' in full_code_before or 'iMA' in full_code_before or 'Handle' in full_code_before:
                    errors.append(LogicalError(
                        category=LogicalErrorCategory.HANDLE_LEAK,
                        severity="high",
                        line_number=i,
                        code_snippet=stripped,
                        description="OnDeinit exists but indicator handles may not be released.",
                        recommendation="Add IndicatorRelease() calls for all indicator handles in OnDeinit."
                    ))

        # 9. Color buffer without proper color index setup
        if 'ColorBuffer' in line and 'SetIndexBuffer' in line:
            if 'INDICATOR_COLOR_INDEX' not in line:
                errors.append(LogicalError(
                    category=LogicalErrorCategory.BUFFER_MISMATCH,
                    severity="medium",
                    line_number=i,
                    code_snippet=stripped,
                    description="Color buffer set without INDICATOR_COLOR_INDEX type.",
                    recommendation="Use SetIndexBuffer(N, ColorBuffer, INDICATOR_COLOR_INDEX);"
                ))

        # 10. Checking for uninitialized EMPTY_VALUE usage
        if 'EMPTY_VALUE' in line and '=' in line and '==' not in line:
            # This is an assignment to EMPTY_VALUE, check if array is initialized
            pass

    return errors


# ============================================================================
# DEEP LOGICAL ERROR DETECTION (Uses Agent Integration)
# ============================================================================

async def deep_scan_for_logical_errors(
    file_path: str,
    include_fast_scan: bool = True
) -> Dict[str, Any]:
    """
    Deep scan using awareness_orchestrator → mt5_infinite_reliability_agent.

    This leverages the full agent pipeline for comprehensive analysis.
    """
    start_time = time.time()

    # Read the file
    path = Path(file_path)
    if not path.exists():
        return {"success": False, "error": f"File not found: {file_path}"}

    code = path.read_text(encoding="utf-8")

    results = {
        "file_path": str(file_path),
        "file_name": path.name,
        "lines_analyzed": len(code.split('\n')),
        "fast_scan_errors": [],
        "deep_scan_errors": [],
        "recommendations": [],
        "success": True
    }

    # Phase 1: Fast local scan (no LLM)
    if include_fast_scan:
        fast_errors = fast_scan_for_logical_errors(code)
        results["fast_scan_errors"] = [
            {
                "category": e.category.value,
                "severity": e.severity,
                "line": e.line_number,
                "snippet": e.code_snippet[:100],
                "description": e.description,
                "recommendation": e.recommendation
            }
            for e in fast_errors
        ]
        results["fast_scan_count"] = len(fast_errors)

    # Phase 2: Deep agent-based analysis
    try:
        # Import the orchestrator
        from awareness_orchestrator.agent import orchestrate_mql5_file

        # Run the orchestration with MT5 agent as primary
        deep_result = await orchestrate_mql5_file(
            file_path=str(file_path),
            ftmo_compliance=True  # Always check FTMO compliance
        )

        if deep_result.get("success"):
            # Extract logical errors from MT5 analysis
            mt5_analysis = deep_result.get("mt5_analysis", {})
            if mt5_analysis and mt5_analysis.get("success"):
                result_data = mt5_analysis.get("result", {})
                if isinstance(result_data, dict):
                    # Extract issues classified as logical errors
                    issues = result_data.get("issues", [])
                    for issue in issues:
                        if is_logical_error(issue):
                            results["deep_scan_errors"].append(issue)

            # Also extract recommendations
            results["recommendations"] = deep_result.get("recommendations", [])

        results["deep_scan_count"] = len(results["deep_scan_errors"])

    except ImportError as e:
        results["deep_scan_warning"] = f"Agent import failed: {e}. Using fast scan only."
    except Exception as e:
        results["deep_scan_warning"] = f"Agent analysis failed: {e}. Using fast scan only."

    # Calculate totals
    results["total_errors"] = (
        results.get("fast_scan_count", 0) +
        results.get("deep_scan_count", 0)
    )
    results["duration"] = time.time() - start_time

    return results


def is_logical_error(issue: dict) -> bool:
    """Determine if an issue is a logical error vs style/performance."""
    if not isinstance(issue, dict):
        return False

    logical_keywords = [
        "array", "bounds", "index", "division", "zero", "null", "uninitialized",
        "infinite", "loop", "condition", "operator", "return", "buffer", "handle",
        "leak", "race", "state", "inconsist", "mismatch", "off-by", "overflow"
    ]

    message = str(issue.get("message", "")).lower()
    description = str(issue.get("description", "")).lower()
    category = str(issue.get("category", "")).lower()

    combined = f"{message} {description} {category}"

    return any(keyword in combined for keyword in logical_keywords)


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

async def detect_logical_errors(
    file_path: str,
    mode: str = "fast"  # "fast", "deep", or "full"
) -> Dict[str, Any]:
    """
    Main entry point for logical error detection.

    Args:
        file_path: Path to MQL5 file to analyze
        mode:
            - "fast": Local pattern matching only (instant)
            - "deep": Agent-based analysis only
            - "full": Both fast and deep analysis

    Returns:
        Dictionary with detected errors and recommendations
    """
    if mode == "fast":
        path = Path(file_path)
        if not path.exists():
            return {"success": False, "error": f"File not found: {file_path}"}

        code = path.read_text(encoding="utf-8")
        errors = fast_scan_for_logical_errors(code)

        return {
            "file_path": str(file_path),
            "mode": "fast",
            "errors": [
                {
                    "category": e.category.value,
                    "severity": e.severity,
                    "line": e.line_number,
                    "snippet": e.code_snippet[:100],
                    "description": e.description,
                    "recommendation": e.recommendation
                }
                for e in errors
            ],
            "total_errors": len(errors),
            "success": True
        }

    elif mode == "deep":
        return await deep_scan_for_logical_errors(file_path, include_fast_scan=False)

    else:  # full
        return await deep_scan_for_logical_errors(file_path, include_fast_scan=True)


def format_report(results: Dict[str, Any]) -> str:
    """Format results into a readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("LOGICAL ERROR DETECTION REPORT")
    lines.append("=" * 70)
    lines.append(f"File: {results.get('file_path', 'unknown')}")
    lines.append(f"Mode: {results.get('mode', 'full')}")
    lines.append(f"Lines analyzed: {results.get('lines_analyzed', 'N/A')}")
    lines.append(f"Duration: {results.get('duration', 0):.2f}s")
    lines.append("")

    # Fast scan results
    fast_errors = results.get("fast_scan_errors", results.get("errors", []))
    if fast_errors:
        lines.append("-" * 70)
        lines.append(f"PATTERN-BASED ERRORS FOUND: {len(fast_errors)}")
        lines.append("-" * 70)
        for i, error in enumerate(fast_errors, 1):
            severity = error.get("severity", "unknown").upper()
            lines.append(f"\n[{i}] [{severity}] {error.get('category', 'unknown')}")
            lines.append(f"    Line {error.get('line', '?')}: {error.get('snippet', '')[:60]}")
            lines.append(f"    Issue: {error.get('description', 'No description')}")
            lines.append(f"    Fix: {error.get('recommendation', 'No recommendation')}")

    # Deep scan results
    deep_errors = results.get("deep_scan_errors", [])
    if deep_errors:
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"AGENT-DETECTED ERRORS: {len(deep_errors)}")
        lines.append("-" * 70)
        for i, error in enumerate(deep_errors, 1):
            lines.append(f"\n[{i}] {error}")

    # Recommendations
    recommendations = results.get("recommendations", [])
    if recommendations:
        lines.append("")
        lines.append("-" * 70)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 70)
        for rec in recommendations[:10]:
            if isinstance(rec, dict):
                lines.append(f"- [{rec.get('priority', 'N/A')}] {rec.get('recommendation', str(rec))}")
            else:
                lines.append(f"- {rec}")

    # Summary
    lines.append("")
    lines.append("=" * 70)
    total = results.get("total_errors", len(fast_errors))
    lines.append(f"TOTAL LOGICAL ERRORS: {total}")
    if total == 0:
        lines.append("No logical errors detected!")
    elif total < 5:
        lines.append("Status: Minor issues found. Review and fix.")
    else:
        lines.append("Status: SIGNIFICANT ISSUES. Prioritize fixing critical/high severity items.")
    lines.append("=" * 70)

    return "\n".join(lines)


# ============================================================================
# CLI ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python detect_logical_errors.py <file.mq5> [mode]")
        print("Modes: fast (default), deep, full")
        sys.exit(1)

    file_path = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "fast"

    print(f"Scanning {file_path} for logical errors (mode: {mode})...")

    results = asyncio.run(detect_logical_errors(file_path, mode))

    if results.get("success"):
        print(format_report(results))
    else:
        print(f"Error: {results.get('error', 'Unknown error')}")
        sys.exit(1)
