"""
Tool implementations for Multi-Agent Debugging System.
"""

import asyncio
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from pydantic_ai import RunContext

from .dependencies import AgentDependencies, ToolResult, ToolType, AnalysisMode
from .settings import settings


async def run_debugging_tool(
    ctx: RunContext[AgentDependencies],
    tool_name: str,
    target_path: str,
    tool_args: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Execute a C++ debugging tool and return structured results.

    Args:
        ctx: Runtime context with dependencies
        tool_name: Name of the debugging tool to run
        target_path: Path to the target file/binary
        tool_args: Optional additional arguments for the tool

    Returns:
        Dictionary with execution results and structured findings
    """
    start_time = time.time()
    tool_args = tool_args or []

    try:
        # Get tool-specific command configuration
        command, tool_specific_args = _get_tool_command(tool_name, target_path, tool_args)

        # Execute the tool with timeout
        process = await asyncio.create_subprocess_exec(
            *command,
            *tool_specific_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=ctx.deps.context.output_dir
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=settings.analysis_timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            raise subprocess.TimeoutExpired(command[0], settings.analysis_timeout)

        execution_time = time.time() - start_time

        # Parse tool output and extract issues
        issues_found = _parse_tool_output(tool_name, stdout.decode(), stderr.decode())

        # Create tool result
        result = ToolResult(
            tool_name=tool_name,
            command=" ".join(command + tool_specific_args),
            exit_code=process.returncode,
            stdout=stdout.decode(),
            stderr=stderr.decode(),
            execution_time=execution_time,
            issues_found=issues_found,
            success=process.returncode == 0 or len(issues_found) > 0,  # Some tools return non-zero when finding issues
            error_message=None
        )

        # Cache the result
        await ctx.deps.cache_result(tool_name, result)

        return {
            "tool_name": tool_name,
            "success": result.success,
            "execution_time": execution_time,
            "issues_count": len(issues_found),
            "issues": issues_found,
            "raw_output": stdout.decode(),
            "command": result.command
        }

    except Exception as e:
        execution_time = time.time() - start_time
        error_result = ToolResult(
            tool_name=tool_name,
            command=f"Failed to execute {tool_name}",
            exit_code=-1,
            stdout="",
            stderr="",
            execution_time=execution_time,
            issues_found=[],
            success=False,
            error_message=str(e)
        )

        await ctx.deps.cache_result(tool_name, error_result)

        return {
            "tool_name": tool_name,
            "success": False,
            "execution_time": execution_time,
            "error": str(e),
            "issues": []
        }


async def correlate_findings(
    ctx: RunContext[AgentDependencies],
    tool_results: List[Dict[str, Any]],
    correlation_threshold: float = 0.7,
    priority_mode: str = "severity"
) -> Dict[str, Any]:
    """
    Advanced correlation of findings across multiple debugging tools with sophisticated pattern recognition.

    Args:
        ctx: Runtime context with dependencies
        tool_results: List of tool execution results
        correlation_threshold: Minimum confidence for correlation
        priority_mode: Prioritization method (severity, confidence, consensus, smart)

    Returns:
        Dictionary with correlated findings and intelligent recommendations
    """
    start_time = time.time()

    try:
        # Extract and enrich all issues from tool results
        all_issues = []
        tool_coverage = {}
        for result in tool_results:
            tool_name = result["tool_name"]
            tool_coverage[tool_name] = {
                "success": result.get("success", False),
                "execution_time": result.get("execution_time", 0),
                "issues_count": result.get("issues_count", 0)
            }

            if result.get("success", False):
                for issue in result.get("issues", []):
                    # Enrich issue with metadata
                    enriched_issue = {
                        **issue,
                        "source_tool": tool_name,
                        "tool_type": _get_tool_type(tool_name),
                        "discovery_time": time.time(),
                        "semantic_hash": _calculate_semantic_hash(issue)
                    }
                    all_issues.append(enriched_issue)

        # Advanced pattern recognition and grouping
        issue_groups = _advanced_issue_grouping(all_issues, correlation_threshold)

        # Multi-dimensional prioritization
        prioritized_groups = _advanced_prioritization(issue_groups, priority_mode, tool_coverage)

        # Generate intelligent recommendations
        recommendations = _generate_intelligent_recommendations(prioritized_groups, tool_coverage)

        # Calculate advanced metrics
        metrics = _calculate_advanced_metrics(prioritized_groups, tool_coverage, all_issues)

        execution_time = time.time() - start_time

        return {
            "correlation_success": True,
            "execution_time": execution_time,
            "total_raw_issues": len(all_issues),
            "correlated_groups": len(issue_groups),
            "high_priority_issues": len([g for g in prioritized_groups if g["priority"] == "critical"]),
            "critical_chain_issues": len([g for g in prioritized_groups if g.get("is_chain_critical", False)]),
            "issue_groups": prioritized_groups,
            "recommendations": recommendations,
            "tool_coverage": tool_coverage,
            "advanced_metrics": metrics,
            "correlation_matrix": _build_correlation_matrix(issue_groups),
            "summary": {
                "critical_issues": len([g for g in prioritized_groups if g["severity"] == "critical"]),
                "security_issues": len([g for g in prioritized_groups if g.get("category") in ["buffer_overflow", "memory_error", "injection"]]),
                "performance_issues": len([g for g in prioritized_groups if "performance" in g.get("category", "").lower()]),
                "tools_consensus": _calculate_tool_consensus(issue_groups),
                "confidence_score": _calculate_overall_confidence(prioritized_groups),
                "risk_score": metrics.get("overall_risk_score", 0.0)
            }
        }

    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "correlation_success": False,
            "execution_time": execution_time,
            "error": str(e),
            "issue_groups": [],
            "recommendations": []
        }


async def compile_source(
    ctx: RunContext[AgentDependencies],
    source_path: str,
    build_type: str = "debug",
    additional_flags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compile C++ source code for dynamic analysis.

    Args:
        ctx: Runtime context with dependencies
        source_path: Path to source file or directory
        build_type: Build configuration (debug, release, analysis)
        additional_flags: Additional compiler flags

    Returns:
        Dictionary with compilation results
    """
    start_time = time.time()
    additional_flags = additional_flags or []

    try:
        source_path_obj = Path(source_path)

        # Determine build method
        if source_path_obj.name == "CMakeLists.txt" or (source_path_obj / "CMakeLists.txt").exists():
            result = await _compile_with_cmake(source_path, build_type, additional_flags, ctx)
        elif source_path_obj.name == "Makefile" or (source_path_obj / "Makefile").exists():
            result = await _compile_with_make(source_path, build_type, additional_flags, ctx)
        else:
            result = await _compile_direct(source_path, build_type, additional_flags, ctx)

        execution_time = time.time() - start_time
        result["execution_time"] = execution_time

        # Update context with compiled binary path
        if result["success"] and result.get("binary_path"):
            ctx.deps.context.compiled_binary = result["binary_path"]

        return result

    except Exception as e:
        execution_time = time.time() - start_time
        return {
            "success": False,
            "execution_time": execution_time,
            "error": str(e),
            "binary_path": None,
            "build_log": ""
        }


def _get_tool_command(tool_name: str, target_path: str, args: List[str]) -> Tuple[List[str], List[str]]:
    """Get command and arguments for a specific debugging tool."""
    tool_configs = {
        # Advanced GDB with comprehensive debugging
        "gdb": ([settings.gdb_path], [
            "--batch", "--quiet", "--return-child-result",
            "--ex", "set logging on",
            "--ex", "set logging file gdb_analysis.log",
            "--ex", "set logging overwrite on",
            "--ex", "set print pretty on",
            "--ex", "set print array on",
            "--ex", "set print array-indexes on",
            "--ex", "set print elements 0",
            "--ex", "handle SIGSEGV stop print",
            "--ex", "handle SIGABRT stop print",
            "--ex", "handle SIGFPE stop print",
            "--ex", "run",
            "--ex", "thread apply all bt full",
            "--ex", "info registers",
            "--ex", "info frame",
            "--ex", "info locals",
            "--ex", "info args",
            "--ex", "disassemble",
            "--ex", "x/32xb $rsp",
            "--ex", "info proc mappings",
            "--ex", "maintenance info sections",
            "--args", target_path
        ] + args),

        # Advanced GDB with core dump analysis
        "gdb-core": ([settings.gdb_path], [
            "--batch", "--quiet",
            "--ex", "set logging on",
            "--ex", "set logging file gdb_core_analysis.log",
            "--ex", "thread apply all bt full",
            "--ex", "info registers",
            "--ex", "info sharedlibrary",
            "--ex", "info proc mappings",
            "--ex", "print $_siginfo",
            "--core", "core", target_path
        ]),

        # Comprehensive Strace with detailed syscall analysis
        "strace": ([settings.strace_path], [
            "-f", "-tt", "-T", "-y", "-yy", "-s", "1024",
            "-e", "trace=all",
            "-e", "signal=all",
            "-e", "status=successful,failed",
            "-o", "strace_detailed.log",
            target_path
        ] + args),

        "strace-memory": ([settings.strace_path], [
            "-f", "-tt", "-T", "-y", "-s", "1024",
            "-e", "trace=memory,mmap,munmap,mprotect,brk,sbrk",
            "-o", "strace_memory.log",
            target_path
        ] + args),

        "strace-io": ([settings.strace_path], [
            "-f", "-tt", "-T", "-y", "-s", "1024",
            "-e", "trace=read,write,open,close,openat,lseek,pread,pwrite",
            "-o", "strace_io.log",
            target_path
        ] + args),

        # Advanced Ltrace with comprehensive library tracking
        "ltrace": ([settings.ltrace_path], [
            "-f", "-tt", "-T", "-n", "4", "-s", "1024",
            "-e", "*",
            "-o", "ltrace_detailed.log",
            target_path
        ] + args),

        "ltrace-malloc": ([settings.ltrace_path], [
            "-f", "-tt", "-T", "-s", "1024",
            "-e", "malloc,calloc,realloc,free,new,delete",
            "-o", "ltrace_memory.log",
            target_path
        ] + args),

        # Advanced Perf with comprehensive profiling
        "perf": ([settings.perf_path], ["stat", "-d", "-d", "-d", target_path] + args),

        "perf-record": ([settings.perf_path], [
            "record", "-g", "--call-graph=dwarf",
            "-e", "cycles,instructions,cache-misses,branch-misses,page-faults",
            "-o", "perf_profile.data",
            target_path
        ] + args),

        "perf-mem": ([settings.perf_path], [
            "mem", "record", "-a", "-d",
            "-e", "cpu/mem-loads,ldlat=30/P,cpu/mem-stores/P",
            target_path
        ] + args),

        # Comprehensive Valgrind suite
        "valgrind": ([settings.valgrind_path], [
            "--tool=memcheck",
            "--leak-check=full",
            "--show-leak-kinds=all",
            "--track-origins=yes",
            "--track-fds=yes",
            "--show-reachable=yes",
            "--num-callers=30",
            "--verbose",
            "--xml=yes",
            "--xml-file=valgrind_memcheck.xml",
            target_path
        ] + args),

        "valgrind-cachegrind": ([settings.valgrind_path], [
            "--tool=cachegrind",
            "--cache-sim=yes",
            "--branch-sim=yes",
            "--cachegrind-out-file=cachegrind.out",
            target_path
        ] + args),

        "valgrind-callgrind": ([settings.valgrind_path], [
            "--tool=callgrind",
            "--collect-jumps=yes",
            "--collect-systime=yes",
            "--callgrind-out-file=callgrind.out",
            target_path
        ] + args),

        "valgrind-massif": ([settings.valgrind_path], [
            "--tool=massif",
            "--heap=yes",
            "--stacks=yes",
            "--detailed-freq=1",
            "--max-snapshots=1000",
            "--massif-out-file=massif.out",
            target_path
        ] + args),

        "valgrind-helgrind": ([settings.valgrind_path], [
            "--tool=helgrind",
            "--track-lockorders=yes",
            "--history-level=full",
            "--conflict-cache-size=2000000",
            target_path
        ] + args),

        "valgrind-drd": ([settings.valgrind_path], [
            "--tool=drd",
            "--check-stack-var=yes",
            "--track-lockorders=yes",
            "--exclusive-threshold=10",
            target_path
        ] + args),

        # Enhanced Cppcheck with maximum analysis
        "cppcheck": ([settings.cppcheck_path], [
            "--enable=all",
            "--inconclusive",
            "--std=c++20",
            "--platform=unix64",
            "--check-config",
            "--check-library",
            "--addon=misra",
            "--addon=cert",
            "--addon=threadsafety",
            "--json",
            "--output-file=cppcheck_results.json",
            "--cppcheck-build-dir=cppcheck_build",
            "--max-ctu-depth=10",
            "--project=" + target_path if target_path.endswith('.json') else target_path
        ] + args),

        # Advanced Clang-tidy with comprehensive checks using project configuration
        "clang-tidy": ([settings.clang_tidy_path], [
            "--config-file=.clang-tidy",  # Use project's .clang-tidy configuration
            "--header-filter=.*",
            "--format-style=file",
            "--export-fixes=clang_tidy_fixes.yaml",
            "--extra-arg=-std=c++23",  # Updated to C++23 as per project settings
            "--extra-arg=-Wall",
            "--extra-arg=-Wextra",
            target_path,
            "--"
        ] + args),

        # Advanced sanitizer combinations
        "asan": ([settings.compiler], [
            "-fsanitize=address,undefined,leak",
            "-fsanitize-address-use-after-scope",
            "-fsanitize-recover=undefined",
            "-fno-sanitize-recover=address",
            "-fstack-protector-strong",
            "-g3", "-O1", "-fno-omit-frame-pointer",
            "-fno-optimize-sibling-calls",
            "-DASAN_OPTIONS=detect_leaks=1:halt_on_error=1:abort_on_error=1",
            "-o", f"{target_path}_asan", target_path
        ]),

        "msan": ([settings.compiler], [
            "-fsanitize=memory",
            "-fsanitize-memory-track-origins=2",
            "-g3", "-O1", "-fno-omit-frame-pointer",
            "-o", f"{target_path}_msan", target_path
        ]),

        "ubsan": ([settings.compiler], [
            "-fsanitize=undefined,nullability,integer,bounds",
            "-fsanitize-recover=undefined",
            "-g3", "-O1",
            "-o", f"{target_path}_ubsan", target_path
        ]),

        "tsan": ([settings.compiler], [
            "-fsanitize=thread",
            "-g3", "-O1",
            "-o", f"{target_path}_tsan", target_path
        ]),

        # Coverage analysis
        "gcov": ([settings.compiler], [
            "-fprofile-arcs", "-ftest-coverage",
            "-g3", "-O0",
            "-o", f"{target_path}_gcov", target_path
        ]),

        # Custom project integrations
        "ai-clang-tidy": (["bash"], [_find_project_script("ai_clang_tidy.sh"), "analyze", target_path]),
        "build-safety": (["bash"], [_find_project_script("build_safety_check.sh")])
    }

    if tool_name not in tool_configs:
        raise ValueError(f"Unknown tool: {tool_name}")

    return tool_configs[tool_name]


def _find_project_script(script_name: str) -> str:
    """Find a project script by walking up the directory tree."""
    current_dir = Path.cwd()
    while current_dir.parent != current_dir:
        script_path = current_dir / "scripts" / script_name
        if script_path.exists():
            return str(script_path)
        if (current_dir / "CLAUDE.md").exists():
            break  # Found project root
        current_dir = current_dir.parent
    raise FileNotFoundError(f"Script {script_name} not found in project")


def _parse_tool_output(tool_name: str, stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse tool output and extract structured issues with maximum detail extraction."""
    issues = []

    if tool_name == "cppcheck":
        # Parse cppcheck JSON output
        try:
            if stdout.strip():
                data = json.loads(stdout)
                for error in data.get("errors", []):
                    issues.append({
                        "severity": error.get("severity", "unknown"),
                        "message": error.get("message", ""),
                        "file": error.get("file", ""),
                        "line": error.get("line", 0),
                        "id": error.get("id", ""),
                        "confidence": 0.9
                    })
        except json.JSONDecodeError:
            # Fallback to text parsing
            for line in stdout.split('\n'):
                if '[' in line and ']' in line:
                    issues.append({
                        "severity": "medium",
                        "message": line.strip(),
                        "confidence": 0.7
                    })

    elif tool_name == "clang-tidy":
        # Parse clang-tidy output
        for line in stdout.split('\n'):
            if 'warning:' in line or 'error:' in line:
                issues.append({
                    "severity": "high" if "error:" in line else "medium",
                    "message": line.strip(),
                    "confidence": 0.8
                })

    elif tool_name == "valgrind":
        # Parse valgrind output for memory issues
        for line in stderr.split('\n'):
            if 'definitely lost:' in line or 'possibly lost:' in line:
                if not line.strip().endswith("0 bytes in 0 blocks"):
                    issues.append({
                        "severity": "high",
                        "message": line.strip(),
                        "category": "memory_leak",
                        "confidence": 0.95
                    })

    elif tool_name == "gdb":
        # Parse GDB backtrace output
        for line in stdout.split('\n'):
            if 'Segmentation fault' in line or 'SIGSEGV' in line:
                issues.append({
                    "severity": "critical",
                    "message": line.strip(),
                    "category": "segfault",
                    "confidence": 1.0
                })

    elif tool_name in ["asan", "ubsan", "tsan"]:
        # Parse sanitizer outputs
        output_text = stderr + stdout  # Sanitizers often output to stderr

        if "AddressSanitizer" in output_text or tool_name == "asan":
            for line in output_text.split('\n'):
                if 'ERROR: AddressSanitizer:' in line:
                    issues.append({
                        "severity": "critical",
                        "message": line.strip(),
                        "category": "memory_error",
                        "confidence": 0.98
                    })
                elif 'heap-buffer-overflow' in line or 'stack-buffer-overflow' in line:
                    issues.append({
                        "severity": "critical",
                        "message": line.strip(),
                        "category": "buffer_overflow",
                        "confidence": 0.95
                    })

        if "UndefinedBehaviorSanitizer" in output_text or tool_name == "ubsan":
            for line in output_text.split('\n'):
                if 'runtime error:' in line:
                    issues.append({
                        "severity": "high",
                        "message": line.strip(),
                        "category": "undefined_behavior",
                        "confidence": 0.90
                    })

        if "ThreadSanitizer" in output_text or tool_name == "tsan":
            for line in output_text.split('\n'):
                if 'WARNING: ThreadSanitizer:' in line:
                    issues.append({
                        "severity": "high",
                        "message": line.strip(),
                        "category": "data_race",
                        "confidence": 0.92
                    })

    elif tool_name.startswith("gdb"):
        # Advanced GDB parsing with comprehensive crash analysis
        issues.extend(_parse_gdb_output(stdout, stderr, tool_name))

    elif tool_name.startswith("strace"):
        # Advanced strace parsing for syscall analysis
        issues.extend(_parse_strace_output(stdout, stderr, tool_name))

    elif tool_name.startswith("ltrace"):
        # Advanced ltrace parsing for library call analysis
        issues.extend(_parse_ltrace_output(stdout, stderr, tool_name))

    elif tool_name.startswith("perf"):
        # Advanced perf parsing for performance analysis
        issues.extend(_parse_perf_output(stdout, stderr, tool_name))

    elif tool_name.startswith("valgrind"):
        # Enhanced valgrind parsing for all tools
        issues.extend(_parse_valgrind_output(stdout, stderr, tool_name))

    elif tool_name == "msan":
        # MemorySanitizer output parsing
        for line in (stderr + stdout).split('\n'):
            if 'MemorySanitizer:' in line:
                issues.append({
                    "severity": "critical",
                    "message": line.strip(),
                    "category": "uninitialized_memory",
                    "confidence": 0.95
                })

    elif tool_name == "gcov":
        # Coverage analysis parsing
        issues.extend(_parse_coverage_output(stdout, stderr))

    elif tool_name == "ai-clang-tidy":
        # Parse AI-enhanced clang-tidy output
        for line in stdout.split('\n'):
            if 'AI-ENHANCED:' in line or 'RECOMMENDATION:' in line:
                issues.append({
                    "severity": "medium",
                    "message": line.strip(),
                    "category": "ai_recommendation",
                    "confidence": 0.85
                })
            elif 'CRITICAL:' in line:
                issues.append({
                    "severity": "critical",
                    "message": line.strip(),
                    "category": "ai_critical",
                    "confidence": 0.90
                })

    elif tool_name == "build-safety":
        # Parse build safety checker output
        for line in stdout.split('\n'):
            if 'SAFETY VIOLATION:' in line:
                issues.append({
                    "severity": "high",
                    "message": line.strip(),
                    "category": "build_safety",
                    "confidence": 0.88
                })

    # Generic parsing for other tools
    else:
        # Look for common error patterns
        error_patterns = [
            ("error", "high", 0.8),
            ("warning", "medium", 0.6),
            ("leak", "high", 0.9),
            ("undefined", "medium", 0.7),
            ("overflow", "high", 0.9)
        ]

        for line in (stdout + stderr).split('\n'):
            line_lower = line.lower()
            for pattern, severity, confidence in error_patterns:
                if pattern in line_lower:
                    issues.append({
                        "severity": severity,
                        "message": line.strip(),
                        "confidence": confidence
                    })
                    break

    return issues


def _group_similar_issues(issues: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """Group similar issues together for correlation."""
    groups = []

    for issue in issues:
        # Find existing group for this issue
        grouped = False
        for group in groups:
            # Simple similarity based on message content and location
            similarity = _calculate_similarity(issue, group["representative"])
            if similarity >= threshold:
                group["issues"].append(issue)
                group["tool_consensus"].add(issue["source_tool"])
                grouped = True
                break

        if not grouped:
            # Create new group
            groups.append({
                "representative": issue,
                "issues": [issue],
                "tool_consensus": {issue["source_tool"]},
                "confidence": issue.get("confidence", 0.5)
            })

    return groups


def _calculate_similarity(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> float:
    """Calculate similarity between two issues."""
    # Simple similarity based on message and location
    score = 0.0

    # Check message similarity (simple word overlap)
    msg1_words = set(issue1.get("message", "").lower().split())
    msg2_words = set(issue2.get("message", "").lower().split())
    if msg1_words and msg2_words:
        overlap = len(msg1_words & msg2_words)
        total = len(msg1_words | msg2_words)
        score += 0.6 * (overlap / total) if total > 0 else 0

    # Check location similarity
    if issue1.get("file") == issue2.get("file"):
        score += 0.2
        line_diff = abs(issue1.get("line", 0) - issue2.get("line", 0))
        if line_diff <= 5:  # Same or nearby lines
            score += 0.2

    return min(score, 1.0)


def _prioritize_issue_groups(groups: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    """Prioritize issue groups based on specified criteria."""
    severity_order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

    for group in groups:
        # Calculate group priority
        max_severity = max(
            (severity_order.get(issue.get("severity", "low"), 1) for issue in group["issues"]),
            default=1
        )

        # Convert back to severity name
        severity_names = {v: k for k, v in severity_order.items()}
        group["severity"] = severity_names.get(max_severity, "low")

        # Calculate consensus score
        tool_count = len(group["tool_consensus"])
        group["consensus_score"] = tool_count / 7.0  # Normalize by total tool count

        # Assign priority
        if max_severity >= 3 and tool_count >= 2:
            group["priority"] = "high"
        elif max_severity >= 2 or tool_count >= 2:
            group["priority"] = "medium"
        else:
            group["priority"] = "low"

    # Sort by priority and confidence
    return sorted(groups, key=lambda g: (
        {"high": 3, "medium": 2, "low": 1}[g["priority"]],
        g["consensus_score"],
        g["confidence"]
    ), reverse=True)


def _generate_recommendations(groups: List[Dict[str, Any]]) -> List[str]:
    """Generate actionable recommendations from issue groups."""
    recommendations = []

    # Focus on high-priority groups
    high_priority = [g for g in groups if g["priority"] == "high"]

    if high_priority:
        recommendations.append(f"Address {len(high_priority)} critical issues with multi-tool consensus")

    # Memory-related recommendations
    memory_issues = [g for g in groups if any("leak" in i.get("message", "").lower() for i in g["issues"])]
    if memory_issues:
        recommendations.append("Review memory management: potential leaks detected by multiple tools")

    # Security recommendations
    security_keywords = ["overflow", "underflow", "injection", "vulnerability"]
    security_issues = [g for g in groups if any(
        any(keyword in i.get("message", "").lower() for keyword in security_keywords)
        for i in g["issues"]
    )]
    if security_issues:
        recommendations.append("Security review required: potential vulnerabilities detected")

    # Performance recommendations
    if any("perf" in g["tool_consensus"] for g in groups):
        recommendations.append("Performance optimization opportunities identified")

    return recommendations[:10]  # Limit to top 10 recommendations


def _calculate_tool_consensus(groups: List[Dict[str, Any]]) -> float:
    """Calculate overall tool consensus score."""
    if not groups:
        return 0.0

    total_consensus = sum(len(g["tool_consensus"]) for g in groups)
    max_possible = len(groups) * 7  # 7 tools max
    return total_consensus / max_possible if max_possible > 0 else 0.0


def _calculate_overall_confidence(groups: List[Dict[str, Any]]) -> float:
    """Calculate overall confidence score."""
    if not groups:
        return 0.0

    return sum(g["confidence"] for g in groups) / len(groups)


async def _compile_with_cmake(source_path: str, build_type: str, flags: List[str], ctx) -> Dict[str, Any]:
    """Compile using CMake."""
    build_dir = Path(ctx.deps.context.output_dir) / "cmake_build"
    build_dir.mkdir(exist_ok=True)

    # Configure
    configure_cmd = ["cmake", "-S", source_path, "-B", str(build_dir), f"-DCMAKE_BUILD_TYPE={build_type.title()}"]
    process = await asyncio.create_subprocess_exec(*configure_cmd, capture_output=True)
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        return {
            "success": False,
            "error": f"CMake configuration failed: {stderr.decode()}",
            "build_log": stdout.decode() + stderr.decode()
        }

    # Build
    build_cmd = ["cmake", "--build", str(build_dir)]
    process = await asyncio.create_subprocess_exec(*build_cmd, capture_output=True)
    stdout, stderr = await process.communicate()

    success = process.returncode == 0
    binary_path = None
    if success:
        # Find the built binary
        for item in build_dir.rglob("*"):
            if item.is_file() and item.stat().st_mode & 0o111:  # Executable
                binary_path = str(item)
                break

    return {
        "success": success,
        "binary_path": binary_path,
        "build_log": stdout.decode() + stderr.decode()
    }


async def _compile_with_make(source_path: str, build_type: str, flags: List[str], ctx) -> Dict[str, Any]:
    """Compile using Make."""
    process = await asyncio.create_subprocess_exec(
        "make", "-C", source_path,
        capture_output=True
    )
    stdout, stderr = await process.communicate()

    success = process.returncode == 0
    binary_path = None
    if success:
        # Look for common binary names
        source_dir = Path(source_path)
        for name in ["main", "a.out", source_dir.name]:
            potential_binary = source_dir / name
            if potential_binary.exists() and potential_binary.stat().st_mode & 0o111:
                binary_path = str(potential_binary)
                break

    return {
        "success": success,
        "binary_path": binary_path,
        "build_log": stdout.decode() + stderr.decode()
    }


async def _compile_direct(source_path: str, build_type: str, flags: List[str], ctx) -> Dict[str, Any]:
    """Direct compilation with g++."""
    source_path_obj = Path(source_path)
    output_path = Path(ctx.deps.context.output_dir) / f"{source_path_obj.stem}_debug"

    compile_flags = ["-g", "-O0"] if build_type == "debug" else ["-O2"]
    compile_flags.extend(flags)

    cmd = [settings.compiler] + compile_flags + ["-o", str(output_path), source_path]

    process = await asyncio.create_subprocess_exec(*cmd, capture_output=True)
    stdout, stderr = await process.communicate()

    success = process.returncode == 0

    return {
        "success": success,
        "binary_path": str(output_path) if success else None,
        "build_log": stdout.decode() + stderr.decode()
    }


# Advanced Correlation and Prioritization Functions

def _get_tool_type(tool_name: str) -> str:
    """Classify tool by analysis type."""
    static_tools = ["cppcheck", "clang-tidy", "ai-clang-tidy", "build-safety"]
    dynamic_tools = ["gdb", "valgrind", "asan", "ubsan", "tsan"]
    profiling_tools = ["perf", "strace", "ltrace"]

    if tool_name in static_tools:
        return "static"
    elif tool_name in dynamic_tools:
        return "dynamic"
    elif tool_name in profiling_tools:
        return "profiling"
    else:
        return "unknown"


def _calculate_semantic_hash(issue: Dict[str, Any]) -> str:
    """Calculate semantic hash for issue deduplication."""
    import hashlib

    # Extract key semantic elements
    message = issue.get("message", "").lower()
    category = issue.get("category", "")
    severity = issue.get("severity", "")
    file_path = issue.get("file", "")

    # Normalize message (remove line numbers, addresses, etc.)
    import re
    normalized_msg = re.sub(r'\b\d+\b', 'N', message)  # Replace numbers
    normalized_msg = re.sub(r'0x[0-9a-fA-F]+', 'ADDR', normalized_msg)  # Replace addresses
    normalized_msg = re.sub(r'[^\w\s]', '', normalized_msg)  # Remove special chars

    semantic_content = f"{normalized_msg}|{category}|{severity}|{file_path}"
    return hashlib.md5(semantic_content.encode()).hexdigest()[:16]


def _advanced_issue_grouping(issues: List[Dict[str, Any]], threshold: float) -> List[Dict[str, Any]]:
    """Advanced issue grouping with semantic understanding."""
    groups = []

    for issue in issues:
        # Find best matching group
        best_group = None
        best_similarity = 0.0

        for group in groups:
            similarity = _calculate_advanced_similarity(issue, group["representative"])
            if similarity >= threshold and similarity > best_similarity:
                best_similarity = similarity
                best_group = group

        if best_group:
            # Add to existing group
            best_group["issues"].append(issue)
            best_group["tool_consensus"].add(issue["source_tool"])
            best_group["tool_types"].add(issue["tool_type"])

            # Update group confidence based on consensus
            best_group["confidence"] = _calculate_group_confidence(best_group)

            # Check for issue chains (one issue causing another)
            best_group["is_chain_critical"] = _detect_issue_chain(best_group["issues"])

        else:
            # Create new group
            new_group = {
                "representative": issue,
                "issues": [issue],
                "tool_consensus": {issue["source_tool"]},
                "tool_types": {issue["tool_type"]},
                "confidence": issue.get("confidence", 0.5),
                "semantic_hash": issue["semantic_hash"],
                "is_chain_critical": False,
                "impact_score": _calculate_impact_score(issue)
            }
            groups.append(new_group)

    return groups


def _calculate_advanced_similarity(issue1: Dict[str, Any], issue2: Dict[str, Any]) -> float:
    """Calculate sophisticated similarity between issues."""
    score = 0.0

    # Semantic hash match (highest weight)
    if issue1["semantic_hash"] == issue2["semantic_hash"]:
        score += 0.4

    # Category match
    if issue1.get("category") == issue2.get("category") and issue1.get("category"):
        score += 0.25

    # Severity compatibility
    severity_weights = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}
    sev1 = severity_weights.get(issue1.get("severity", "low"), 1)
    sev2 = severity_weights.get(issue2.get("severity", "low"), 1)
    severity_sim = 1.0 - abs(sev1 - sev2) / 4.0
    score += 0.15 * severity_sim

    # Location similarity
    if issue1.get("file") == issue2.get("file") and issue1.get("file"):
        score += 0.1
        line1, line2 = issue1.get("line", 0), issue2.get("line", 0)
        if abs(line1 - line2) <= 10:  # Within 10 lines
            score += 0.1

    return min(score, 1.0)


def _calculate_group_confidence(group: Dict[str, Any]) -> float:
    """Calculate confidence based on tool consensus and consistency."""
    tool_count = len(group["tool_consensus"])
    tool_type_count = len(group["tool_types"])

    # Base confidence from individual issues
    base_confidence = sum(issue.get("confidence", 0.5) for issue in group["issues"]) / len(group["issues"])

    # Consensus bonus (multiple tools finding same issue)
    consensus_bonus = min(tool_count * 0.1, 0.4)

    # Tool diversity bonus (different types of tools agreeing)
    diversity_bonus = min(tool_type_count * 0.05, 0.2)

    return min(base_confidence + consensus_bonus + diversity_bonus, 1.0)


def _detect_issue_chain(issues: List[Dict[str, Any]]) -> bool:
    """Detect if issues form a causal chain (one causing another)."""
    # Look for patterns indicating causal relationships
    categories = [issue.get("category", "") for issue in issues]

    # Memory corruption chains
    memory_chain = any(cat in categories for cat in ["memory_error", "buffer_overflow"]) and \
                   any(cat in categories for cat in ["segfault", "undefined_behavior"])

    # Build/compilation chains
    build_chain = "build_safety" in categories and \
                  any(cat in categories for cat in ["memory_error", "undefined_behavior"])

    return memory_chain or build_chain


def _calculate_impact_score(issue: Dict[str, Any]) -> float:
    """Calculate potential impact score for an issue."""
    severity_impact = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2,
        "info": 0.1
    }

    category_impact = {
        "segfault": 1.0,
        "memory_error": 0.95,
        "buffer_overflow": 0.95,
        "data_race": 0.8,
        "undefined_behavior": 0.7,
        "memory_leak": 0.6,
        "performance": 0.4
    }

    base_impact = severity_impact.get(issue.get("severity", "low"), 0.2)
    category_modifier = category_impact.get(issue.get("category", ""), 0.5)
    confidence = issue.get("confidence", 0.5)

    return (base_impact * 0.5 + category_modifier * 0.3 + confidence * 0.2)


def _advanced_prioritization(groups: List[Dict[str, Any]], mode: str, tool_coverage: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Multi-dimensional prioritization with intelligent ranking."""

    for group in groups:
        # Calculate risk score
        group["risk_score"] = _calculate_risk_score(group, tool_coverage)

        # Assign priority levels
        group["priority"] = _assign_priority_level(group)

        # Calculate fix urgency
        group["fix_urgency"] = _calculate_fix_urgency(group)

        # Estimate fix difficulty
        group["fix_difficulty"] = _estimate_fix_difficulty(group)

        # Calculate business impact
        group["business_impact"] = _calculate_business_impact(group)

    # Sort based on priority mode
    if mode == "smart":
        # Weighted combination of all factors
        groups.sort(key=lambda g: (
            g["risk_score"] * 0.3 +
            g["fix_urgency"] * 0.25 +
            g["business_impact"] * 0.2 +
            (1.0 - g["fix_difficulty"]) * 0.15 +  # Easier fixes get higher priority
            g["confidence"] * 0.1
        ), reverse=True)
    elif mode == "severity":
        groups.sort(key=lambda g: (g["impact_score"], g["confidence"]), reverse=True)
    elif mode == "consensus":
        groups.sort(key=lambda g: (len(g["tool_consensus"]), g["confidence"]), reverse=True)
    else:  # confidence
        groups.sort(key=lambda g: g["confidence"], reverse=True)

    return groups


def _calculate_risk_score(group: Dict[str, Any], tool_coverage: Dict[str, Any]) -> float:
    """Calculate comprehensive risk score."""
    # Base risk from impact and confidence
    base_risk = group["impact_score"] * group["confidence"]

    # Tool consensus multiplier
    consensus_multiplier = 1.0 + (len(group["tool_consensus"]) - 1) * 0.2

    # Chain critical bonus
    chain_bonus = 0.3 if group.get("is_chain_critical", False) else 0.0

    # Security category bonus
    security_categories = ["buffer_overflow", "memory_error", "injection", "undefined_behavior"]
    security_bonus = 0.2 if group["representative"].get("category") in security_categories else 0.0

    return min((base_risk * consensus_multiplier) + chain_bonus + security_bonus, 1.0)


def _assign_priority_level(group: Dict[str, Any]) -> str:
    """Assign discrete priority level."""
    risk_score = group["risk_score"]
    consensus = len(group["tool_consensus"])

    if risk_score >= 0.8 or (risk_score >= 0.6 and consensus >= 3):
        return "critical"
    elif risk_score >= 0.5 or (risk_score >= 0.3 and consensus >= 2):
        return "high"
    elif risk_score >= 0.3:
        return "medium"
    else:
        return "low"


def _calculate_fix_urgency(group: Dict[str, Any]) -> float:
    """Calculate how urgently this needs to be fixed."""
    category = group["representative"].get("category", "")
    severity = group["representative"].get("severity", "low")

    # Critical categories need immediate attention
    if category in ["segfault", "buffer_overflow", "memory_error"]:
        return 1.0
    elif category in ["data_race", "undefined_behavior"]:
        return 0.8
    elif severity == "critical":
        return 0.9
    elif severity == "high":
        return 0.7
    else:
        return 0.4


def _estimate_fix_difficulty(group: Dict[str, Any]) -> float:
    """Estimate difficulty of fixing this issue (0.0 = easy, 1.0 = very hard)."""
    category = group["representative"].get("category", "")
    consensus = len(group["tool_consensus"])

    # Issues with good tool consensus are usually easier to fix
    consensus_factor = max(0.2, 1.0 - (consensus - 1) * 0.1)

    # Category-based difficulty
    if category in ["ai_recommendation", "performance"]:
        return 0.3 * consensus_factor  # Usually easy improvements
    elif category in ["memory_leak", "build_safety"]:
        return 0.5 * consensus_factor  # Moderate difficulty
    elif category in ["data_race", "undefined_behavior"]:
        return 0.8 * consensus_factor  # Hard to debug and fix
    else:
        return 0.6 * consensus_factor  # Default moderate difficulty


def _calculate_business_impact(group: Dict[str, Any]) -> float:
    """Calculate business/operational impact."""
    category = group["representative"].get("category", "")
    severity = group["representative"].get("severity", "low")

    # Security issues have high business impact
    if category in ["buffer_overflow", "memory_error", "injection"]:
        return 1.0
    # Stability issues
    elif category in ["segfault", "undefined_behavior"]:
        return 0.9
    # Performance issues
    elif "performance" in category:
        return 0.6
    # General severity mapping
    elif severity == "critical":
        return 0.8
    elif severity == "high":
        return 0.6
    else:
        return 0.3


def _generate_intelligent_recommendations(groups: List[Dict[str, Any]], tool_coverage: Dict[str, Any]) -> List[str]:
    """Generate sophisticated, actionable recommendations."""
    recommendations = []

    # Analyze critical issues
    critical_groups = [g for g in groups if g["priority"] == "critical"]
    if critical_groups:
        urgent_fixes = len([g for g in critical_groups if g["fix_urgency"] >= 0.8])
        recommendations.append(
            f"🚨 IMMEDIATE ACTION: {urgent_fixes} critical issues require immediate fixes "
            f"(average risk score: {sum(g['risk_score'] for g in critical_groups) / len(critical_groups):.2f})"
        )

    # Security-focused recommendations
    security_issues = [g for g in groups if g["representative"].get("category") in
                      ["buffer_overflow", "memory_error", "injection", "undefined_behavior"]]
    if security_issues:
        recommendations.append(
            f"🛡️ SECURITY REVIEW: {len(security_issues)} security vulnerabilities detected. "
            f"Prioritize buffer overflow and memory corruption fixes."
        )

    # Memory management recommendations
    memory_issues = [g for g in groups if "memory" in g["representative"].get("category", "").lower()]
    if memory_issues:
        tool_suggestions = []
        if "valgrind" not in tool_coverage:
            tool_suggestions.append("valgrind")
        if "asan" not in tool_coverage:
            tool_suggestions.append("AddressSanitizer")

        rec = f"💾 MEMORY MANAGEMENT: {len(memory_issues)} memory-related issues found."
        if tool_suggestions:
            rec += f" Consider running: {', '.join(tool_suggestions)}"
        recommendations.append(rec)

    # Tool consensus recommendations
    high_consensus = [g for g in groups if len(g["tool_consensus"]) >= 3]
    if high_consensus:
        recommendations.append(
            f"🎯 HIGH CONFIDENCE: {len(high_consensus)} issues confirmed by multiple tools. "
            f"These should be prioritized for fixes."
        )

    # Performance recommendations
    if "perf" in tool_coverage:
        recommendations.append("⚡ PERFORMANCE: Consider profiling optimizations after fixing critical issues.")

    # AI enhancement recommendations
    if "ai-clang-tidy" in tool_coverage:
        ai_suggestions = [g for g in groups if g["representative"].get("category") == "ai_recommendation"]
        if ai_suggestions:
            recommendations.append(
                f"🤖 AI INSIGHTS: {len(ai_suggestions)} AI-enhanced recommendations available. "
                f"Review for optimization opportunities."
            )

    # Quick wins identification
    easy_fixes = [g for g in groups if g["fix_difficulty"] <= 0.4 and g["priority"] in ["high", "medium"]]
    if easy_fixes:
        recommendations.append(
            f"✅ QUICK WINS: {len(easy_fixes)} issues can be fixed with low effort. "
            f"Start here for rapid improvement."
        )

    # Chain critical issues
    chain_issues = [g for g in groups if g.get("is_chain_critical", False)]
    if chain_issues:
        recommendations.append(
            f"🔗 CASCADING ISSUES: {len(chain_issues)} issue chains detected. "
            f"Fixing root causes will resolve multiple problems."
        )

    return recommendations[:12]  # Limit to most important recommendations


def _calculate_advanced_metrics(groups: List[Dict[str, Any]], tool_coverage: Dict[str, Any], all_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate comprehensive analysis metrics."""
    if not groups:
        return {"overall_risk_score": 0.0}

    # Overall risk assessment
    weighted_risks = [g["risk_score"] * len(g["issues"]) for g in groups]
    total_issues = sum(len(g["issues"]) for g in groups)
    overall_risk = sum(weighted_risks) / total_issues if total_issues > 0 else 0.0

    # Tool effectiveness
    tool_effectiveness = {}
    for tool, coverage in tool_coverage.items():
        if coverage["success"]:
            tool_effectiveness[tool] = coverage["issues_count"] / max(coverage["execution_time"], 0.1)

    # Issue distribution
    severity_distribution = {}
    category_distribution = {}
    for group in groups:
        severity = group["representative"].get("severity", "unknown")
        category = group["representative"].get("category", "unknown")
        severity_distribution[severity] = severity_distribution.get(severity, 0) + len(group["issues"])
        category_distribution[category] = category_distribution.get(category, 0) + len(group["issues"])

    return {
        "overall_risk_score": overall_risk,
        "tool_effectiveness": tool_effectiveness,
        "severity_distribution": severity_distribution,
        "category_distribution": category_distribution,
        "avg_group_confidence": sum(g["confidence"] for g in groups) / len(groups),
        "consensus_ratio": len([g for g in groups if len(g["tool_consensus"]) >= 2]) / len(groups),
        "chain_critical_ratio": len([g for g in groups if g.get("is_chain_critical", False)]) / len(groups)
    }


def _build_correlation_matrix(groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Build correlation matrix between different tools and issue types."""
    matrix = {}

    # Tool co-occurrence matrix
    tools_matrix = {}
    for group in groups:
        tools = list(group["tool_consensus"])
        for i, tool1 in enumerate(tools):
            for tool2 in tools[i+1:]:
                key = f"{tool1}+{tool2}"
                tools_matrix[key] = tools_matrix.get(key, 0) + 1

    # Category-severity correlation
    category_severity = {}
    for group in groups:
        category = group["representative"].get("category", "unknown")
        severity = group["representative"].get("severity", "unknown")
        key = f"{category}_{severity}"
        category_severity[key] = category_severity.get(key, 0) + 1

    return {
        "tool_correlations": tools_matrix,
        "category_severity_correlations": category_severity
    }


# Advanced parsing functions for maximum tool utilization

def _parse_gdb_output(stdout: str, stderr: str, tool_name: str) -> List[Dict[str, Any]]:
    """Advanced GDB output parsing with comprehensive crash analysis."""
    issues = []

    # Parse signal information
    for line in stdout.split('\n'):
        if 'received signal' in line.lower():
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "signal_crash",
                "confidence": 0.98,
                "signal_info": line
            })

        if 'segmentation fault' in line.lower() or 'sigsegv' in line.lower():
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "segfault",
                "confidence": 1.0
            })

        if 'stack overflow' in line.lower():
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "stack_overflow",
                "confidence": 0.95
            })

        # Parse register corruption indicators
        if 'corrupted' in line.lower() and 'register' in line.lower():
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "register_corruption",
                "confidence": 0.90
            })

    return issues


def _parse_strace_output(stdout: str, stderr: str, tool_name: str) -> List[Dict[str, Any]]:
    """Advanced strace parsing for comprehensive syscall analysis."""
    issues = []

    # Parse for suspicious syscall patterns
    lines = stdout.split('\n') + stderr.split('\n')

    for line in lines:
        # Failed syscalls
        if 'EFAULT' in line or 'SIGSEGV' in line:
            issues.append({
                "severity": "high",
                "message": line.strip(),
                "category": "syscall_fault",
                "confidence": 0.85
            })

        # Memory mapping issues
        if 'mmap' in line and ('ENOMEM' in line or 'failed' in line.lower()):
            issues.append({
                "severity": "high",
                "message": line.strip(),
                "category": "memory_mapping_failure",
                "confidence": 0.80
            })

        # File descriptor leaks
        if 'EMFILE' in line or 'ENFILE' in line:
            issues.append({
                "severity": "medium",
                "message": line.strip(),
                "category": "fd_exhaustion",
                "confidence": 0.75
            })

    return issues


def _parse_ltrace_output(stdout: str, stderr: str, tool_name: str) -> List[Dict[str, Any]]:
    """Advanced ltrace parsing for library call analysis."""
    issues = []

    lines = stdout.split('\n') + stderr.split('\n')

    for line in lines:
        # Memory allocation patterns
        if 'malloc(0)' in line:
            issues.append({
                "severity": "medium",
                "message": line.strip(),
                "category": "zero_malloc",
                "confidence": 0.70
            })

        # Double free detection
        if 'free(' in line and 'already freed' in line.lower():
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "double_free",
                "confidence": 0.95
            })

        # Library call failures
        if '+++ exited with' in line and not line.endswith('0 +++'):
            issues.append({
                "severity": "medium",
                "message": line.strip(),
                "category": "library_call_failure",
                "confidence": 0.60
            })

    return issues


def _parse_perf_output(stdout: str, stderr: str, tool_name: str) -> List[Dict[str, Any]]:
    """Advanced perf parsing for performance analysis."""
    issues = []

    lines = stdout.split('\n') + stderr.split('\n')

    for line in lines:
        # Cache miss analysis
        if 'cache-misses' in line:
            try:
                # Extract percentage
                if '%' in line:
                    percentage_str = line.split('%')[0].split()[-1]
                    percentage = float(percentage_str)
                    if percentage > 10.0:
                        issues.append({
                            "severity": "medium",
                            "message": f"High cache miss rate: {percentage}%",
                            "category": "cache_performance",
                            "confidence": 0.80,
                            "metric_value": percentage
                        })
            except (ValueError, IndexError):
                pass

        # Branch prediction analysis
        if 'branch-misses' in line and '%' in line:
            try:
                percentage_str = line.split('%')[0].split()[-1]
                percentage = float(percentage_str)
                if percentage > 5.0:
                    issues.append({
                        "severity": "low",
                        "message": f"High branch miss rate: {percentage}%",
                        "category": "branch_prediction",
                        "confidence": 0.70,
                        "metric_value": percentage
                    })
            except (ValueError, IndexError):
                pass

        # Page fault analysis
        if 'page-faults' in line:
            try:
                # Extract count
                count_str = line.split()[0].replace(',', '')
                count = int(count_str)
                if count > 1000:
                    issues.append({
                        "severity": "medium",
                        "message": f"High page fault count: {count}",
                        "category": "memory_performance",
                        "confidence": 0.75,
                        "metric_value": count
                    })
            except (ValueError, IndexError):
                pass

    return issues


def _parse_valgrind_output(stdout: str, stderr: str, tool_name: str) -> List[Dict[str, Any]]:
    """Enhanced valgrind parsing for all specialized tools."""
    issues = []

    if tool_name == "valgrind" or tool_name == "valgrind-memcheck":
        return _parse_valgrind_memcheck(stdout, stderr)
    elif tool_name == "valgrind-cachegrind":
        return _parse_valgrind_cachegrind(stdout, stderr)
    elif tool_name == "valgrind-callgrind":
        return _parse_valgrind_callgrind(stdout, stderr)
    elif tool_name == "valgrind-massif":
        return _parse_valgrind_massif(stdout, stderr)
    elif tool_name == "valgrind-helgrind":
        return _parse_valgrind_helgrind(stdout, stderr)
    elif tool_name == "valgrind-drd":
        return _parse_valgrind_drd(stdout, stderr)

    return issues


def _parse_valgrind_memcheck(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind memcheck output."""
    issues = []

    for line in stderr.split('\n'):
        if 'definitely lost:' in line or 'possibly lost:' in line:
            if not line.strip().endswith("0 bytes in 0 blocks"):
                severity = "critical" if "definitely" in line else "high"
                issues.append({
                    "severity": severity,
                    "message": line.strip(),
                    "category": "memory_leak",
                    "confidence": 0.95 if "definitely" in line else 0.80
                })

        if 'Invalid read' in line or 'Invalid write' in line:
            issues.append({
                "severity": "critical",
                "message": line.strip(),
                "category": "invalid_memory_access",
                "confidence": 0.98
            })

    return issues


def _parse_valgrind_cachegrind(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind cachegrind output."""
    issues = []

    for line in stderr.split('\n'):
        # Parse cache statistics
        if 'D1  miss rate:' in line:
            try:
                rate_str = line.split(':')[1].strip().rstrip('%')
                rate = float(rate_str)
                if rate > 5.0:
                    issues.append({
                        "severity": "medium",
                        "message": f"High L1 data cache miss rate: {rate}%",
                        "category": "cache_performance",
                        "confidence": 0.85,
                        "metric_value": rate
                    })
            except (ValueError, IndexError):
                pass

    return issues


def _parse_valgrind_callgrind(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind callgrind output."""
    issues = []

    # Callgrind primarily generates profiling data files
    # Look for execution completion and file generation
    for line in stderr.split('\n'):
        if 'Events    :' in line:
            issues.append({
                "severity": "info",
                "message": f"Profiling completed: {line.strip()}",
                "category": "profiling_info",
                "confidence": 1.0
            })

    return issues


def _parse_valgrind_massif(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind massif output."""
    issues = []

    for line in stderr.split('\n'):
        if 'peak:' in line:
            try:
                # Extract peak memory usage
                peak_str = line.split('peak:')[1].strip()
                issues.append({
                    "severity": "info",
                    "message": f"Peak memory usage: {peak_str}",
                    "category": "memory_usage",
                    "confidence": 1.0
                })
            except IndexError:
                pass

    return issues


def _parse_valgrind_helgrind(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind helgrind output."""
    issues = []

    for line in stderr.split('\n'):
        if 'Possible data race' in line:
            issues.append({
                "severity": "high",
                "message": line.strip(),
                "category": "data_race",
                "confidence": 0.90
            })

        if 'lock order violated' in line.lower():
            issues.append({
                "severity": "high",
                "message": line.strip(),
                "category": "lock_order_violation",
                "confidence": 0.85
            })

    return issues


def _parse_valgrind_drd(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse Valgrind DRD output."""
    issues = []

    for line in stderr.split('\n'):
        if 'Data race' in line:
            issues.append({
                "severity": "high",
                "message": line.strip(),
                "category": "data_race",
                "confidence": 0.92
            })

        if 'mutex' in line.lower() and 'error' in line.lower():
            issues.append({
                "severity": "medium",
                "message": line.strip(),
                "category": "mutex_error",
                "confidence": 0.80
            })

    return issues


def _parse_coverage_output(stdout: str, stderr: str) -> List[Dict[str, Any]]:
    """Parse coverage analysis output."""
    issues = []

    for line in stdout.split('\n'):
        # Look for low coverage indicators
        if 'lines......:' in line or 'functions..:' in line:
            try:
                percentage_match = line.split('%')[0].split()[-1]
                percentage = float(percentage_match)
                coverage_type = "line" if "lines" in line else "function"

                if percentage < 80.0:
                    severity = "medium" if percentage < 50.0 else "low"
                    issues.append({
                        "severity": severity,
                        "message": f"Low {coverage_type} coverage: {percentage}%",
                        "category": "test_coverage",
                        "confidence": 0.90,
                        "metric_value": percentage
                    })
            except (ValueError, IndexError):
                pass

    return issues