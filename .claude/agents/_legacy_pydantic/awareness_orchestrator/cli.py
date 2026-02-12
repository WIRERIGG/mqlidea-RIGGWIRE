"""
CLI interface for Awareness Orchestrator.

Provides command-line access to orchestration capabilities.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional
import argparse

from .agent import orchestrate, analyze_file
from .dependencies import OrchestrationDeps, get_dependencies
from .models import OrchestrationResult, AgentFindings


def print_findings(findings: AgentFindings):
    """Pretty-print agent findings."""
    print(f"\n{'='*70}")
    print(f"🤖 {findings.agent_type.value.upper()} AGENT RESULTS")
    print(f"{'='*70}")
    print(f"Duration: {findings.duration:.2f}s")
    print(f"Summary: {findings.summary}\n")

    if findings.findings:
        print(f"Findings ({len(findings.findings)}):")
        for i, finding in enumerate(findings.findings, 1):
            severity_emoji = {
                "critical": "🔴",
                "high": "🟠",
                "medium": "🟡",
                "low": "🟢",
                "info": "ℹ️"
            }
            emoji = severity_emoji.get(finding.severity.value, "•")

            print(f"\n{i}. {emoji} {finding.title} [{finding.severity.value}]")
            print(f"   {finding.description}")
            if finding.file_path:
                location = f"{finding.file_path}"
                if finding.line_number:
                    location += f":{finding.line_number}"
                print(f"   📍 {location}")
            if finding.recommendation:
                print(f"   💡 {finding.recommendation}")


def print_orchestration_result(result: OrchestrationResult):
    """Pretty-print orchestration results."""
    print(f"\n{'='*70}")
    print(f"🎯 ORCHESTRATION COMPLETE")
    print(f"{'='*70}")
    print(f"Success: {'✅' if result.success else '❌'}")
    print(f"Total Duration: {result.total_duration:.2f}s")
    print(f"Agents Executed: {len(result.agent_findings)}\n")

    # Print findings from each agent
    for findings in result.agent_findings:
        print_findings(findings)

    # Print summary
    print(f"\n{'='*70}")
    print(f"📋 SUMMARY")
    print(f"{'='*70}")
    print(result.summary)

    # Print recommendations
    if result.recommendations:
        print(f"\n💡 RECOMMENDATIONS ({len(result.recommendations)}):")
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")

    # Print errors if any
    if result.errors:
        print(f"\n❌ ERRORS ({len(result.errors)}):")
        for error in result.errors:
            print(f"  • {error}")


async def run_orchestration(
    file_path: str,
    task: str,
    project_root: Optional[str] = None,
    build_dir: Optional[str] = None
):
    """Run full orchestration."""
    # Setup dependencies
    deps = get_dependencies(
        project_root=Path(project_root) if project_root else None,
        build_dir=Path(build_dir) if build_dir else None
    )

    print(f"🚀 Starting Awareness Orchestrator")
    print(f"📁 File: {file_path}")
    print(f"📝 Task: {task}\n")

    try:
        result = await orchestrate(file_path, task, deps)
        print_orchestration_result(result)

        # Show dashboard
        if result.success:
            print(f"\n{'='*70}")
            print("📊 METRICS DASHBOARD")
            print(f"{'='*70}")
            dashboard = deps.generate_dashboard()
            print(dashboard)

    except Exception as e:
        print(f"\n❌ Orchestration failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


async def run_analysis(
    file_path: str,
    context: str = "",
    project_root: Optional[str] = None,
    build_dir: Optional[str] = None
):
    """Run analysis agent only."""
    deps = get_dependencies(
        project_root=Path(project_root) if project_root else None,
        build_dir=Path(build_dir) if build_dir else None
    )

    print(f"🔍 Running Analysis Agent")
    print(f"📁 File: {file_path}\n")

    try:
        findings = await analyze_file(file_path, context, deps)
        print_findings(findings)

    except Exception as e:
        print(f"\n❌ Analysis failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


def show_dashboard(
    project_root: Optional[str] = None,
    build_dir: Optional[str] = None
):
    """Show metrics dashboard."""
    deps = get_dependencies(
        project_root=Path(project_root) if project_root else None,
        build_dir=Path(build_dir) if build_dir else None
    )

    print("📊 AWARENESS ORCHESTRATOR METRICS")
    print(f"{'='*70}")
    dashboard = deps.generate_dashboard()
    print(dashboard)


def list_agents():
    """List all available Awareness Orchestrator agents."""
    from pathlib import Path

    print("=" * 70)
    print("AWARENESS ORCHESTRATOR - Available Agents")
    print("=" * 70)
    print()

    agents_dir = Path(__file__).parent.parent.parent
    agent_files = [
        ("awareness-orchestrator.md", "Main Orchestrator", "Full multi-agent coordination system"),
        ("awareness-orchestrator-analysis.md", "Analysis Agent", "Code quality and structural analysis"),
        ("awareness-orchestrator-architecture.md", "Architecture Agent", "Design patterns and modularization"),
        ("awareness-orchestrator-validation.md", "Validation Agent", "Testing strategy and QA planning")
    ]

    for i, (filename, name, description) in enumerate(agent_files, 1):
        agent_path = agents_dir / filename
        status = "✅" if agent_path.exists() else "❌"

        print(f"{i}. {name} {status}")
        print(f"   {description}")
        print(f"   File: .claude/agents/{filename}")

        if agent_path.exists():
            # Try to read the YAML frontmatter
            try:
                with open(agent_path) as f:
                    content = f.read()
                    if content.startswith("---"):
                        # Extract name from frontmatter
                        lines = content.split("\n")
                        for line in lines[1:10]:
                            if line.startswith("name:"):
                                agent_name = line.split(":", 1)[1].strip()
                                print(f"   Agent Name: {agent_name}")
                                break
            except:
                pass

        print()

    print("=" * 70)
    print(f"Total Agents: {len([f for f in agent_files if (agents_dir / f[0]).exists()])}/{len(agent_files)}")
    print("=" * 70)
    print()
    print("Usage:")
    print("  # Use main orchestrator (coordinates all agents)")
    print("  python -m awareness_orchestrator orchestrate <file> <task>")
    print()
    print("  # Use individual agent (via Claude Code)")
    print("  # Claude Code automatically selects agents based on task")
    print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Awareness Orchestrator - Intelligent Code Analysis System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full orchestration
  python -m awareness_orchestrator orchestrate tests/safe_test.cpp "Analyze for improvements"

  # Analysis only
  python -m awareness_orchestrator analyze include/blitzfire_trading.hpp

  # Show metrics dashboard
  python -m awareness_orchestrator dashboard

  # List available agents
  python -m awareness_orchestrator --agents
        """
    )

    parser.add_argument(
        "--agents",
        action="store_true",
        help="List all available Awareness Orchestrator agents"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        help="Project root directory (default: /IdeaProjects/wire_ground)"
    )
    parser.add_argument(
        "--build-dir",
        type=str,
        help="Build directory (default: <project-root>/cmake-build-debug)"
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Orchestrate command
    orchestrate_parser = subparsers.add_parser(
        "orchestrate",
        help="Run full orchestration with all agents"
    )
    orchestrate_parser.add_argument("file", help="File to analyze")
    orchestrate_parser.add_argument("task", help="Task description")

    # Analyze command
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Run analysis agent only"
    )
    analyze_parser.add_argument("file", help="File to analyze")
    analyze_parser.add_argument(
        "--context",
        default="",
        help="Additional context for analysis"
    )

    # Dashboard command
    subparsers.add_parser("dashboard", help="Show metrics dashboard")

    args = parser.parse_args()

    # Handle --agents flag
    if args.agents:
        list_agents()
        sys.exit(0)

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == "orchestrate":
        asyncio.run(run_orchestration(
            args.file,
            args.task,
            args.project_root,
            args.build_dir
        ))
    elif args.command == "analyze":
        asyncio.run(run_analysis(
            args.file,
            args.context,
            args.project_root,
            args.build_dir
        ))
    elif args.command == "dashboard":
        show_dashboard(args.project_root, args.build_dir)


if __name__ == "__main__":
    main()
