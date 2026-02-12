#!/usr/bin/env python3
"""
Simple test script for the NEVER FAIL BUILD RESOLVER CLI.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help='Show version and exit')
@click.option('--health', is_flag=True, help='Check agent health status')
@click.pass_context
def test_cli(ctx, version, health):
    """Test CLI for NEVER FAIL BUILD RESOLVER."""
    if version:
        console.print("NEVER FAIL BUILD RESOLVER test version 1.0.0")
        return
    
    if health:
        console.print("✅ Test CLI is operational!")
        return
    
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())

@test_cli.command()
@click.argument('project_path', type=click.Path(), default='.')
@click.option('--mode', '-m',
              type=click.Choice(['fast', 'smart', 'thorough', 'emergency']),
              default='smart')
def test_resolve(project_path, mode):
    """Test resolution command."""
    console.print(Panel(
        f"🧪 TEST MODE - Build Resolution\n"
        f"📁 Project: {project_path}\n"
        f"⚡ Mode: {mode.upper()}\n"
        f"🔄 This is a test of the CLI interface",
        title="TEST NEVER FAIL BUILD RESOLVER",
        border_style="yellow"
    ))
    
    console.print(f"✅ Test command executed successfully!")
    console.print(f"💡 In a real scenario, this would resolve build problems in {mode} mode")

@test_cli.command()
def test_status():
    """Test status command."""
    console.print(Panel(
        "🧪 TEST STATUS\n"
        "✅ CLI Interface: Working\n"
        "✅ Rich Display: Working\n" 
        "✅ Click Commands: Working\n"
        "⚠️  Agent Backend: Not loaded (test mode)",
        title="Test Status",
        border_style="blue"
    ))

if __name__ == '__main__':
    test_cli()