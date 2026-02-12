#!/usr/bin/env python3
"""
Multi-Agent Orchestration System for RIGGWIRE-EA-FTMO-LIVE

This script coordinates three specialized agent systems:
1. MT5 Infinite Reliability Agent - MQL5 code analysis
2. Multi-Agent Debugging System - C++/general debugging
3. Awareness Orchestrator - Code quality and architecture

Context is passed between agents to build comprehensive understanding
and generate integrated fix recommendations.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Setup paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
FTMO_LIVE_DIR = PROJECT_ROOT / "RIGGWIRE-EA-FTMO-LIVE"

print(f"Script directory: {SCRIPT_DIR}")
print(f"Project root: {PROJECT_ROOT}")
print(f"FTMO-LIVE directory: {FTMO_LIVE_DIR}")

# Agent directories
MT5_AGENT_DIR = SCRIPT_DIR / "mt5_infinite_reliability_agent"
DEBUG_AGENT_DIR = SCRIPT_DIR / "multi_agent_debugging_system"
ORCHESTRATOR_DIR = SCRIPT_DIR / "awareness_orchestrator"

class MultiAgentOrchestrator:
    """Orchestrates multiple agent systems with context sharing"""

    def __init__(self):
        self.session_id = f"multi_agent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.context = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "target_directory": str(FTMO_LIVE_DIR),
            "agents_used": [],
            "shared_findings": {},
            "integrated_recommendations": []
        }
        self.results = {
            "mt5_agent": None,
            "debug_agent": None,
            "orchestrator": None
        }

    def log(self, message: str, agent: str = "ORCHESTRATOR"):
        """Log with timestamp and agent name"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{agent}] {message}")

    async def run_mt5_reliability_agent(self):
        """Phase 1: Run MT5 Infinite Reliability Agent"""
        self.log("=" * 60)
        self.log("PHASE 1: MT5 INFINITE RELIABILITY AGENT")
        self.log("=" * 60)
        self.context["agents_used"].append("mt5_infinite_reliability_agent")

        # Check if we already have results
        results_file = MT5_AGENT_DIR / "ftmo_live_analysis_results.json"
        if results_file.exists():
            self.log(f"Loading existing MT5 analysis from {results_file}")
            with open(results_file, 'r') as f:
                self.results["mt5_agent"] = json.load(f)

            # Extract key findings
            total_issues = self.results["mt5_agent"]["summary"]["total_unused_patterns"]
            files_with_issues = self.results["mt5_agent"]["summary"]["files_with_issues"]

            self.log(f"MT5 Agent found {total_issues} issues in {files_with_issues} files")

            # Share findings with context
            self.context["shared_findings"]["mt5_agent"] = {
                "total_issues": total_issues,
                "files_with_issues": files_with_issues,
                "top_files": self._get_top_problem_files(self.results["mt5_agent"]),
                "issue_types": self._categorize_mt5_issues(self.results["mt5_agent"])
            }

            return True
        else:
            self.log("No existing MT5 analysis found. Please run analyze_ftmo_live.py first.", "ERROR")
            return False

    def _get_top_problem_files(self, mt5_results: Dict) -> List[Dict]:
        """Extract top problem files from MT5 analysis"""
        files = []
        for file_data in mt5_results.get("files_analyzed", []):
            if len(file_data.get("unused_logic", [])) > 0:
                files.append({
                    "name": file_data["file_name"],
                    "issues": len(file_data["unused_logic"]),
                    "lines": file_data.get("lines", 0)
                })

        # Sort by issues descending
        files.sort(key=lambda x: x["issues"], reverse=True)
        return files[:10]  # Top 10

    def _categorize_mt5_issues(self, mt5_results: Dict) -> Dict[str, int]:
        """Categorize issues by type"""
        categories = {
            "commented_code": 0,
            "potentially_unused_variable": 0,
            "unreachable_code": 0,
            "empty_function": 0,
            "other": 0
        }

        for file_data in mt5_results.get("files_analyzed", []):
            for issue in file_data.get("unused_logic", []):
                issue_type = issue.get("type", "other")
                if issue_type in categories:
                    categories[issue_type] += 1
                else:
                    categories["other"] += 1

        return categories

    async def analyze_mql5_language_patterns(self):
        """Phase 2: Analyze MQL5-specific language patterns"""
        self.log("=" * 60)
        self.log("PHASE 2: MQL5 LANGUAGE PATTERN ANALYSIS")
        self.log("=" * 60)

        # Common MQL5 patterns to check
        patterns = {
            "memory_management": [
                "ArrayResize",
                "ArrayFree",
                "delete",
                "new"
            ],
            "error_handling": [
                "_LastError",
                "GetLastError",
                "ResetLastError"
            ],
            "indicator_functions": [
                "iCustom",
                "CopyBuffer",
                "IndicatorCreate",
                "IndicatorRelease"
            ],
            "trade_operations": [
                "OrderSend",
                "PositionOpen",
                "PositionClose",
                "PositionModify"
            ]
        }

        mql5_findings = {}

        for mq5_file in FTMO_LIVE_DIR.glob("*.mq5"):
            self.log(f"Analyzing {mq5_file.name} for MQL5 patterns...")
            try:
                with open(mq5_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                file_patterns = {}
                for category, keywords in patterns.items():
                    count = sum(content.count(keyword) for keyword in keywords)
                    if count > 0:
                        file_patterns[category] = count

                if file_patterns:
                    mql5_findings[mq5_file.name] = file_patterns

            except Exception as e:
                self.log(f"Error analyzing {mq5_file.name}: {e}", "ERROR")

        self.context["shared_findings"]["mql5_patterns"] = mql5_findings
        self.log(f"Found MQL5 patterns in {len(mql5_findings)} files")

        return True

    async def generate_integrated_recommendations(self):
        """Phase 3: Generate integrated recommendations from all agent findings"""
        self.log("=" * 60)
        self.log("PHASE 3: INTEGRATED RECOMMENDATIONS")
        self.log("=" * 60)

        recommendations = []

        # Priority 1: Critical issues from MT5 agent
        mt5_findings = self.context["shared_findings"].get("mt5_agent", {})
        issue_types = mt5_findings.get("issue_types", {})

        if issue_types.get("unreachable_code", 0) > 0:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "code_quality",
                "title": "Remove Unreachable Code",
                "description": f"Found {issue_types['unreachable_code']} instances of unreachable code after return statements",
                "action": "Delete all code after unconditional return statements",
                "estimated_time": "30-60 minutes",
                "files_affected": self._get_files_with_unreachable_code()
            })

        if issue_types.get("potentially_unused_variable", 0) > 0:
            recommendations.append({
                "priority": "HIGH",
                "category": "code_quality",
                "title": "Remove Unused Variables",
                "description": f"Found {issue_types['potentially_unused_variable']} potentially unused variables",
                "action": "Review and remove variables that are declared but never used",
                "estimated_time": "2-3 hours",
                "files_affected": self._get_files_with_unused_vars()
            })

        if issue_types.get("commented_code", 0) > 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "code_quality",
                "title": "Clean Up Commented Code",
                "description": f"Found {issue_types['commented_code']} blocks of commented-out code",
                "action": "Delete commented code blocks (use git for version history)",
                "estimated_time": "1-2 hours",
                "files_affected": self._get_files_with_commented_code()
            })

        # Priority 2: Specific file recommendations
        top_files = mt5_findings.get("top_files", [])
        for i, file_info in enumerate(top_files[:3], 1):
            recommendations.append({
                "priority": "HIGH" if i == 1 else "MEDIUM",
                "category": "file_cleanup",
                "title": f"Clean Up {file_info['name']}",
                "description": f"{file_info['issues']} issues in {file_info['lines']} lines",
                "action": f"Systematically review and fix all issues in {file_info['name']}",
                "estimated_time": f"{max(1, file_info['issues'] // 30)} hours",
                "files_affected": [file_info['name']]
            })

        # Priority 3: MQL5-specific recommendations
        mql5_patterns = self.context["shared_findings"].get("mql5_patterns", {})

        # Check for memory management patterns
        memory_heavy_files = [
            name for name, patterns in mql5_patterns.items()
            if patterns.get("memory_management", 0) > 10
        ]
        if memory_heavy_files:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "mql5_best_practices",
                "title": "Review Memory Management",
                "description": f"{len(memory_heavy_files)} files with heavy memory operations",
                "action": "Ensure proper ArrayFree() calls and memory cleanup",
                "estimated_time": "1-2 hours",
                "files_affected": memory_heavy_files
            })

        # Check for error handling
        files_without_error_handling = [
            name for name, patterns in mql5_patterns.items()
            if patterns.get("error_handling", 0) == 0 and name.endswith('.mq5')
        ]
        if files_without_error_handling:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "mql5_best_practices",
                "title": "Add Error Handling",
                "description": f"{len(files_without_error_handling)} main files without error handling",
                "action": "Add GetLastError() checks after critical operations",
                "estimated_time": "2-3 hours",
                "files_affected": files_without_error_handling
            })

        self.context["integrated_recommendations"] = recommendations
        self.log(f"Generated {len(recommendations)} integrated recommendations")

        return recommendations

    def _get_files_with_unreachable_code(self) -> List[str]:
        """Get list of files with unreachable code"""
        files = []
        if self.results["mt5_agent"]:
            for file_data in self.results["mt5_agent"]["files_analyzed"]:
                for issue in file_data.get("unused_logic", []):
                    if issue["type"] == "unreachable_code":
                        files.append(file_data["file_name"])
                        break
        return list(set(files))

    def _get_files_with_unused_vars(self) -> List[str]:
        """Get list of files with unused variables"""
        files = []
        if self.results["mt5_agent"]:
            for file_data in self.results["mt5_agent"]["files_analyzed"]:
                for issue in file_data.get("unused_logic", []):
                    if issue["type"] == "potentially_unused_variable":
                        files.append(file_data["file_name"])
                        break
        return list(set(files))

    def _get_files_with_commented_code(self) -> List[str]:
        """Get list of files with commented code"""
        files = []
        if self.results["mt5_agent"]:
            for file_data in self.results["mt5_agent"]["files_analyzed"]:
                for issue in file_data.get("unused_logic", []):
                    if issue["type"] == "commented_code":
                        files.append(file_data["file_name"])
                        break
        return list(set(files))

    async def save_orchestration_results(self):
        """Save final orchestration results"""
        output_file = SCRIPT_DIR / f"orchestration_results_{self.session_id}.json"

        output_data = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "context": self.context,
            "recommendations": self.context["integrated_recommendations"],
            "summary": {
                "total_recommendations": len(self.context["integrated_recommendations"]),
                "critical_priority": sum(1 for r in self.context["integrated_recommendations"] if r["priority"] == "CRITICAL"),
                "high_priority": sum(1 for r in self.context["integrated_recommendations"] if r["priority"] == "HIGH"),
                "medium_priority": sum(1 for r in self.context["integrated_recommendations"] if r["priority"] == "MEDIUM"),
            }
        }

        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)

        self.log(f"Orchestration results saved to {output_file}")

        # Also create markdown report
        await self.create_markdown_report(output_file.with_suffix('.md'))

    async def create_markdown_report(self, output_file: Path):
        """Create comprehensive markdown report"""
        with open(output_file, 'w') as f:
            f.write("# Multi-Agent Orchestration Results\n\n")
            f.write(f"**Session ID:** {self.session_id}\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Target:** `{FTMO_LIVE_DIR}`\n\n")

            f.write("## Executive Summary\n\n")

            # MT5 Agent Summary
            if self.context["shared_findings"].get("mt5_agent"):
                mt5 = self.context["shared_findings"]["mt5_agent"]
                f.write("### MT5 Infinite Reliability Agent\n\n")
                f.write(f"- **Total Issues:** {mt5['total_issues']}\n")
                f.write(f"- **Files Affected:** {mt5['files_with_issues']}\n\n")

                f.write("#### Issue Breakdown\n\n")
                for issue_type, count in mt5["issue_types"].items():
                    if count > 0:
                        f.write(f"- **{issue_type.replace('_', ' ').title()}:** {count}\n")
                f.write("\n")

            # MQL5 Pattern Analysis
            if self.context["shared_findings"].get("mql5_patterns"):
                patterns = self.context["shared_findings"]["mql5_patterns"]
                f.write("### MQL5 Language Pattern Analysis\n\n")
                f.write(f"Analyzed {len(patterns)} files for MQL5-specific patterns\n\n")

            # Recommendations
            f.write("## Integrated Recommendations\n\n")
            f.write(f"Generated {len(self.context['integrated_recommendations'])} recommendations\n\n")

            # Group by priority
            for priority in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                recs = [r for r in self.context["integrated_recommendations"] if r["priority"] == priority]
                if recs:
                    f.write(f"### {priority} Priority ({len(recs)} items)\n\n")
                    for i, rec in enumerate(recs, 1):
                        f.write(f"#### {i}. {rec['title']}\n\n")
                        f.write(f"- **Category:** {rec['category']}\n")
                        f.write(f"- **Description:** {rec['description']}\n")
                        f.write(f"- **Action:** {rec['action']}\n")
                        f.write(f"- **Estimated Time:** {rec['estimated_time']}\n")
                        f.write(f"- **Files Affected:** {', '.join(rec['files_affected'][:5])}")
                        if len(rec['files_affected']) > 5:
                            f.write(f" (+{len(rec['files_affected']) - 5} more)")
                        f.write("\n\n")

            f.write("---\n\n")
            f.write("**Next Steps:**\n\n")
            f.write("1. Review recommendations by priority\n")
            f.write("2. Create feature branch for fixes\n")
            f.write("3. Implement fixes incrementally with testing\n")
            f.write("4. Commit after each file cleanup\n\n")

        self.log(f"Markdown report saved to {output_file}")

    async def orchestrate(self):
        """Main orchestration workflow"""
        self.log("="*80)
        self.log("MULTI-AGENT ORCHESTRATION SYSTEM")
        self.log("="*80)
        self.log(f"Session ID: {self.session_id}")
        self.log(f"Target: {FTMO_LIVE_DIR}")
        self.log("")

        try:
            # Phase 1: MT5 Agent
            success = await self.run_mt5_reliability_agent()
            if not success:
                self.log("MT5 Agent phase failed. Aborting orchestration.", "ERROR")
                return False

            # Phase 2: MQL5 Pattern Analysis
            await self.analyze_mql5_language_patterns()

            # Phase 3: Generate Recommendations
            await self.generate_integrated_recommendations()

            # Phase 4: Save Results
            await self.save_orchestration_results()

            self.log("")
            self.log("="*80)
            self.log("ORCHESTRATION COMPLETE")
            self.log("="*80)
            self.log(f"Total Recommendations: {len(self.context['integrated_recommendations'])}")
            self.log(f"Results saved to: orchestration_results_{self.session_id}.json")
            self.log("")

            return True

        except Exception as e:
            self.log(f"Orchestration failed with error: {e}", "ERROR")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point"""
    orchestrator = MultiAgentOrchestrator()
    success = await orchestrator.orchestrate()

    if success:
        print("\n" + "="*80)
        print("✅ Multi-Agent Orchestration Successful!")
        print("="*80)
        print("\nNext Steps:")
        print("1. Review orchestration_results_*.md for prioritized recommendations")
        print("2. Start with CRITICAL priority items")
        print("3. Create git branch: cleanup/multi-agent-fixes")
        print("4. Implement fixes incrementally with testing")
        print("\n")
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ Multi-Agent Orchestration Failed")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
