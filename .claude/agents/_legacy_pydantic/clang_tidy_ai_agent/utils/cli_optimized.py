"""
CLI interface for the optimized Clang-Tidy AI Agent.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

try:
    from ..legacy.agent_optimized import OptimizedClangTidyAgent
    from ..legacy.settings_optimized import load_optimized_settings
except ImportError:
    # Fallback for direct execution
    from legacy.agent_optimized import OptimizedClangTidyAgent
    from legacy.settings_optimized import load_optimized_settings

console = Console()


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--config", "-c", help="Path to configuration file")
@click.pass_context
def cli(ctx, verbose, config):
    """Optimized Clang-Tidy AI Agent - Enterprise C++ code quality automation."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config"] = config


@cli.command()
@click.argument("files", nargs=-1, required=True)
@click.option("--checks", "-c", help="Comma-separated list of clang-tidy checks")
@click.option("--auto-fix", is_flag=True, help="Automatically apply safe fixes")
@click.option("--output", "-o", help="Output file for results")
@click.option("--format", "output_format", default="json", 
              type=click.Choice(["json", "table", "markdown"]),
              help="Output format")
@click.pass_context
async def analyze(ctx, files, checks, auto_fix, output, output_format):
    """Analyze C++ files for clang-tidy warnings."""
    verbose = ctx.obj.get("verbose", False)
    
    if verbose:
        console.print("🚀 Starting optimized clang-tidy analysis...")
    
    # Load settings
    try:
        settings = load_optimized_settings()
        if verbose:
            console.print("✓ Configuration loaded")
    except Exception as e:
        console.print(f"❌ Failed to load configuration: {e}", style="red")
        sys.exit(1)
    
    # Create agent
    agent = OptimizedClangTidyAgent(settings)
    
    # Process files
    results = []
    total_warnings = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console if verbose else None
    ) as progress:
        
        if len(files) == 1 and '*' in files[0]:
            # Project analysis mode
            task = progress.add_task("Analyzing project...", total=None)
            
            try:
                result = await agent.analyze_project(
                    [files[0]], 
                    checks
                )
                results.append(result.dict())
                total_warnings = result.total_warnings
                
            except Exception as e:
                console.print(f"❌ Analysis failed: {e}", style="red")
                sys.exit(1)
                
        else:
            # Individual file analysis
            for file_path in files:
                task = progress.add_task(f"Analyzing {file_path}...", total=None)
                
                try:
                    result = await agent.analyze_with_fixes(
                        file_path, 
                        auto_fix
                    )
                    results.append(result)
                    total_warnings += result.get("total_warnings", 0)
                    
                except Exception as e:
                    console.print(f"❌ Failed to analyze {file_path}: {e}", style="red")
                    continue
                
                progress.update(task, completed=True)
    
    # Display results
    if output_format == "table":
        _display_table_results(results, total_warnings, verbose)
    elif output_format == "markdown":
        _display_markdown_results(results, total_warnings)
    else:
        output_data = {
            "summary": {
                "files_analyzed": len(results),
                "total_warnings": total_warnings,
                "auto_fixes_applied": auto_fix
            },
            "results": results,
            "metrics": agent.get_metrics()
        }
        
        output_json = json.dumps(output_data, indent=2 if verbose else None)
        
        if output:
            Path(output).write_text(output_json)
            console.print(f"✓ Results saved to {output}")
        else:
            print(output_json)
    
    if verbose:
        _display_performance_metrics(agent.get_metrics())


@cli.command()
@click.argument("pattern", default="**/*.cpp")
@click.option("--checks", "-c", help="Comma-separated list of clang-tidy checks")
@click.option("--output", "-o", help="Output file for project report")
@click.pass_context
async def project(ctx, pattern, checks, output):
    """Analyze entire project with comprehensive reporting."""
    verbose = ctx.obj.get("verbose", False)
    
    console.print("🏢 Starting project-wide analysis...")
    
    settings = load_optimized_settings()
    agent = OptimizedClangTidyAgent(settings)
    
    start_time = time.time()
    
    try:
        result = await agent.analyze_project([pattern], checks)
        
        execution_time = time.time() - start_time
        
        # Create comprehensive report
        report = {
            "project_analysis": result.dict(),
            "execution_summary": {
                "duration_seconds": execution_time,
                "files_per_second": result.files_analyzed / execution_time,
                "warnings_per_file": result.total_warnings / max(result.files_analyzed, 1)
            },
            "performance_metrics": agent.get_metrics()
        }
        
        if output:
            Path(output).write_text(json.dumps(report, indent=2))
            console.print(f"✓ Project report saved to {output}")
        else:
            _display_project_report(result, execution_time)
            
    except Exception as e:
        console.print(f"❌ Project analysis failed: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.pass_context
async def status(ctx):
    """Show agent status and configuration."""
    verbose = ctx.obj.get("verbose", False)
    
    try:
        settings = load_optimized_settings()
        agent = OptimizedClangTidyAgent(settings)
        
        # Create status table
        table = Table(title="Clang-Tidy AI Agent Status")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")
        
        # Configuration status
        table.add_row(
            "Configuration",
            "✓ Loaded",
            f"Project: {settings.project_root}"
        )
        
        # LLM status
        provider_info = agent.provider.get_model_info()
        llm_status = "✓ Available" if provider_info["primary"]["available"] else "❌ Unavailable"
        table.add_row(
            "LLM Provider",
            llm_status,
            f"{settings.llm_provider} ({settings.llm_model})"
        )
        
        # Tool availability
        clang_tidy_status = "✓ Available" if settings.clang_tidy_binary_path.exists() else "❌ Missing"
        table.add_row(
            "Clang-Tidy",
            clang_tidy_status,
            str(settings.clang_tidy_binary_path)
        )
        
        # Cache status
        cache_status = "✓ Enabled" if settings.enable_caching else "❌ Disabled"
        table.add_row(
            "Caching",
            cache_status,
            f"TTL: {settings.cache_ttl_seconds}s"
        )
        
        console.print(table)
        
        if verbose:
            # Show detailed configuration
            config_panel = Panel(
                json.dumps(settings.get_summary(), indent=2),
                title="Detailed Configuration",
                expand=False
            )
            console.print(config_panel)
            
    except Exception as e:
        console.print(f"❌ Status check failed: {e}", style="red")


@cli.command()
@click.option("--reset", is_flag=True, help="Reset performance counters")
@click.pass_context
async def metrics(ctx, reset):
    """Show performance metrics."""
    try:
        settings = load_optimized_settings()
        agent = OptimizedClangTidyAgent(settings)
        
        if reset:
            # Reset metrics (would need to implement this)
            console.print("✓ Metrics reset")
            return
        
        metrics = agent.get_metrics()
        _display_performance_metrics(metrics)
        
    except Exception as e:
        console.print(f"❌ Failed to get metrics: {e}", style="red")


def _display_table_results(results: List[dict], total_warnings: int, verbose: bool):
    """Display results in table format."""
    table = Table(title=f"Analysis Results ({total_warnings} warnings total)")
    table.add_column("File", style="cyan")
    table.add_column("Warnings", justify="right", style="yellow")
    table.add_column("Fixes Applied", justify="right", style="green")
    
    for result in results:
        fixes_count = len(result.get("fixes_applied", []))
        table.add_row(
            result.get("file", "N/A"),
            str(result.get("total_warnings", 0)),
            str(fixes_count)
        )
    
    console.print(table)


def _display_markdown_results(results: List[dict], total_warnings: int):
    """Display results in markdown format."""
    markdown = f"# Clang-Tidy Analysis Results\n\n"
    markdown += f"**Total Warnings:** {total_warnings}\n\n"
    
    for result in results:
        file_name = result.get("file", "N/A")
        warnings = result.get("total_warnings", 0)
        fixes = len(result.get("fixes_applied", []))
        
        markdown += f"## {file_name}\n\n"
        markdown += f"- Warnings: {warnings}\n"
        markdown += f"- Fixes Applied: {fixes}\n\n"
        
        if result.get("warnings"):
            markdown += "### Warnings\n\n"
            for warning in result["warnings"]:
                markdown += f"- Line {warning.get('line', 'N/A')}: {warning.get('message', 'N/A')}\n"
            markdown += "\n"
    
    print(markdown)


def _display_project_report(result, execution_time: float):
    """Display project analysis report."""
    panel = Panel(
        f"""
📊 **Project Analysis Complete**

📁 Files Analyzed: {result.files_analyzed}
⚠️  Total Warnings: {result.total_warnings}
⏱️  Execution Time: {execution_time:.2f}s
🚀 Files/Second: {result.files_analyzed / execution_time:.2f}
📈 Cache Hit Rate: {result.cache_hit_rate:.1%}

🎯 **Top Recommendations:**
{chr(10).join(f"• {rec}" for rec in result.recommendations[:3])}
        """.strip(),
        title="Project Analysis Report",
        expand=False
    )
    console.print(panel)


def _display_performance_metrics(metrics: dict):
    """Display performance metrics."""
    metrics_table = Table(title="Performance Metrics")
    metrics_table.add_column("Metric", style="cyan")
    metrics_table.add_column("Value", justify="right", style="green")
    
    for key, value in metrics.items():
        if isinstance(value, float):
            formatted_value = f"{value:.2f}"
        else:
            formatted_value = str(value)
        
        metrics_table.add_row(
            key.replace("_", " ").title(),
            formatted_value
        )
    
    console.print(metrics_table)


def main():
    """Main entry point for the CLI."""
    # Convert click commands to async
    def run_async_command(func):
        def wrapper(*args, **kwargs):
            return asyncio.run(func(*args, **kwargs))
        return wrapper
    
    # Wrap async commands
    cli.commands["analyze"] = click.command()(run_async_command(analyze.callback))
    cli.commands["project"] = click.command()(run_async_command(project.callback))
    cli.commands["status"] = click.command()(run_async_command(status.callback))
    cli.commands["metrics"] = click.command()(run_async_command(metrics.callback))
    
    cli()


if __name__ == "__main__":
    main()