#!/usr/bin/env python3
"""
TrendCipher Indicator Fix - Multi-Agent Orchestration
=====================================================

Specialized orchestration for fixing broken TrendCipher.mq5 indicator.

User Issue: "broke it while trying to improve it"
Goal: Identify what's broken, keep working features, discard incompatible ones
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Target file
FTMO_LIVE_DIR = Path(__file__).parent.parent.parent / "RIGGWIRE-EA-FTMO-LIVE"
TRENDCIPHER_FILE = FTMO_LIVE_DIR / "TrendCipher.mq5"

# MQL5 Language Reference (embedded for agent context)
MQL5_LANGUAGE_OVERVIEW = """
# MQL5 Critical Rules for Indicator Development

## 1. Indicator Buffers
- MUST be contiguous (0, 1, 2, ..., N-1) - gaps cause Error 539
- Types: INDICATOR_DATA (plotted), INDICATOR_CALCULATIONS (internal)
- SetIndexBuffer() calls must match #property indicator_buffers
- ArraySetAsSeries(buffer, true) for time series indexing

## 2. Variable Scope and Lifetime
- Global variables: Persist across OnCalculate() calls
- Static variables: Persist within function scope
- Local variables: Reset every function call
- Arrays: Dynamic sizing with ArrayResize()

## 3. Common Errors
- Error 539: Buffer index gaps or invalid EX5 structure
- Division by zero: Always check denominator > tolerance
- Array out of bounds: Validate index before access
- EMPTY_VALUE: Check after CopyBuffer() calls

## 4. OnCalculate() Best Practices
- Calculate from `start` index to 0 (time series)
- Use prev_calculated for incremental updates
- Always validate rates_total and array sizes
- Handle history changes (rates_total != prev_calculated)

## 5. Performance Optimization
- Minimize loop iterations (only recalc changed bars)
- Use running sums instead of repeated summations
- Cache indicator handle results
- Release handles in OnDeinit()
"""


class TrendCipherAnalyzer:
    """Specialized analyzer for TrendCipher indicator issues."""

    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "file": str(TRENDCIPHER_FILE),
            "analysis": {},
            "issues": [],
            "recommendations": []
        }

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def analyze_file(self) -> Dict[str, Any]:
        """Comprehensive TrendCipher analysis."""
        if not TRENDCIPHER_FILE.exists():
            self.log("ERROR: TrendCipher.mq5 not found", "ERROR")
            return {"status": "error", "message": "File not found"}

        with open(TRENDCIPHER_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        self.log("Analyzing TrendCipher.mq5 (3316 lines)...", "INFO")

        # Phase 1: Structural Analysis
        self.log("=== PHASE 1: STRUCTURAL ANALYSIS ===", "INFO")
        structural = self.analyze_structure(content)
        self.results["analysis"]["structural"] = structural

        # Phase 2: Buffer Management Analysis
        self.log("=== PHASE 2: BUFFER MANAGEMENT ===", "INFO")
        buffers = self.analyze_buffers(content)
        self.results["analysis"]["buffers"] = buffers

        # Phase 3: Logic Flow Analysis
        self.log("=== PHASE 3: LOGIC FLOW ===", "INFO")
        logic = self.analyze_logic(content)
        self.results["analysis"]["logic"] = logic

        # Phase 4: Compilation Issues
        self.log("=== PHASE 4: COMPILATION CHECKS ===", "INFO")
        compilation = self.check_compilation_issues(content)
        self.results["analysis"]["compilation"] = compilation

        # Phase 5: EA Compatibility
        self.log("=== PHASE 5: EA COMPATIBILITY ===", "INFO")
        compatibility = self.check_ea_compatibility(content)
        self.results["analysis"]["compatibility"] = compatibility

        # Generate recommendations
        self.generate_recommendations()

        return self.results

    def analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze file structure."""
        lines = content.splitlines()

        # Count version headers
        version_count = len(re.findall(r'v\d+\.\d+', content))

        # Find property declarations
        properties = re.findall(r'#property\s+(\w+)\s+(.+)', content)

        # Count functions
        functions = re.findall(r'^(int|double|bool|void|string)\s+(\w+)\s*\(', content, re.MULTILINE)

        # Find buffer declarations
        buffer_declarations = re.findall(r'double\s+(\w+Buffer)\[\];', content)

        return {
            "total_lines": len(lines),
            "version_references": version_count,
            "properties": len(properties),
            "functions": len(functions),
            "buffer_declarations": len(buffer_declarations),
            "property_list": dict(properties[:10]),  # First 10 properties
            "function_names": [f[1] for f in functions[:20]]  # First 20 functions
        }

    def analyze_buffers(self, content: str) -> Dict[str, Any]:
        """Analyze buffer management for Error 539 risks."""
        issues = []

        # Find indicator_buffers property
        buffers_match = re.search(r'#property\s+indicator_buffers\s+(\d+)', content)
        plots_match = re.search(r'#property\s+indicator_plots\s+(\d+)', content)

        total_buffers = int(buffers_match.group(1)) if buffers_match else 0
        total_plots = int(plots_match.group(1)) if plots_match else 0

        # Find SetIndexBuffer calls
        set_buffer_calls = re.findall(r'SetIndexBuffer\((\d+),\s*(\w+),\s*(\w+)\)', content)
        buffer_indices = [int(call[0]) for call in set_buffer_calls]
        buffer_indices.sort()

        # Check for gaps
        gaps = []
        for i in range(len(buffer_indices) - 1):
            if buffer_indices[i+1] - buffer_indices[i] > 1:
                gaps.append({
                    "from": buffer_indices[i],
                    "to": buffer_indices[i+1],
                    "gap_size": buffer_indices[i+1] - buffer_indices[i] - 1
                })

        if gaps:
            issues.append({
                "severity": "CRITICAL",
                "type": "Buffer Index Gap",
                "description": f"Found {len(gaps)} buffer index gaps - will cause Error 539",
                "gaps": gaps
            })

        # Check buffer count mismatch
        if len(buffer_indices) != total_buffers:
            issues.append({
                "severity": "CRITICAL",
                "type": "Buffer Count Mismatch",
                "description": f"indicator_buffers={total_buffers} but {len(buffer_indices)} SetIndexBuffer calls found"
            })

        return {
            "total_buffers": total_buffers,
            "total_plots": total_plots,
            "buffer_indices": buffer_indices,
            "gaps": gaps,
            "issues": issues
        }

    def analyze_logic(self, content: str) -> Dict[str, Any]:
        """Analyze logic flow for common issues."""
        issues = []
        warnings = []

        # Check for division without safety checks
        divisions = re.findall(r'/\s*([a-zA-Z_]\w*)', content)
        if len(divisions) > 50:
            warnings.append({
                "type": "Division Operations",
                "count": len(divisions),
                "recommendation": "Ensure all divisions check for zero denominator"
            })

        # Check for array access patterns
        array_accesses = re.findall(r'(\w+)\[(\d+|i|j|k|index)\]', content)
        if len(array_accesses) > 100:
            warnings.append({
                "type": "Array Access",
                "count": len(array_accesses),
                "recommendation": "Verify bounds checking before array access"
            })

        # Check for EMPTY_VALUE validation
        copybuffer_calls = len(re.findall(r'CopyBuffer\(', content))
        empty_value_checks = len(re.findall(r'EMPTY_VALUE', content))

        if copybuffer_calls > 0 and empty_value_checks < copybuffer_calls:
            warnings.append({
                "type": "Missing EMPTY_VALUE Checks",
                "copybuffer_calls": copybuffer_calls,
                "empty_value_checks": empty_value_checks,
                "recommendation": "Add EMPTY_VALUE validation after CopyBuffer() calls"
            })

        # Check for static variable issues
        static_vars = re.findall(r'static\s+(\w+)\s+(\w+)', content)
        if len(static_vars) > 5:
            warnings.append({
                "type": "Static Variables",
                "count": len(static_vars),
                "recommendation": "Consider using global variables for state persistence"
            })

        return {
            "issues": issues,
            "warnings": warnings,
            "stats": {
                "divisions": len(divisions),
                "array_accesses": len(array_accesses),
                "copybuffer_calls": copybuffer_calls,
                "static_variables": len(static_vars)
            }
        }

    def check_compilation_issues(self, content: str) -> Dict[str, Any]:
        """Check for common compilation errors."""
        issues = []

        # Check for undeclared identifiers (variables used before declaration)
        # This is a heuristic check
        declared_vars = set(re.findall(r'(?:double|int|bool|string|datetime)\s+(\w+)\s*[=;]', content))
        used_vars = set(re.findall(r'(?<![a-zA-Z_])([a-zA-Z_]\w+)(?:\s*=|\s*\[)', content))

        # Check for function calls without declarations
        declared_functions = set(re.findall(r'^(?:int|double|bool|void|string)\s+(\w+)\s*\(', content, re.MULTILINE))
        called_functions = set(re.findall(r'(\w+)\s*\(', content))

        # Look for common typos
        typos = []
        if 'g_activeSignalDirection' in content and 'DISABLED in v12.9' in content:
            typos.append({
                "variable": "g_activeSignalDirection",
                "issue": "Variable referenced but commented as DISABLED",
                "line_pattern": "g_activeSignalDirection"
            })

        if typos:
            issues.append({
                "severity": "MEDIUM",
                "type": "Potential Typos or Disabled Code",
                "count": len(typos),
                "examples": typos
            })

        return {
            "issues": issues,
            "stats": {
                "declared_vars": len(declared_vars),
                "used_vars": len(used_vars),
                "declared_functions": len(declared_functions),
                "called_functions": len(called_functions)
            }
        }

    def check_ea_compatibility(self, content: str) -> Dict[str, Any]:
        """Check compatibility with EA requirements."""
        compatibility = {
            "signal_generation": False,
            "buffer_access": False,
            "proper_empty_values": False,
            "issues": []
        }

        # Check for signal buffer assignments
        if re.search(r'buyEntryBuffer\[', content) and re.search(r'sellEntryBuffer\[', content):
            compatibility["signal_generation"] = True
        else:
            compatibility["issues"].append({
                "type": "Signal Generation",
                "description": "Missing buy/sell entry buffer assignments"
            })

        # Check for EMPTY_VALUE usage in signal buffers
        if re.search(r'buyEntryBuffer.*EMPTY_VALUE', content):
            compatibility["proper_empty_values"] = True

        # Check for iCustom compatibility (EA needs to call this indicator)
        if '#property indicator_separate_window' in content:
            compatibility["buffer_access"] = True

        return compatibility

    def generate_recommendations(self):
        """Generate fix recommendations based on analysis."""
        buffers = self.results["analysis"]["buffers"]
        compilation = self.results["analysis"]["compilation"]
        compatibility = self.results["analysis"]["compatibility"]

        # Priority 1: Buffer gaps (CRITICAL)
        if buffers["gaps"]:
            self.results["recommendations"].append({
                "priority": "CRITICAL",
                "category": "Buffer Management",
                "action": "Fix buffer index gaps to prevent Error 539",
                "details": f"Found {len(buffers['gaps'])} gaps in buffer indices",
                "fix": "Add placeholder buffers or renumber indices to be contiguous"
            })

        # Priority 2: Buffer count mismatch
        if buffers["issues"]:
            for issue in buffers["issues"]:
                if issue["type"] == "Buffer Count Mismatch":
                    self.results["recommendations"].append({
                        "priority": "CRITICAL",
                        "category": "Buffer Management",
                        "action": "Fix buffer count mismatch",
                        "details": issue["description"],
                        "fix": "Update #property indicator_buffers to match SetIndexBuffer() calls"
                    })

        # Priority 3: EA Compatibility
        if not compatibility["signal_generation"]:
            self.results["recommendations"].append({
                "priority": "HIGH",
                "category": "EA Compatibility",
                "action": "Fix signal buffer assignments",
                "details": "EA requires buyEntryBuffer and sellEntryBuffer to be populated",
                "fix": "Ensure GenerateEntryExitSignals() properly sets signal buffers"
            })

        # Priority 4: Code cleanup
        logic_warnings = self.results["analysis"]["logic"]["warnings"]
        if len(logic_warnings) > 3:
            self.results["recommendations"].append({
                "priority": "MEDIUM",
                "category": "Code Quality",
                "action": "Address logic warnings",
                "details": f"{len(logic_warnings)} warnings found",
                "fix": "Review division operations, array bounds, and EMPTY_VALUE checks"
            })


def main():
    print("=" * 80)
    print("TRENDCIPHER INDICATOR FIX - MULTI-AGENT ORCHESTRATION")
    print("=" * 80)
    print()

    analyzer = TrendCipherAnalyzer()
    results = analyzer.analyze_file()

    # Save results
    output_file = Path(__file__).parent / f"trendcipher_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Results saved: {output_file}")
    print()

    # Print summary
    if "buffers" in results["analysis"]:
        buffers = results["analysis"]["buffers"]
        print(f"Buffer Analysis:")
        print(f"  Total Buffers: {buffers['total_buffers']}")
        print(f"  Total Plots: {buffers['total_plots']}")
        print(f"  Buffer Gaps: {len(buffers['gaps'])}")
        if buffers['gaps']:
            print(f"  ⚠️  CRITICAL: Buffer index gaps detected (Error 539 risk)")
        print()

    if results["recommendations"]:
        print(f"Recommendations: {len(results['recommendations'])}")
        for i, rec in enumerate(results["recommendations"], 1):
            print(f"  {i}. [{rec['priority']}] {rec['action']}")
        print()

    return 0 if not results["recommendations"] else 1


if __name__ == "__main__":
    sys.exit(main())
