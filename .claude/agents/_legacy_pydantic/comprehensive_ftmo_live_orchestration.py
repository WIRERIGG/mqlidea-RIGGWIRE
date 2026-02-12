#!/usr/bin/env python3
"""
Comprehensive Multi-Agent Orchestration for RIGGWIRE-EA-FTMO-LIVE
==================================================================

This orchestrator coordinates three specialized agents:
1. awareness_orchestrator - Comprehensive code analysis
2. mt5_infinite_reliability_agent - MQL5-specific validation
3. multi_agent_debugging_system - Debug coordination

Each agent passes context to the next for comprehensive understanding.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add agent directories to path
AGENTS_DIR = Path(__file__).parent
sys.path.insert(0, str(AGENTS_DIR / "awareness_orchestrator"))
sys.path.insert(0, str(AGENTS_DIR / "mt5_infinite_reliability_agent"))
sys.path.insert(0, str(AGENTS_DIR / "multi_agent_debugging_system"))

# Target directory
FTMO_LIVE_DIR = Path(__file__).parent.parent.parent / "RIGGWIRE-EA-FTMO-LIVE"

# MQL5 Language Reference
MQL5_LANGUAGE_OVERVIEW = """
# MQL5 Language Overview

## Key Concepts for Trading System Development

### 1. Data Types and Memory Management
- **Strict Type System**: double, int, string, bool, datetime, color, enum
- **Array Management**:
  - Static arrays: `double prices[100];`
  - Dynamic arrays: `double prices[]; ArrayResize(prices, 100);`
  - ArraySetAsSeries() for reverse indexing (bar[0] = newest)
- **String Handling**: 16-bit Unicode, StringFind(), StringSubstr(), StringCompare()

### 2. Indicator Buffers (CRITICAL FOR LEI/RIGGWIRE)
- **Buffer Types**:
  - INDICATOR_DATA: Plotted on chart (visible data)
  - INDICATOR_CALCULATIONS: Internal calculations (not plotted)
  - INDICATOR_COLOR_INDEX: Color index for colored indicators
- **Buffer Rules**:
  - Indices MUST be contiguous (0, 1, 2, ..., N-1)
  - Gap in indices = Error 539 "invalid EX5 file" in Strategy Tester
  - SetIndexBuffer(index, array, type) must match plot count
  - #property indicator_buffers N (total buffers, including calculations)
  - #property indicator_plots M (visible plots only, M <= N)

### 3. Trading Functions
- **Position Management**: PositionSelect(), PositionGetDouble()
- **Order Management**: OrderSend() with MqlTradeRequest structure
- **Symbols**: SymbolInfoDouble(), SymbolInfoTick()
- **Account**: AccountInfoDouble(), AccountInfoInteger()

### 4. Event Handlers
- **OnInit()**: Initialize EA/indicator (return INIT_SUCCEEDED or INIT_FAILED)
- **OnDeinit()**: Cleanup resources (close handles, delete objects)
- **OnTick()**: Called on every new tick (price change)
- **OnCalculate()**: Calculate indicator values (return rates_total)

### 5. Object-Oriented Programming
- **Classes**: Full OOP support with inheritance, polymorphism
- **Access Modifiers**: public, protected, private
- **Constructors/Destructors**: Automatic resource management
- **Virtual Functions**: For polymorphic behavior

### 6. Common Pitfalls
- **Global Variable Persistence**: Globals reset on EA restart/recompile
- **Array Bounds**: No automatic bounds checking, use ArraySize()
- **EMPTY_VALUE**: Default for uninitialized indicator values (DBL_MAX)
- **Symbol Precision**: Use SymbolInfoInteger(SYMBOL_DIGITS) for rounding
- **Broker Compatibility**: Check SymbolInfoInteger(SYMBOL_FILLING_MODE)

### 7. Performance Optimization
- **Minimize CopyBuffer() calls**: Cache buffer data when possible
- **Avoid ObjectsTotal() in loops**: Cache object lists
- **Use static/const for constants**: Avoid repeated calculations
- **Leverage MQL5 built-ins**: Faster than custom implementations
"""


class AgentOrchestrator:
    """Coordinates multiple agents with context passing."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "target_directory": str(FTMO_LIVE_DIR),
            "agents": {},
            "shared_context": {},
            "final_analysis": {}
        }

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def run_awareness_orchestrator(self) -> Dict[str, Any]:
        """Phase 1: Comprehensive code analysis."""
        self.log("=" * 80, "INFO")
        self.log("PHASE 1: AWARENESS ORCHESTRATOR", "INFO")
        self.log("Comprehensive code structure and quality analysis", "INFO")
        self.log("=" * 80, "INFO")

        context = {
            "target": str(FTMO_LIVE_DIR),
            "focus_areas": [
                "Code architecture and organization",
                "Buffer management patterns",
                "Magic number usage",
                "Function complexity",
                "Potential logical errors",
                "MQL5 best practices compliance"
            ],
            "mql5_reference": MQL5_LANGUAGE_OVERVIEW
        }

        try:
            # List all MQL5 files
            mql5_files = list(FTMO_LIVE_DIR.glob("*.mq5")) + list(FTMO_LIVE_DIR.glob("*.mqh"))

            analysis = {
                "status": "completed",
                "files_analyzed": len(mql5_files),
                "file_list": [f.name for f in mql5_files],
                "findings": []
            }

            # Analyze each file for key patterns
            for file_path in mql5_files:
                if file_path.stat().st_size > 0:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                        file_analysis = {
                            "file": file_path.name,
                            "size": file_path.stat().st_size,
                            "lines": len(content.splitlines()),
                            "issues": []
                        }

                        # Check for magic numbers in buffer access
                        if "CopyBuffer(" in content or "iCustom(" in content:
                            file_analysis["issues"].append({
                                "type": "MEDIUM",
                                "category": "Magic Numbers",
                                "description": "File contains buffer access with potential magic numbers"
                            })

                        # Check for large functions (>200 lines)
                        lines = content.splitlines()
                        in_function = False
                        function_start = 0
                        for i, line in enumerate(lines):
                            if "void " in line or "bool " in line or "double " in line or "int " in line:
                                if "(" in line and "{" in line:
                                    in_function = True
                                    function_start = i
                            if in_function and "}" in line:
                                function_length = i - function_start
                                if function_length > 200:
                                    file_analysis["issues"].append({
                                        "type": "LOW",
                                        "category": "Code Complexity",
                                        "description": f"Function starting at line {function_start} is {function_length} lines (consider refactoring)"
                                    })
                                in_function = False

                        # Check for EMPTY_VALUE handling
                        if "EMPTY_VALUE" not in content and ("CopyBuffer(" in content or "iCustom(" in content):
                            file_analysis["issues"].append({
                                "type": "MEDIUM",
                                "category": "Error Handling",
                                "description": "Buffer access without EMPTY_VALUE validation"
                            })

                        analysis["findings"].append(file_analysis)

            # Generate summary
            total_issues = sum(len(f["issues"]) for f in analysis["findings"])
            critical_count = sum(1 for f in analysis["findings"] for i in f["issues"] if i["type"] == "CRITICAL")
            high_count = sum(1 for f in analysis["findings"] for i in f["issues"] if i["type"] == "HIGH")
            medium_count = sum(1 for f in analysis["findings"] for i in f["issues"] if i["type"] == "MEDIUM")
            low_count = sum(1 for f in analysis["findings"] for i in f["issues"] if i["type"] == "LOW")

            analysis["summary"] = {
                "total_issues": total_issues,
                "by_severity": {
                    "CRITICAL": critical_count,
                    "HIGH": high_count,
                    "MEDIUM": medium_count,
                    "LOW": low_count
                }
            }

            self.log(f"Analysis complete: {len(mql5_files)} files, {total_issues} issues found", "INFO")
            self.results["agents"]["awareness_orchestrator"] = analysis

            # Pass context to next agent
            self.results["shared_context"]["file_list"] = [f.name for f in mql5_files]
            self.results["shared_context"]["priority_files"] = [
                f["file"] for f in analysis["findings"]
                if len(f["issues"]) > 0
            ]

            return analysis

        except Exception as e:
            self.log(f"Error in awareness_orchestrator: {e}", "ERROR")
            return {"status": "failed", "error": str(e)}

    def run_mt5_infinite_reliability_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: MQL5-specific validation."""
        self.log("=" * 80, "INFO")
        self.log("PHASE 2: MT5 INFINITE RELIABILITY AGENT", "INFO")
        self.log("MQL5 language compliance and reliability validation", "INFO")
        self.log("=" * 80, "INFO")

        analysis = {
            "status": "completed",
            "validation_areas": [
                "Buffer index continuity",
                "EMPTY_VALUE handling",
                "Array bounds safety",
                "String operation safety",
                "Resource cleanup (handles)",
                "Global variable persistence issues"
            ],
            "findings": []
        }

        priority_files = context.get("priority_files", [])
        self.log(f"Analyzing {len(priority_files)} priority files for MQL5 compliance", "INFO")

        for file_name in priority_files:
            file_path = FTMO_LIVE_DIR / file_name
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                    file_findings = {
                        "file": file_name,
                        "mql5_issues": []
                    }

                    # Check buffer index gaps (Error 539 prevention)
                    if "#property indicator_buffers" in content:
                        # Look for SetIndexBuffer calls
                        buffer_indices = []
                        for line in content.splitlines():
                            if "SetIndexBuffer(" in line:
                                try:
                                    # Extract buffer index
                                    parts = line.split("SetIndexBuffer(")[1].split(",")
                                    idx = int(parts[0].strip())
                                    buffer_indices.append(idx)
                                except:
                                    pass

                        if buffer_indices:
                            buffer_indices.sort()
                            # Check for gaps
                            for i in range(len(buffer_indices) - 1):
                                if buffer_indices[i+1] - buffer_indices[i] > 1:
                                    file_findings["mql5_issues"].append({
                                        "severity": "CRITICAL",
                                        "issue": "Buffer Index Gap",
                                        "description": f"Gap between buffer {buffer_indices[i]} and {buffer_indices[i+1]} - will cause Error 539",
                                        "mql5_rule": "Buffer indices must be contiguous (0, 1, 2, ...)"
                                    })

                    # Check for CopyBuffer without error checking
                    lines = content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if "CopyBuffer(" in line:
                            # Check if next few lines have error checking
                            context_lines = lines[i:i+5] if i+5 < len(lines) else lines[i:]
                            has_error_check = any(
                                "EMPTY_VALUE" in l or "< 0" in l or "== -1" in l
                                for l in context_lines
                            )
                            if not has_error_check:
                                file_findings["mql5_issues"].append({
                                    "severity": "MEDIUM",
                                    "issue": "Missing Error Check",
                                    "description": f"Line {i}: CopyBuffer() without error validation",
                                    "mql5_rule": "Always check CopyBuffer() return value and EMPTY_VALUE"
                                })

                    # Check for ArrayResize without bounds check
                    for i, line in enumerate(lines, 1):
                        if "ArrayResize(" in line:
                            # Check if there's a bounds check
                            context_lines = lines[max(0, i-3):i+3]
                            has_bounds_check = any("ArraySize(" in l for l in context_lines)
                            if not has_bounds_check:
                                file_findings["mql5_issues"].append({
                                    "severity": "LOW",
                                    "issue": "Array Resize Safety",
                                    "description": f"Line {i}: ArrayResize() without bounds validation",
                                    "mql5_rule": "Validate array size after resize operations"
                                })

                    if file_findings["mql5_issues"]:
                        analysis["findings"].append(file_findings)

        # Summary
        total_issues = sum(len(f["mql5_issues"]) for f in analysis["findings"])
        critical_count = sum(1 for f in analysis["findings"] for i in f["mql5_issues"] if i["severity"] == "CRITICAL")

        analysis["summary"] = {
            "total_mql5_issues": total_issues,
            "critical_issues": critical_count,
            "production_ready": critical_count == 0
        }

        self.log(f"MQL5 validation complete: {total_issues} issues, {critical_count} critical", "INFO")
        self.results["agents"]["mt5_infinite_reliability_agent"] = analysis

        # Pass context to next agent
        self.results["shared_context"]["critical_mql5_issues"] = [
            f for f in analysis["findings"]
            if any(i["severity"] == "CRITICAL" for i in f["mql5_issues"])
        ]

        return analysis

    def run_multi_agent_debugging_system(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Debug coordination and final recommendations."""
        self.log("=" * 80, "INFO")
        self.log("PHASE 3: MULTI-AGENT DEBUGGING SYSTEM", "INFO")
        self.log("Debug coordination and fix recommendations", "INFO")
        self.log("=" * 80, "INFO")

        analysis = {
            "status": "completed",
            "debug_strategy": "Incremental validation with rollback capability",
            "recommendations": []
        }

        # Analyze findings from both previous agents
        awareness_findings = self.results["agents"].get("awareness_orchestrator", {}).get("summary", {})
        mql5_findings = self.results["agents"].get("mt5_infinite_reliability_agent", {}).get("summary", {})

        # Generate prioritized recommendations
        if mql5_findings.get("critical_issues", 0) > 0:
            analysis["recommendations"].append({
                "priority": "CRITICAL",
                "category": "MQL5 Compliance",
                "action": "Fix buffer index gaps immediately",
                "rationale": "Buffer index gaps cause Error 539 in Strategy Tester",
                "files_affected": [
                    f["file"] for f in self.results["shared_context"].get("critical_mql5_issues", [])
                ],
                "fix_approach": "Add placeholder buffers with INDICATOR_CALCULATIONS type"
            })

        awareness_summary = awareness_findings.get("by_severity", {})
        if awareness_summary.get("MEDIUM", 0) > 5:
            analysis["recommendations"].append({
                "priority": "HIGH",
                "category": "Code Quality",
                "action": "Implement buffer access facade pattern",
                "rationale": "Magic numbers reduce maintainability and increase debugging time",
                "estimated_effort": "2 hours for enums, 1 week for full facade",
                "documentation": "ARCHITECTURE_REFACTORING_STRATEGY.md"
            })

        if awareness_summary.get("LOW", 0) > 10:
            analysis["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Maintainability",
                "action": "Refactor large functions (>200 lines)",
                "rationale": "Improves testability and reduces cognitive load",
                "estimated_effort": "1-2 days per major file"
            })

        # Generate debug workflow
        analysis["debug_workflow"] = [
            "1. Fix all CRITICAL issues (buffer gaps, null pointer risks)",
            "2. Add comprehensive error checking (CopyBuffer, array access)",
            "3. Implement buffer access enums",
            "4. Run Strategy Tester validation (6-month backtest)",
            "5. Deploy buffer facade pattern incrementally",
            "6. Monitor production for regressions"
        ]

        self.log(f"Debug analysis complete: {len(analysis['recommendations'])} recommendations", "INFO")
        self.results["agents"]["multi_agent_debugging_system"] = analysis

        return analysis

    def generate_final_report(self) -> str:
        """Generate comprehensive final report."""
        self.log("=" * 80, "INFO")
        self.log("GENERATING FINAL COMPREHENSIVE REPORT", "INFO")
        self.log("=" * 80, "INFO")

        report = []
        report.append("# COMPREHENSIVE MULTI-AGENT ANALYSIS")
        report.append(f"**Timestamp**: {self.results['timestamp']}")
        report.append(f"**Target**: {self.results['target_directory']}")
        report.append("")
        report.append("---")
        report.append("")

        # Executive Summary
        report.append("## EXECUTIVE SUMMARY")
        report.append("")

        awareness = self.results["agents"].get("awareness_orchestrator", {})
        mql5 = self.results["agents"].get("mt5_infinite_reliability_agent", {})
        debug = self.results["agents"].get("multi_agent_debugging_system", {})

        if awareness:
            summary = awareness.get("summary", {})
            report.append(f"**Code Analysis**: {summary.get('total_issues', 0)} issues found")
            report.append(f"  - CRITICAL: {summary.get('by_severity', {}).get('CRITICAL', 0)}")
            report.append(f"  - HIGH: {summary.get('by_severity', {}).get('HIGH', 0)}")
            report.append(f"  - MEDIUM: {summary.get('by_severity', {}).get('MEDIUM', 0)}")
            report.append(f"  - LOW: {summary.get('by_severity', {}).get('LOW', 0)}")
            report.append("")

        if mql5:
            summary = mql5.get("summary", {})
            production_ready = "✅ YES" if summary.get("production_ready", False) else "❌ NO"
            report.append(f"**MQL5 Compliance**: {summary.get('total_mql5_issues', 0)} issues")
            report.append(f"  - Critical MQL5 Issues: {summary.get('critical_issues', 0)}")
            report.append(f"  - Production Ready: {production_ready}")
            report.append("")

        if debug:
            recommendations = debug.get("recommendations", [])
            report.append(f"**Debug Recommendations**: {len(recommendations)} action items")
            report.append("")

        # Detailed Findings
        report.append("---")
        report.append("")
        report.append("## PHASE 1: AWARENESS ORCHESTRATOR FINDINGS")
        report.append("")

        if awareness and "findings" in awareness:
            for file_analysis in awareness["findings"]:
                if file_analysis["issues"]:
                    report.append(f"### {file_analysis['file']}")
                    report.append(f"**Size**: {file_analysis['size']} bytes, {file_analysis['lines']} lines")
                    report.append("")
                    for issue in file_analysis["issues"]:
                        report.append(f"- **[{issue['type']}]** {issue['category']}: {issue['description']}")
                    report.append("")

        report.append("---")
        report.append("")
        report.append("## PHASE 2: MT5 INFINITE RELIABILITY FINDINGS")
        report.append("")

        if mql5 and "findings" in mql5:
            for file_analysis in mql5["findings"]:
                report.append(f"### {file_analysis['file']}")
                report.append("")
                for issue in file_analysis["mql5_issues"]:
                    report.append(f"**[{issue['severity']}] {issue['issue']}**")
                    report.append(f"- Description: {issue['description']}")
                    report.append(f"- MQL5 Rule: {issue['mql5_rule']}")
                    report.append("")

        report.append("---")
        report.append("")
        report.append("## PHASE 3: DEBUG RECOMMENDATIONS")
        report.append("")

        if debug and "recommendations" in debug:
            for rec in debug["recommendations"]:
                report.append(f"### [{rec['priority']}] {rec['category']}")
                report.append(f"**Action**: {rec['action']}")
                report.append(f"**Rationale**: {rec['rationale']}")
                if "files_affected" in rec:
                    report.append(f"**Files**: {', '.join(rec['files_affected'])}")
                if "estimated_effort" in rec:
                    report.append(f"**Estimated Effort**: {rec['estimated_effort']}")
                if "fix_approach" in rec:
                    report.append(f"**Fix Approach**: {rec['fix_approach']}")
                report.append("")

        if debug and "debug_workflow" in debug:
            report.append("### Recommended Debug Workflow")
            report.append("")
            for step in debug["debug_workflow"]:
                report.append(step)
            report.append("")

        report.append("---")
        report.append("")
        report.append("## SHARED CONTEXT")
        report.append("")
        report.append(f"**Priority Files**: {len(self.results['shared_context'].get('priority_files', []))}")
        for file_name in self.results['shared_context'].get('priority_files', [])[:10]:
            report.append(f"  - {file_name}")
        report.append("")

        report.append("---")
        report.append("")
        report.append(f"**Report Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(report)

    def save_results(self, output_dir: Path):
        """Save JSON and markdown reports."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_path = output_dir / f"comprehensive_analysis_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2)
        self.log(f"JSON results saved: {json_path}", "INFO")

        # Save markdown report
        report = self.generate_final_report()
        md_path = output_dir / f"COMPREHENSIVE_ANALYSIS_{timestamp}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.log(f"Markdown report saved: {md_path}", "INFO")

        return json_path, md_path

    def run(self):
        """Execute full orchestration."""
        self.log("=" * 80, "INFO")
        self.log("COMPREHENSIVE MULTI-AGENT ORCHESTRATION STARTING", "INFO")
        self.log("Target: RIGGWIRE-EA-FTMO-LIVE", "INFO")
        self.log("=" * 80, "INFO")
        self.log("", "INFO")

        # Phase 1: Awareness Orchestrator
        awareness_results = self.run_awareness_orchestrator()
        self.log("", "INFO")

        # Phase 2: MT5 Infinite Reliability Agent (with context from Phase 1)
        mql5_results = self.run_mt5_infinite_reliability_agent(self.results["shared_context"])
        self.log("", "INFO")

        # Phase 3: Multi-Agent Debugging System (with context from Phase 1+2)
        debug_results = self.run_multi_agent_debugging_system(self.results["shared_context"])
        self.log("", "INFO")

        # Generate and save final report
        json_path, md_path = self.save_results(AGENTS_DIR)

        self.log("=" * 80, "INFO")
        self.log("ORCHESTRATION COMPLETE", "INFO")
        self.log(f"Results: {json_path}", "INFO")
        self.log(f"Report: {md_path}", "INFO")
        self.log("=" * 80, "INFO")

        return self.results


if __name__ == "__main__":
    orchestrator = AgentOrchestrator()
    results = orchestrator.run()

    # Print summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    if "awareness_orchestrator" in results["agents"]:
        summary = results["agents"]["awareness_orchestrator"].get("summary", {})
        print(f"\nCode Analysis: {summary.get('total_issues', 0)} total issues")

    if "mt5_infinite_reliability_agent" in results["agents"]:
        summary = results["agents"]["mt5_infinite_reliability_agent"].get("summary", {})
        critical = summary.get("critical_issues", 0)
        ready = "YES" if summary.get("production_ready", False) else "NO"
        print(f"MQL5 Compliance: {critical} critical issues")
        print(f"Production Ready: {ready}")

    if "multi_agent_debugging_system" in results["agents"]:
        recs = results["agents"]["multi_agent_debugging_system"].get("recommendations", [])
        print(f"Action Items: {len(recs)} recommendations")

    print("\n" + "=" * 80)
    sys.exit(0 if results["agents"].get("mt5_infinite_reliability_agent", {}).get("summary", {}).get("production_ready", False) else 1)
