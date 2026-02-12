#!/usr/bin/env python3
"""
CLI interface for NEVER FAIL BUILD RESOLVER.

This provides a command-line interface to the build resolution agent,
compatible with the existing wire_ground build system.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.text import Text

from agent import (
    resolve_build_fast,
    resolve_build_smart,
    resolve_build_thorough,
    resolve_build_emergency,
    health_check
)

console = Console()
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('--health', is_flag=True, help='Check agent health status')
@click.pass_context
def cli(ctx, version, health):
    """
    NEVER FAIL BUILD RESOLVER - AI-powered C++ build problem resolution.
    
    The agent that NEVER gives up and ALWAYS finds a solution to ANY build problem.
    """
    if version:
        from . import __version__
        console.print(f"NEVER FAIL BUILD RESOLVER version {__version__}")
        return
    
    if health:
        asyncio.run(show_health_check())
        return
    
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@cli.command()
@click.argument('error_log_file', type=click.Path(exists=True), required=False)
@click.option('--project-path', '-p', default='.', 
              help='Path to project root (default: current directory)')
@click.option('--mode', '-m', 
              type=click.Choice(['fast', 'smart', 'thorough', 'emergency']),
              default='smart',
              help='Resolution mode (default: smart)')
@click.option('--interactive/--no-interactive', default=True,
              help='Interactive mode for step-by-step resolution')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def resolve(error_log_file, project_path, mode, interactive, verbose):
    """
    Resolve build problems using AI analysis and automated fixes.
    
    If ERROR_LOG_FILE is not provided, the agent will attempt to build
    the project and analyze any errors that occur.
    """
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    
    project_path = Path(project_path).resolve()
    
    if error_log_file:
        error_log = Path(error_log_file).read_text()
    else:
        console.print("🔨 No error log provided. Building project to capture errors...")
        error_log = asyncio.run(capture_build_errors(project_path))
        if not error_log:
            console.print("✅ Build succeeded! No problems to resolve.")
            return
    
    console.print(Panel(
        f"🚀 Starting NEVER FAIL BUILD RESOLVER\n"
        f"📁 Project: {project_path}\n"
        f"⚡ Mode: {mode.upper()}\n"
        f"🎯 Guarantee: We NEVER give up!",
        title="Build Problem Resolution",
        border_style="blue"
    ))
    
    # Run the resolution
    asyncio.run(run_resolution(error_log, str(project_path), mode, interactive))


@cli.command()
@click.argument('project_path', type=click.Path(exists=True), default='.')
@click.option('--mode', '-m',
              type=click.Choice(['fast', 'smart', 'thorough', 'emergency']),
              default='smart')
def fix_build(project_path, mode):
    """
    Drop-in replacement for ./scripts/fix_build.sh with AI resolution.
    
    This command provides the same interface as the existing bash script
    but uses AI-powered problem resolution.
    """
    project_path = Path(project_path).resolve()
    
    console.print(Panel(
        f"🤖 AI-Powered Build Resolution\n"
        f"📁 Project: {project_path}\n"
        f"⚡ Mode: {mode.upper()}\n"
        f"🔄 Replacing: ./scripts/fix_build.sh {mode}",
        title="NEVER FAIL BUILD RESOLVER",
        border_style="green"
    ))
    
    # Capture build errors and resolve
    asyncio.run(fix_build_workflow(str(project_path), mode))


@cli.command()
def status():
    """Show current agent status and configuration."""
    asyncio.run(show_detailed_status())


async def show_health_check():
    """Display health check results."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task("Checking agent health...", total=None)
        
        health = await health_check()
        progress.remove_task(task)
    
    if health["status"] == "healthy":
        console.print("✅ Agent is healthy and ready!", style="green")
        console.print(f"🤖 Model: {health.get('model_name', 'Unknown')}")
        console.print(f"📁 Project: {health.get('project_root', 'Unknown')}")
        console.print(f"🔧 CMake: {'✅' if health.get('cmake_available') else '❌'}")
        console.print(f"🧹 Clang-Tidy: {'✅' if health.get('clang_tidy_available') else '❌'}")
    else:
        console.print("❌ Agent health check failed!", style="red")
        console.print(f"Error: {health.get('error', 'Unknown error')}")


async def show_detailed_status():
    """Show detailed agent status."""
    health = await health_check()
    
    status_text = Text()
    status_text.append("NEVER FAIL BUILD RESOLVER Status\n\n", style="bold blue")
    
    if health["status"] == "healthy":
        status_text.append("Status: ", style="bold")
        status_text.append("OPERATIONAL", style="green")
        status_text.append("\n\n")
        
        status_text.append("Configuration:\n", style="bold")
        status_text.append(f"  • Model Provider: {health.get('model_provider', 'Unknown')}\n")
        status_text.append(f"  • Model Name: {health.get('model_name', 'Unknown')}\n")
        status_text.append(f"  • Project Root: {health.get('project_root', 'Unknown')}\n")
        status_text.append(f"  • MCP Enabled: {health.get('mcp_enabled', False)}\n")
        status_text.append(f"  • Learning Enabled: {health.get('learning_enabled', False)}\n")
        
        status_text.append("\nSystem Dependencies:\n", style="bold")
        status_text.append(f"  • CMake: {'Available' if health.get('cmake_available') else 'Missing'}\n")
        status_text.append(f"  • Clang-Tidy: {'Available' if health.get('clang_tidy_available') else 'Missing'}\n")
    else:
        status_text.append("Status: ", style="bold")
        status_text.append("ERROR", style="red")
        status_text.append(f"\nError: {health.get('error', 'Unknown error')}\n")
    
    console.print(Panel(status_text, title="Agent Status", border_style="blue"))


async def capture_build_errors(project_path: Path) -> str:
    """Capture build errors by attempting to build the project."""
    try:
        # Try to build using the standard wire_ground command
        process = await asyncio.create_subprocess_shell(
            "/.jbdevcontainer/JetBrains/RemoteDev/dist/243a1514282d0_CLion-2025.2/bin/cmake/linux/x64/bin/cmake --build cmake-build-debug --target wire_ground_tests",
            cwd=project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )
        
        stdout, _ = await process.communicate()
        output = stdout.decode('utf-8', errors='ignore')
        
        if process.returncode != 0:
            return output
        else:
            return ""  # Build succeeded, no errors
            
    except Exception as e:
        console.print(f"❌ Error capturing build output: {e}", style="red")
        return ""


async def run_resolution(error_log: str, project_path: str, mode: str, interactive: bool):
    """Run the resolution process with progress display."""
    mode_functions = {
        'fast': resolve_build_fast,
        'smart': resolve_build_smart,
        'thorough': resolve_build_thorough,
        'emergency': resolve_build_emergency
    }
    
    resolve_func = mode_functions[mode]
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(f"Resolving build problems in {mode} mode...", total=None)
        
        try:
            result = await resolve_func(error_log, project_path)
            progress.remove_task(task)
            
            if result["success"]:
                console.print("🎉 Build problems resolved successfully!", style="green")
                console.print(f"📊 Resolution completed in {mode} mode")
                console.print(f"🆔 Session ID: {result['session_id']}")
            else:
                console.print("❌ Resolution failed:", style="red")
                console.print(f"Error: {result.get('error', 'Unknown error')}")
                
                if interactive:
                    console.print("\n🔄 Would you like to try a different mode?")
                    # Interactive escalation logic would go here
                    
        except Exception as e:
            progress.remove_task(task)
            console.print(f"💥 Unexpected error during resolution: {e}", style="red")


async def fix_build_workflow(project_path: str, mode: str):
    """Complete fix build workflow matching the bash script interface."""
    # First capture current build state
    error_log = await capture_build_errors(Path(project_path))
    
    if not error_log:
        console.print("✅ Build already successful - no fixes needed!", style="green")
        return
    
    # Run resolution
    await run_resolution(error_log, project_path, mode, interactive=False)
    
    # Verify the fix by building again
    console.print("\n🔍 Verifying resolution by rebuilding...")
    verification_log = await capture_build_errors(Path(project_path))
    
    if not verification_log:
        console.print("🎉 BUILD SUCCESS! Resolution verified.", style="green bold")
        console.print("✨ NEVER FAIL BUILD RESOLVER: Mission Accomplished!")
    else:
        console.print("⚠️  Build still has issues. Escalating to thorough mode...", style="yellow")
        if mode != "thorough":
            await run_resolution(verification_log, project_path, "thorough", interactive=False)


if __name__ == '__main__':
    cli()