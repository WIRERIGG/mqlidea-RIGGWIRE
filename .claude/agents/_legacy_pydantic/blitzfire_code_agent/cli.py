"""Interactive CLI for the Blitzfire Code Agent."""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional, List
import json
import time

# ANSI color codes for terminal output
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'

    # Blitzfire brand colors
    FIRE = '\033[38;5;202m'  # Orange
    LIGHTNING = '\033[38;5;226m'  # Bright Yellow
    SUCCESS = '\033[38;5;46m'  # Bright Green


def print_banner():
    """Print the Blitzfire banner with style."""
    banner = f"""
{Colors.FIRE}{Colors.BOLD}
    ▄▄▄▄▄▄▄▄▄▄▄  ▄            ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄  ▄▄▄▄▄▄▄▄▄▄▄
   ▐░░░░░░░░░░░▌▐░▌          ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
   ▐░█▀▀▀▀▀▀▀▀▀ ▐░▌           ▀▀▀▀█░█▀▀▀▀  ▀▀▀▀█░█▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀  ▀▀▀▀█░█▀▀▀▀ ▐░█▀▀▀▀▀▀▀▀▀
   ▐░▌          ▐░▌               ▐░▌          ▐░▌     ▐░▌          ▐░▌               ▐░▌     ▐░▌
   ▐░█▄▄▄▄▄▄▄▄▄ ▐░▌               ▐░▌          ▐░▌     ▐░▌ ▄▄▄▄▄▄▄▄ ▐░█▄▄▄▄▄▄▄▄▄      ▐░▌     ▐░█▄▄▄▄▄▄▄▄▄
   ▐░░░░░░░░░░░▌▐░▌               ▐░▌          ▐░▌     ▐░▌▐░░░░░░░░▌▐░░░░░░░░░░░▌     ▐░▌     ▐░░░░░░░░░░░▌
   ▐░█▀▀▀▀▀▀▀▀▀ ▐░▌               ▐░▌          ▐░▌     ▐░▌ ▀▀▀▀▀▀█░▌▐░█▀▀▀▀▀▀▀▀▀      ▐░▌     ▐░█▀▀▀▀▀▀▀▀▀
   ▐░▌          ▐░▌               ▐░▌          ▐░▌     ▐░▌       ▐░▌▐░▌               ▐░▌     ▐░▌
   ▐░▌          ▐░█▄▄▄▄▄▄▄▄▄  ▄▄▄▄█░█▄▄▄▄      ▐░▌     ▐░█▄▄▄▄▄▄▄█░▌▐░▌           ▄▄▄▄█░█▄▄▄▄ ▐░█▄▄▄▄▄▄▄▄▄
   ▐░▌          ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌     ▐░▌     ▐░░░░░░░░░░░▌▐░▌          ▐░░░░░░░░░░░▌▐░░░░░░░░░░░▌
    ▀            ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀       ▀       ▀▀▀▀▀▀▀▀▀▀▀  ▀            ▀▀▀▀▀▀▀▀▀▀▀  ▀▀▀▀▀▀▀▀▀▀▀
{Colors.RESET}

{Colors.LIGHTNING}🚀 AI-Powered C++ Optimization Agent - Faster than a cheetah on espresso! ⚡{Colors.RESET}
{Colors.CYAN}💡 PhD-level performance engineering with infectious enthusiasm{Colors.RESET}

"""
    print(banner)


def format_analysis_output(analysis_result, use_colors: bool = True) -> str:
    """Format analysis results with colors and styling."""
    if not use_colors:
        Colors.RESET = Colors.BOLD = Colors.RED = Colors.GREEN = Colors.YELLOW = ""
        Colors.BLUE = Colors.MAGENTA = Colors.CYAN = Colors.WHITE = ""
        Colors.FIRE = Colors.LIGHTNING = Colors.SUCCESS = ""

    output = [
        f"\n{Colors.FIRE}{Colors.BOLD}🔍 ANALYSIS SUMMARY{Colors.RESET}",
        f"{Colors.CYAN}{'='*50}{Colors.RESET}",
        f"Code Hash: {analysis_result.code_hash}",
        f"Architecture: {Colors.BLUE}{analysis_result.architecture.value}{Colors.RESET}",
        f"Mode: {Colors.MAGENTA}{analysis_result.optimization_mode.value}{Colors.RESET}",
        f"Lines Analyzed: {Colors.WHITE}{analysis_result.lines_analyzed}{Colors.RESET}",
        ""
    ]

    # Complexity Analysis
    complexity = analysis_result.complexity
    output.extend([
        f"{Colors.LIGHTNING}{Colors.BOLD}⚡ COMPLEXITY ANALYSIS{Colors.RESET}",
        f"Time Complexity: {Colors.YELLOW}{complexity.time_complexity}{Colors.RESET}",
        f"Space Complexity: {Colors.YELLOW}{complexity.space_complexity}{Colors.RESET}",
        f"Loop Nesting Depth: {Colors.RED if complexity.loop_nesting_depth > 2 else Colors.GREEN}{complexity.loop_nesting_depth}{Colors.RESET}",
        f"Performance Hotspots: {Colors.FIRE}{', '.join(map(str, complexity.hotspots[:5]))}{Colors.RESET}",
        ""
    ])

    # Issues Found
    if analysis_result.issues:
        output.extend([
            f"{Colors.RED}{Colors.BOLD}🚨 ISSUES FOUND ({len(analysis_result.issues)}){Colors.RESET}",
            f"{Colors.CYAN}{'='*30}{Colors.RESET}"
        ])

        for issue in analysis_result.issues:
            severity_color = {
                'low': Colors.YELLOW,
                'medium': Colors.FIRE,
                'high': Colors.RED,
                'critical': Colors.RED + Colors.BOLD
            }.get(issue.severity, Colors.WHITE)

            output.extend([
                f"  {severity_color}Line {issue.line_number}: {issue.issue_type.upper()}{Colors.RESET}",
                f"    Description: {issue.description}",
                f"    Suggestion: {Colors.SUCCESS}{issue.suggestion}{Colors.RESET}",
                f"    Impact: {Colors.LIGHTNING}{issue.estimated_impact:.1f}x speedup{Colors.RESET}",
                ""
            ])
    else:
        output.append(f"{Colors.SUCCESS}✨ No major performance issues found! Your code is already well-optimized.{Colors.RESET}")

    # Optimization Candidates
    if analysis_result.optimization_candidates:
        output.extend([
            f"{Colors.SUCCESS}{Colors.BOLD}🎯 OPTIMIZATION OPPORTUNITIES{Colors.RESET}",
            f"{Colors.CYAN}{'='*40}{Colors.RESET}"
        ])
        for candidate in analysis_result.optimization_candidates:
            output.append(f"  • {Colors.LIGHTNING}{candidate}{Colors.RESET}")
        output.append("")

    # Performance Summary
    output.extend([
        f"{Colors.MAGENTA}{Colors.BOLD}📊 PERFORMANCE SUMMARY{Colors.RESET}",
        f"{Colors.CYAN}{'='*35}{Colors.RESET}",
        f"Baseline Score: {Colors.WHITE}{analysis_result.baseline_score:.1f}/10{Colors.RESET}",
        f"Optimization Potential: {Colors.FIRE}{analysis_result.optimization_potential:.1f}x speedup{Colors.RESET}",
        f"Critical Issues: {Colors.RED if analysis_result.critical_issues > 0 else Colors.GREEN}{analysis_result.critical_issues}{Colors.RESET}",
    ])

    return '\n'.join(output)


def format_strategy_output(strategy, use_colors: bool = True) -> str:
    """Format optimization strategy with colors and styling."""
    if not use_colors:
        Colors.RESET = Colors.BOLD = Colors.RED = Colors.GREEN = Colors.YELLOW = ""
        Colors.BLUE = Colors.MAGENTA = Colors.CYAN = Colors.WHITE = ""
        Colors.FIRE = Colors.LIGHTNING = Colors.SUCCESS = ""

    output = [
        f"\n{Colors.LIGHTNING}{Colors.BOLD}⚡ OPTIMIZATION STRATEGY{Colors.RESET}",
        f"{Colors.CYAN}{'='*45}{Colors.RESET}",
        f"Total Estimated Speedup: {Colors.FIRE}{Colors.BOLD}{strategy.total_estimated_speedup:.1f}x{Colors.RESET}",
        f"Recommended Order: {Colors.BLUE}{' → '.join(map(str, [i+1 for i in strategy.recommended_order]))}{Colors.RESET}",
        ""
    ]

    # Optimization Tiers
    for i, tier in enumerate(strategy.tiers):
        tier_color = {
            'easy': Colors.GREEN,
            'medium': Colors.YELLOW,
            'hard': Colors.RED
        }.get(tier.difficulty, Colors.WHITE)

        output.extend([
            f"{Colors.FIRE}{Colors.BOLD}🏆 TIER {tier.tier_number}: {tier.name.upper()}{Colors.RESET}",
            f"  Speedup Estimate: {Colors.LIGHTNING}{tier.estimated_speedup:.1f}x{Colors.RESET}",
            f"  Difficulty: {tier_color}{tier.difficulty.upper()}{Colors.RESET}",
            f"  Safety Impact: {Colors.CYAN}{tier.safety_impact}{Colors.RESET}",
            "",
            f"  {Colors.BOLD}Description:{Colors.RESET}",
            f"    {tier.description}",
            "",
            f"  {Colors.BOLD}Implementation:{Colors.RESET}",
            f"    {Colors.RED}Before:{Colors.RESET}",
            f"      {tier.code_before.strip()}",
            f"    {Colors.SUCCESS}After:{Colors.RESET}",
            f"      {tier.code_after.strip()}",
            "",
            f"  {Colors.BOLD}Why This Works:{Colors.RESET}",
            f"    {tier.explanation}",
            f"{Colors.CYAN}{'─'*60}{Colors.RESET}",
            ""
        ])

    # Warnings
    if strategy.warnings:
        output.extend([
            f"{Colors.YELLOW}{Colors.BOLD}⚠️  IMPORTANT WARNINGS{Colors.RESET}",
            f"{Colors.CYAN}{'='*30}{Colors.RESET}"
        ])
        for warning in strategy.warnings:
            output.append(f"  • {Colors.YELLOW}{warning}{Colors.RESET}")
        output.append("")

    # Next Steps
    if strategy.next_steps:
        output.extend([
            f"{Colors.SUCCESS}{Colors.BOLD}🎯 NEXT STEPS{Colors.RESET}",
            f"{Colors.CYAN}{'='*20}{Colors.RESET}"
        ])
        for step in strategy.next_steps:
            output.append(f"  • {Colors.LIGHTNING}{step}{Colors.RESET}")

    return '\n'.join(output)


class InteractiveCLI:
    """Interactive command-line interface for Blitzfire."""

    def __init__(self, use_colors: bool = True):
        """Initialize the CLI."""
        self.use_colors = use_colors and sys.stdout.isatty()
        self.agent = None
        self.session_id = f"cli_session_{int(time.time())}"

    async def initialize_agent(self):
        """Initialize the Blitzfire agent."""
        from .agent import BlitzfireCodeAgent
        from .providers import get_llm_model

        try:
            self.agent = BlitzfireCodeAgent(session_id=self.session_id)
            if self.use_colors:
                print(f"{Colors.SUCCESS}✅ Blitzfire agent initialized successfully!{Colors.RESET}")
            else:
                print("✅ Blitzfire agent initialized successfully!")
        except Exception as e:
            if self.use_colors:
                print(f"{Colors.RED}❌ Failed to initialize agent: {e}{Colors.RESET}")
            else:
                print(f"❌ Failed to initialize agent: {e}")
            return False
        return True

    async def run_interactive_mode(self):
        """Run the interactive REPL mode."""
        print_banner()

        if not await self.initialize_agent():
            return

        print(f"{Colors.FIRE}🎯 Welcome to Interactive Optimization Mode!{Colors.RESET}")
        print(f"{Colors.CYAN}Type your C++ code, 'help' for commands, or 'quit' to exit.{Colors.RESET}")
        print(f"{Colors.YELLOW}Use 'paste' for multi-line code input.{Colors.RESET}\n")

        while True:
            try:
                # Get user input
                prompt = f"{Colors.LIGHTNING}Blitzfire>{Colors.RESET} " if self.use_colors else "Blitzfire> "
                user_input = input(prompt).strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print(f"{Colors.SUCCESS}🚀 Thanks for using Blitzfire! Keep optimizing!{Colors.RESET}")
                    break

                elif user_input.lower() in ['help', 'h']:
                    self.show_help()

                elif user_input.lower() == 'paste':
                    await self.handle_multiline_input()

                elif user_input.lower().startswith('analyze '):
                    # Analyze file
                    filename = user_input[8:].strip()
                    await self.analyze_file(filename)

                elif user_input.lower().startswith('mode '):
                    # Change optimization mode
                    mode = user_input[5:].strip()
                    self.change_mode(mode)

                else:
                    # Try to analyze as code or chat
                    if any(keyword in user_input.lower() for keyword in ['#include', 'int', 'void', 'class', 'struct']):
                        await self.quick_analyze_code(user_input)
                    else:
                        await self.chat_with_agent(user_input)

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Use 'quit' to exit gracefully.{Colors.RESET}")
            except EOFError:
                break
            except Exception as e:
                print(f"{Colors.RED}❌ Error: {e}{Colors.RESET}")

    async def handle_multiline_input(self):
        """Handle multi-line code input."""
        print(f"{Colors.CYAN}📝 Multi-line input mode. End with a line containing just 'END'{Colors.RESET}")

        lines = []
        while True:
            try:
                line = input("... ")
                if line.strip() == 'END':
                    break
                lines.append(line)
            except (KeyboardInterrupt, EOFError):
                print(f"\n{Colors.YELLOW}Multi-line input cancelled.{Colors.RESET}")
                return

        if lines:
            code = '\n'.join(lines)
            await self.quick_analyze_code(code)

    async def analyze_file(self, filename: str):
        """Analyze a C++ file."""
        try:
            file_path = Path(filename)
            if not file_path.exists():
                print(f"{Colors.RED}❌ File not found: {filename}{Colors.RESET}")
                return

            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            print(f"{Colors.BLUE}📂 Analyzing file: {filename}{Colors.RESET}")
            await self.quick_analyze_code(code)

        except Exception as e:
            print(f"{Colors.RED}❌ Failed to analyze file: {e}{Colors.RESET}")

    async def quick_analyze_code(self, code: str):
        """Quick analysis of provided code."""
        if not self.agent:
            print(f"{Colors.RED}❌ Agent not initialized{Colors.RESET}")
            return

        try:
            print(f"{Colors.FIRE}🔍 Analyzing your code...{Colors.RESET}")
            start_time = time.time()

            response = await self.agent.analyze_and_optimize(
                code_content=code,
                include_benchmarks=False,  # Skip for quick analysis
                include_assembly=False
            )

            analysis_time = time.time() - start_time

            # Display results
            print(format_analysis_output(response.analysis, self.use_colors))
            print(format_strategy_output(response.strategy, self.use_colors))

            # Display personality message
            print(f"\n{Colors.FIRE}{Colors.BOLD}💬 BLITZFIRE SAYS:{Colors.RESET}")
            print(f"{response.personality_message}")

            # Educational insights
            if response.educational_insights:
                print(f"\n{Colors.CYAN}{Colors.BOLD}🧠 LEARNING INSIGHTS:{Colors.RESET}")
                for insight in response.educational_insights:
                    print(f"  💡 {insight}")

            print(f"\n{Colors.MAGENTA}⚡ Blitzfire Score: {response.blitzfire_score}/10{Colors.RESET}")
            print(f"{Colors.CYAN}📊 Analysis completed in {analysis_time:.2f} seconds{Colors.RESET}")

        except Exception as e:
            print(f"{Colors.RED}❌ Analysis failed: {e}{Colors.RESET}")

    async def chat_with_agent(self, message: str):
        """Chat with the agent."""
        if not self.agent:
            print(f"{Colors.RED}❌ Agent not initialized{Colors.RESET}")
            return

        try:
            response = await self.agent.chat(message)
            print(f"{Colors.SUCCESS}{response}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.RED}❌ Chat failed: {e}{Colors.RESET}")

    def change_mode(self, mode: str):
        """Change optimization mode."""
        valid_modes = ['general', 'hft', 'embedded', 'game']
        if mode.lower() in valid_modes:
            print(f"{Colors.SUCCESS}🔧 Mode changed to: {mode}{Colors.RESET}")
            # Would update agent configuration here
        else:
            print(f"{Colors.RED}❌ Invalid mode. Valid modes: {', '.join(valid_modes)}{Colors.RESET}")

    def show_help(self):
        """Show help information."""
        help_text = f"""
{Colors.FIRE}{Colors.BOLD}🚀 BLITZFIRE COMMAND REFERENCE{Colors.RESET}

{Colors.LIGHTNING}Code Analysis:{Colors.RESET}
  • Type or paste C++ code directly for immediate analysis
  • {Colors.CYAN}paste{Colors.RESET} - Enter multi-line code mode
  • {Colors.CYAN}analyze <filename>{Colors.RESET} - Analyze a C++ source file

{Colors.LIGHTNING}Conversation:{Colors.RESET}
  • Ask questions about optimization techniques
  • Get explanations of compiler behavior
  • Learn about performance patterns

{Colors.LIGHTNING}Configuration:{Colors.RESET}
  • {Colors.CYAN}mode <general|hft|embedded|game>{Colors.RESET} - Change optimization mode

{Colors.LIGHTNING}Navigation:{Colors.RESET}
  • {Colors.CYAN}help{Colors.RESET} - Show this help message
  • {Colors.CYAN}quit{Colors.RESET} - Exit Blitzfire

{Colors.SUCCESS}💡 Pro Tips:{Colors.RESET}
  • Start with small code snippets to understand optimization patterns
  • Ask "why" questions to learn the theory behind optimizations
  • Use HFT mode for financial code quality analysis
  • Try embedded mode for memory-constrained optimizations

{Colors.FIRE}Example Questions:{Colors.RESET}
  • "How does SIMD vectorization work?"
  • "What makes code cache-friendly?"
  • "Explain loop unrolling benefits"
"""
        print(help_text)


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Blitzfire Code Agent - AI-Powered C++ Optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  blitzfire                          # Interactive mode
  blitzfire analyze main.cpp         # Analyze a file
  blitzfire --mode hft analyze trading.cpp  # HFT mode analysis
  blitzfire --no-colors --quiet      # Minimal output
"""
    )

    parser.add_argument(
        'command',
        nargs='?',
        choices=['analyze', 'interactive'],
        default='interactive',
        help='Command to execute'
    )

    parser.add_argument(
        'file',
        nargs='?',
        help='File to analyze (for analyze command)'
    )

    parser.add_argument(
        '--mode',
        choices=['general', 'hft', 'embedded', 'game'],
        default='general',
        help='Optimization mode'
    )

    parser.add_argument(
        '--no-colors',
        action='store_true',
        help='Disable colored output'
    )

    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output'
    )

    args = parser.parse_args()

    # Initialize CLI
    cli = InteractiveCLI(use_colors=not args.no_colors)

    if args.command == 'analyze' and args.file:
        # File analysis mode
        if not args.quiet:
            print_banner()
        if await cli.initialize_agent():
            await cli.analyze_file(args.file)
    else:
        # Interactive mode
        await cli.run_interactive_mode()


if __name__ == "__main__":
    asyncio.run(main())