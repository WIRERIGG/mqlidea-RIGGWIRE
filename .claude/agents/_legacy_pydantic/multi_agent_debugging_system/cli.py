"""
Command-line interface for Multi-Agent Debugging System.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional

import click
from .agent import analyze_cpp_code, AnalysisResult


@click.group()
@click.version_option()
def cli():
    """Multi-Agent Debugging System for C++ code analysis."""
    pass


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.option('--analysis-mode', '-m',
              type=click.Choice(['static', 'dynamic', 'comprehensive']),
              default='comprehensive',
              help='Type of analysis to perform')
@click.option('--output-format', '-o',
              type=click.Choice(['json', 'human', 'both']),
              default='both',
              help='Output format')
@click.option('--max-parallel', '-p',
              type=int, default=4,
              help='Maximum parallel tool executions')
@click.option('--timeout', '-t',
              type=int, default=300,
              help='Analysis timeout in seconds')
@click.option('--output-file', '-f',
              type=click.Path(),
              help='Output file path (optional)')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def analyze(
    target_path: str,
    analysis_mode: str,
    output_format: str,
    max_parallel: int,
    timeout: int,
    output_file: Optional[str],
    verbose: bool
):
    """Analyze C++ code with multi-agent debugging system."""

    async def run_analysis():
        if verbose:
            click.echo(f"🚀 Starting {analysis_mode} analysis of {target_path}")
            click.echo(f"📊 Configuration: {max_parallel} parallel tools, {timeout}s timeout")

        try:
            result = await analyze_cpp_code(
                target_path=target_path,
                analysis_mode=analysis_mode,
                output_format=output_format,
                max_parallel_tools=max_parallel,
                timeout=timeout
            )

            # Display results
            if output_format in ['human', 'both']:
                click.echo("\n" + "="*60)
                click.echo("📋 MULTI-AGENT DEBUGGING ANALYSIS REPORT")
                click.echo("="*60)
                click.echo(result.human_readable_report)

                if verbose:
                    click.echo(f"\n📊 Analysis Summary:")
                    click.echo(f"   Session ID: {result.session_id}")
                    click.echo(f"   Execution Time: {result.execution_time:.2f}s")
                    click.echo(f"   Tools Executed: {', '.join(result.tools_executed)}")
                    click.echo(f"   Total Issues: {result.total_issues}")
                    click.echo(f"   Critical Issues: {result.critical_issues}")

            if output_format in ['json', 'both']:
                json_output = result.model_dump_json(indent=2)
                if output_format == 'json':
                    click.echo(json_output)
                elif verbose:
                    click.echo(f"\n📝 JSON Report available")

            # Save to file if requested
            if output_file:
                output_path = Path(output_file)
                if output_format == 'json':
                    output_path.write_text(result.model_dump_json(indent=2))
                else:
                    output_path.write_text(result.human_readable_report)
                click.echo(f"💾 Results saved to: {output_file}")

            # Exit code based on critical issues
            sys.exit(1 if result.critical_issues > 0 else 0)

        except Exception as e:
            click.echo(f"❌ Analysis failed: {str(e)}", err=True)
            sys.exit(1)

    # Run async analysis
    asyncio.run(run_analysis())


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.option('--tools', '-t', multiple=True,
              type=click.Choice(['gdb', 'strace', 'ltrace', 'perf', 'cppcheck', 'clang-tidy', 'valgrind',
                               'asan', 'ubsan', 'tsan', 'ai-clang-tidy', 'build-safety']),
              help='Specific tools to run')
def quick(target_path: str, tools: tuple):
    """Quick analysis with specific tools only."""

    async def run_quick_analysis():
        try:
            # Import here to avoid circular imports
            from .tools import run_debugging_tool
            from .dependencies import create_debugging_context, AgentDependencies, AnalysisMode
            from pydantic_ai import RunContext

            click.echo(f"🏃 Quick analysis of {target_path}")

            context = create_debugging_context(target_path, AnalysisMode.COMPREHENSIVE)
            deps = AgentDependencies(context=context, message_queue=[], results_cache={})

            selected_tools = list(tools) if tools else ['cppcheck', 'clang-tidy']

            results = []
            for tool in selected_tools:
                click.echo(f"   Running {tool}...")
                result = await run_debugging_tool(
                    RunContext(deps=deps),
                    tool,
                    target_path
                )
                results.append(result)

            # Quick summary
            total_issues = sum(len(r.get('issues', [])) for r in results)
            click.echo(f"\n📊 Quick Results:")
            click.echo(f"   Tools: {', '.join(selected_tools)}")
            click.echo(f"   Issues Found: {total_issues}")

            for result in results:
                if result.get('success') and result.get('issues'):
                    click.echo(f"\n{result['tool_name'].upper()}:")
                    for issue in result['issues'][:3]:  # Show top 3 issues
                        severity = issue.get('severity', 'unknown').upper()
                        message = issue.get('message', 'No message')[:80]
                        click.echo(f"   [{severity}] {message}")

        except Exception as e:
            click.echo(f"❌ Quick analysis failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_quick_analysis())


@cli.command()
def check():
    """Check system requirements and tool availability."""

    click.echo("🔧 Checking Multi-Agent Debugging System requirements...\n")

    # Check Python packages
    required_packages = [
        'pydantic_ai',
        'pydantic_settings',
        'click',
        'python-dotenv'
    ]

    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            click.echo(f"✅ {package}")
        except ImportError:
            click.echo(f"❌ {package} - Missing")

    # Check system tools
    import subprocess
    system_tools = {
        'gdb': 'GNU Debugger',
        'strace': 'System call tracer',
        'ltrace': 'Library call tracer',
        'perf': 'Performance analysis tool',
        'cppcheck': 'Static analysis tool',
        'clang-tidy': 'Clang-based linter',
        'valgrind': 'Memory error detector',
        'clang++': 'Clang compiler (for sanitizers)'
    }

    click.echo("\n🛠️  System Tools:")
    for tool, description in system_tools.items():
        try:
            result = subprocess.run([tool, '--version'],
                                  capture_output=True,
                                  check=True)
            click.echo(f"✅ {tool} - {description}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            click.echo(f"❌ {tool} - {description} (Not found)")

    # Check LLM configuration
    click.echo("\n🤖 LLM Configuration:")
    try:
        from .providers import validate_llm_configuration
        if validate_llm_configuration():
            click.echo("✅ LLM provider configured")
        else:
            click.echo("❌ LLM provider not configured")
    except Exception as e:
        click.echo(f"❌ LLM configuration error: {e}")

    click.echo("\n📝 Setup Instructions:")
    click.echo("   1. Install missing Python packages: pip install -r requirements.txt")
    click.echo("   2. Install missing system tools via package manager")
    click.echo("   3. Create .env file with LLM_API_KEY")
    click.echo("   4. Run 'multi-agent-debug analyze --help' for usage")


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
def demo(target_path: str):
    """Run demo analysis with detailed explanations."""

    async def run_demo():
        click.echo("🎯 Multi-Agent Debugging System Demo")
        click.echo("="*50)

        click.echo(f"\n📁 Target: {target_path}")
        click.echo("🤖 Agents: Lead, Tool Agents (GDB, Strace, Cppcheck, etc.), Detail, Plan")
        click.echo("📊 Mode: Comprehensive (static + dynamic)")

        click.echo("\n⏳ Starting comprehensive analysis...")
        click.echo("   This will demonstrate the multi-agent workflow:")
        click.echo("   1. 🎯 Plan Agent creates execution strategy")
        click.echo("   2. ⚡ Tool Agents run in parallel")
        click.echo("   3. 🔍 Detail Agent correlates findings")
        click.echo("   4. 📋 Lead Agent generates report")

        try:
            result = await analyze_cpp_code(
                target_path=target_path,
                analysis_mode="comprehensive",
                output_format="both",
                max_parallel_tools=3,
                timeout=180
            )

            click.echo(f"\n✅ Demo completed in {result.execution_time:.1f}s")
            click.echo(f"🔍 Analysis Results:")
            click.echo(f"   - Tools executed: {len(result.tools_executed)}")
            click.echo(f"   - Issues found: {result.total_issues}")
            click.echo(f"   - Critical issues: {result.critical_issues}")
            click.echo(f"   - Recommendations: {len(result.recommendations)}")

            if result.recommendations:
                click.echo(f"\n🎯 Top Recommendations:")
                for i, rec in enumerate(result.recommendations[:3], 1):
                    click.echo(f"   {i}. {rec}")

            click.echo("\n📊 Full report generated above ⬆️")

        except Exception as e:
            click.echo(f"❌ Demo failed: {str(e)}", err=True)

    asyncio.run(run_demo())


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
@click.option('--correlation-threshold', '-c',
              type=float, default=0.7,
              help='Correlation threshold (0.0-1.0)')
@click.option('--priority-mode', '-p',
              type=click.Choice(['smart', 'severity', 'consensus', 'confidence']),
              default='smart',
              help='Prioritization strategy')
@click.option('--show-matrix', is_flag=True,
              help='Show correlation matrix')
@click.option('--show-metrics', is_flag=True,
              help='Show advanced metrics')
def correlate(target_path: str, correlation_threshold: float, priority_mode: str,
              show_matrix: bool, show_metrics: bool):
    """Advanced correlation analysis with sophisticated pattern recognition."""

    async def run_correlation():
        try:
            click.echo("🧠 Advanced Correlation Analysis")
            click.echo("="*50)
            click.echo(f"📁 Target: {target_path}")
            click.echo(f"🎯 Threshold: {correlation_threshold}")
            click.echo(f"📊 Priority Mode: {priority_mode}")

            # Import here to avoid circular imports
            from .tools import run_debugging_tool, correlate_findings
            from .dependencies import create_debugging_context, AgentDependencies, AnalysisMode, ToolType
            from pydantic_ai import RunContext

            context = create_debugging_context(target_path, AnalysisMode.COMPREHENSIVE)
            deps = AgentDependencies(context=context, message_queue=[], results_cache={})
            ctx = RunContext(deps=deps)

            # Run all available tools
            click.echo("\n🚀 Running comprehensive tool suite...")
            all_tools = [tool.value for tool in ToolType if tool.value in
                        [t.value for t in context.available_tools]]

            tool_results = []
            for tool in all_tools:
                click.echo(f"   ⚡ {tool}...")
                try:
                    result = await run_debugging_tool(ctx, tool, target_path)
                    tool_results.append(result)
                except Exception as e:
                    click.echo(f"   ❌ {tool} failed: {str(e)}")

            # Perform advanced correlation
            click.echo("\n🔬 Performing advanced correlation analysis...")
            correlation_result = await correlate_findings(
                ctx, tool_results, correlation_threshold, priority_mode
            )

            if not correlation_result.get("correlation_success"):
                click.echo(f"❌ Correlation failed: {correlation_result.get('error')}")
                return

            # Display results
            summary = correlation_result["summary"]
            click.echo(f"\n📊 Correlation Results:")
            click.echo(f"   • Total Issues: {correlation_result['total_raw_issues']}")
            click.echo(f"   • Correlated Groups: {correlation_result['correlated_groups']}")
            click.echo(f"   • Critical Issues: {summary['critical_issues']}")
            click.echo(f"   • Security Issues: {summary['security_issues']}")
            click.echo(f"   • Chain Critical: {correlation_result['critical_chain_issues']}")
            click.echo(f"   • Risk Score: {summary['risk_score']:.2f}")
            click.echo(f"   • Tool Consensus: {summary['tools_consensus']:.2f}")

            # Show top priority issues
            issue_groups = correlation_result["issue_groups"]
            if issue_groups:
                click.echo(f"\n🎯 Top Priority Issues:")
                for i, group in enumerate(issue_groups[:5], 1):
                    rep = group["representative"]
                    priority = group["priority"].upper()
                    category = rep.get("category", "unknown")
                    risk_score = group.get("risk_score", 0.0)
                    consensus = len(group["tool_consensus"])

                    click.echo(f"   {i}. [{priority}] {category} (Risk: {risk_score:.2f}, Tools: {consensus})")
                    click.echo(f"      {rep.get('message', 'No message')[:80]}")
                    if group.get("is_chain_critical"):
                        click.echo("      🔗 CHAIN CRITICAL")

            # Show intelligent recommendations
            recommendations = correlation_result["recommendations"]
            if recommendations:
                click.echo(f"\n🎯 Intelligent Recommendations:")
                for i, rec in enumerate(recommendations[:8], 1):
                    click.echo(f"   {i}. {rec}")

            # Advanced metrics display
            if show_metrics:
                metrics = correlation_result["advanced_metrics"]
                click.echo(f"\n📈 Advanced Metrics:")
                click.echo(f"   • Overall Risk Score: {metrics['overall_risk_score']:.3f}")
                click.echo(f"   • Average Group Confidence: {metrics['avg_group_confidence']:.3f}")
                click.echo(f"   • Consensus Ratio: {metrics['consensus_ratio']:.3f}")
                click.echo(f"   • Chain Critical Ratio: {metrics['chain_critical_ratio']:.3f}")

                if metrics.get('tool_effectiveness'):
                    click.echo(f"   • Tool Effectiveness:")
                    for tool, eff in metrics['tool_effectiveness'].items():
                        click.echo(f"     - {tool}: {eff:.2f} issues/sec")

            # Correlation matrix display
            if show_matrix:
                matrix = correlation_result["correlation_matrix"]
                click.echo(f"\n🔗 Correlation Matrix:")

                tool_corr = matrix.get("tool_correlations", {})
                if tool_corr:
                    click.echo("   Tool Co-occurrences:")
                    for combo, count in sorted(tool_corr.items(), key=lambda x: x[1], reverse=True)[:5]:
                        click.echo(f"   • {combo}: {count} shared issues")

                cat_sev = matrix.get("category_severity_correlations", {})
                if cat_sev:
                    click.echo("   Category-Severity Patterns:")
                    for pattern, count in sorted(cat_sev.items(), key=lambda x: x[1], reverse=True)[:5]:
                        click.echo(f"   • {pattern}: {count} occurrences")

            click.echo(f"\n✅ Advanced correlation completed in {correlation_result['execution_time']:.2f}s")

        except Exception as e:
            click.echo(f"❌ Correlation analysis failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_correlation())


@cli.command()
@click.argument('target_path', type=click.Path(exists=True))
def sanitizers(target_path: str):
    """Run comprehensive sanitizer analysis (AddressSanitizer, UBSan, ThreadSanitizer)."""

    async def run_sanitizer_analysis():
        click.echo("🛡️ Comprehensive Sanitizer Analysis")
        click.echo("="*50)

        try:
            # Import here to avoid circular imports
            from .tools import run_debugging_tool
            from .dependencies import create_debugging_context, AgentDependencies, AnalysisMode
            from pydantic_ai import RunContext

            context = create_debugging_context(target_path, AnalysisMode.DYNAMIC)
            deps = AgentDependencies(context=context, message_queue=[], results_cache={})
            ctx = RunContext(deps=deps)

            sanitizers = ['asan', 'ubsan', 'tsan']
            results = {}

            for sanitizer in sanitizers:
                click.echo(f"\n🔍 Running {sanitizer.upper()}...")
                try:
                    result = await run_debugging_tool(ctx, sanitizer, target_path)
                    results[sanitizer] = result

                    if result.get('success'):
                        issues_count = len(result.get('issues', []))
                        click.echo(f"   ✅ {sanitizer.upper()}: {issues_count} issues found")

                        # Show top issues
                        for issue in result.get('issues', [])[:3]:
                            severity = issue.get('severity', 'unknown').upper()
                            category = issue.get('category', 'unknown')
                            message = issue.get('message', 'No message')[:60]
                            click.echo(f"   [{severity}] {category}: {message}")
                    else:
                        click.echo(f"   ❌ {sanitizer.upper()}: Failed to run")

                except Exception as e:
                    click.echo(f"   ❌ {sanitizer.upper()}: {str(e)}")

            # Summary
            total_issues = sum(len(r.get('issues', [])) for r in results.values() if r.get('success'))
            critical_issues = sum(1 for r in results.values() if r.get('success')
                                for issue in r.get('issues', [])
                                if issue.get('severity') == 'critical')

            click.echo(f"\n📊 Sanitizer Summary:")
            click.echo(f"   • Total Issues: {total_issues}")
            click.echo(f"   • Critical Issues: {critical_issues}")
            click.echo(f"   • Sanitizers Run: {len([r for r in results.values() if r.get('success')])}/3")

            if critical_issues > 0:
                click.echo(f"\n⚠️  Critical memory safety issues detected!")
                click.echo(f"   Immediate action required for {critical_issues} critical issues")

        except Exception as e:
            click.echo(f"❌ Sanitizer analysis failed: {str(e)}", err=True)
            sys.exit(1)

    asyncio.run(run_sanitizer_analysis())


if __name__ == '__main__':
    cli()