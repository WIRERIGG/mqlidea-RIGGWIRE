"""Command-line interface for BLITZFIRE C++ Optimizer Agent."""

import asyncio
import argparse
from pathlib import Path
from typing import Optional

from pydantic_ai import Agent
from dependencies import BlitzfireDependencies
from models import OptimizationRequest, OptimizationLevel, OptimizationDomain
from settings import load_settings


async def optimize_code(
    code: str, 
    level: str = "standard", 
    domain: str = "general",
    file_path: Optional[str] = None
) -> str:
    """Optimize C++ code using the Blitzfire agent."""
    settings = load_settings()
    deps = BlitzfireDependencies()
    await deps.initialize()
    
    try:
        # Map string levels to enum values
        level_map = {
            "conservative": OptimizationLevel.CONSERVATIVE,
            "standard": OptimizationLevel.STANDARD,
            "advanced": OptimizationLevel.ADVANCED,
            "extreme": OptimizationLevel.EXTREME
        }
        
        domain_map = {
            "general": OptimizationDomain.GENERAL,
            "hft": OptimizationDomain.HFT,
            "game": OptimizationDomain.GAME_DEV,
            "embedded": OptimizationDomain.EMBEDDED,
            "scientific": OptimizationDomain.SCIENTIFIC
        }
        
        # Create optimization request
        request = OptimizationRequest(
            code=code,
            optimization_level=level_map.get(level, OptimizationLevel.STANDARD),
            focus_domains=[domain_map.get(domain, OptimizationDomain.GENERAL)],
            file_path=file_path
        )
        
        # Create and run agent
        from agent import create_blitzfire_agent
        agent = create_blitzfire_agent(deps)
        
        result = await agent.run("Optimize this C++ code", request)
        return result.data
        
    finally:
        await deps.cleanup()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="BLITZFIRE C++ Optimizer")
    parser.add_argument("file", nargs="?", help="C++ file to optimize")
    parser.add_argument("--code", "-c", help="C++ code string to optimize")
    parser.add_argument(
        "--level", "-l", 
        choices=["conservative", "standard", "advanced", "extreme"],
        default="standard",
        help="Optimization level"
    )
    parser.add_argument(
        "--domain", "-d",
        choices=["general", "hft", "game", "embedded", "scientific"],
        default="general",
        help="Optimization domain focus"
    )
    parser.add_argument("--output", "-o", help="Output file path")
    
    args = parser.parse_args()
    
    # Get code from file or command line
    if args.file:
        code_file = Path(args.file)
        if not code_file.exists():
            print(f"Error: File {args.file} not found")
            return 1
        code = code_file.read_text()
        file_path = str(code_file)
    elif args.code:
        code = args.code
        file_path = None
    else:
        print("Error: Must provide either --code or a file path")
        return 1
    
    # Run optimization
    try:
        result = asyncio.run(optimize_code(code, args.level, args.domain, file_path))
        
        if args.output:
            Path(args.output).write_text(result)
            print(f"Optimized code written to {args.output}")
        else:
            print("Optimized code:")
            print("=" * 50)
            print(result)
            
        return 0
        
    except Exception as e:
        print(f"Error during optimization: {e}")
        return 1


if __name__ == "__main__":
    exit(main())