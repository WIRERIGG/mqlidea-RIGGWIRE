"""
Command Line Interface for Clang-Tidy AI Agent.
Provides interactive and batch processing capabilities for C++ code analysis.
"""

import asyncio
import sys
import argparse
from pathlib import Path
from typing import Optional, List

from agent import ClangTidyFactoryOrchestrator, analyze_cpp_file
from dependencies import create_dependencies, create_test_dependencies


class ClangTidyAICLI:
    """Command line interface for the Clang-Tidy AI Agent."""
    
    def __init__(self):
        self.orchestrator: Optional[ClangTidyFactoryOrchestrator] = None
    
    async def initialize(self, config_path: Optional[str] = None, test_mode: bool = False):
        """Initialize the CLI with dependencies."""
        try:
            if test_mode:
                deps = create_test_dependencies()
            else:
                deps = create_dependencies(config_path=config_path)
            
            self.orchestrator = ClangTidyFactoryOrchestrator(deps)
            print("✅ Clang-Tidy Factory Orchestrator initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Initialization failed: {e}")
            return False
    
    async def analyze_file(self, file_path: str, scope: str = "comprehensive") -> bool:
        """Analyze a single C++ file."""
        if not self.orchestrator:
            print("❌ Orchestrator not initialized. Run with --init first.")
            return False
        
        try:
            print(f"🔍 Analyzing file: {file_path} (scope: {scope})")
            result = await self.orchestrator.analyze_file_simple(file_path)
            print(result)
            return True
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return False
    
    async def run_full_workflow(self, file_path: str) -> bool:
        """Run the complete 5-phase workflow on a file."""
        if not self.orchestrator:
            print("❌ Orchestrator not initialized. Run with --init first.")
            return False
        
        try:
            print(f"🚀 Starting complete 5-phase workflow for: {file_path}")
            results = await self.orchestrator.run_complete_workflow(file_path)
            
            # Display results summary
            if results.get('workflow_completed'):
                summary = results.get('workflow_summary', {})
                print(f"""
🎉 Workflow Completed Successfully!

📊 Results Summary:
  • Total Issues Discovered: {summary.get('total_issues_discovered', 0)}
  • Total Fixes Applied: {summary.get('total_fixes_applied', 0)}
  • Validation Passed: {'✅' if summary.get('validation_passed') else '❌'}
  • Archon Integration: {'✅' if summary.get('archon_integration_successful') else '❌'}

📝 Detailed Results:
  • Phase 1 (Discovery): {len(results.get('phase1_discovery', {}).get('critical_issues', []))} critical, {len(results.get('phase1_discovery', {}).get('high_priority_issues', []))} high priority
  • Phase 2 (Strategy): {len(results.get('phase2_strategy', {}).get('fix_order', []))} fix stages planned
  • Phase 3 (Fixes): {len([k for k in results.keys() if k.startswith('phase3_')])} fix types applied
  • Phase 4 (Validation): {'PASSED' if results.get('phase4_validation', {}).get('validation_passed') else 'FAILED'}
  • Phase 5 (Archon): {'CONNECTED' if results.get('phase5_archon', {}).get('task_created') else 'OFFLINE'}
""")
                return True
            else:
                print(f"❌ Workflow failed: {results.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            return False
    
    async def analyze_project(self, pattern: str) -> bool:
        """Analyze multiple files matching a pattern."""
        if not self.orchestrator:
            print("❌ Orchestrator not initialized. Run with --init first.")
            return False
        
        try:
            from pathlib import Path
            import glob
            
            # Find files matching pattern
            files = glob.glob(pattern, recursive=True)
            cpp_files = [f for f in files if f.endswith(('.cpp', '.cc', '.cxx', '.C'))]
            
            if not cpp_files:
                print(f"❌ No C++ files found matching pattern: {pattern}")
                return False
            
            print(f"🔍 Found {len(cpp_files)} C++ files to analyze:")
            for f in cpp_files:
                print(f"  • {f}")
            
            # Analyze each file
            total_issues = 0
            total_fixes = 0
            success_count = 0
            
            for file_path in cpp_files:
                print(f"\n📁 Analyzing: {file_path}")
                try:
                    discovery = await self.orchestrator.comprehensive_issue_discovery(file_path)
                    total_issues += discovery.total_issues
                    
                    print(f"   Issues: {discovery.total_issues} "
                          f"(Critical: {len(discovery.critical_issues)}, "
                          f"High: {len(discovery.high_priority_issues)}, "
                          f"Medium: {len(discovery.medium_priority_issues)}, "
                          f"Low: {len(discovery.low_priority_issues)})")
                    
                    success_count += 1
                    
                except Exception as e:
                    print(f"   ❌ Failed: {e}")
            
            print(f"""
🎯 Project Analysis Summary:
  • Files Analyzed: {success_count}/{len(cpp_files)}
  • Total Issues Found: {total_issues}
  • Average Issues per File: {total_issues / max(success_count, 1):.1f}

💡 Recommendations:
  • Focus on files with critical issues first
  • Run full workflow on problematic files: --workflow <file>
  • Consider batch fixing with systematic approach
""")
            
            return success_count > 0
            
        except Exception as e:
            print(f"❌ Project analysis failed: {e}")
            return False
    
    async def interactive_mode(self) -> None:
        """Run interactive mode."""
        print("""
🤖 Clang-Tidy Factory Orchestrator - Interactive Mode

Available commands:
  analyze <file>     - Analyze single file
  workflow <file>    - Run complete 5-phase workflow  
  project <pattern>  - Analyze project files (e.g., "src/**/*.cpp")
  help              - Show this help
  exit              - Exit interactive mode

Examples:
  analyze tests/safe_test.cpp
  workflow src/main.cpp  
  project "src/**/*.cpp"
""")
        
        while True:
            try:
                command = input("\n🔧 clang-tidy-ai> ").strip()
                
                if not command:
                    continue
                    
                if command.lower() in ['exit', 'quit', 'q']:
                    print("👋 Goodbye!")
                    break
                    
                if command.lower() in ['help', 'h', '?']:
                    print("""
Available commands:
  analyze <file>     - Analyze single file with issue discovery
  workflow <file>    - Run complete 5-phase factory workflow
  project <pattern>  - Analyze multiple files matching pattern
  scope <scope>      - Set analysis scope (comprehensive, critical, performance, quality)
  help              - Show this help message
  exit              - Exit interactive mode
""")
                    continue
                
                parts = command.split(' ', 1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""
                
                if cmd == 'analyze' and arg:
                    await self.analyze_file(arg)
                elif cmd == 'workflow' and arg:
                    await self.run_full_workflow(arg)
                elif cmd == 'project' and arg:
                    await self.analyze_project(arg)
                elif cmd == 'scope' and arg:
                    print(f"Analysis scope set to: {arg}")
                    # Could implement scope persistence here
                else:
                    print(f"❌ Unknown command: {command}")
                    print("Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Command failed: {e}")
    
    async def demo_mode(self) -> bool:
        """Run demonstration mode with test file."""
        print("🎬 Running Clang-Tidy Factory Orchestrator Demo...")
        
        # Look for a good demo file
        demo_files = [
            "/IdeaProjects/wire_ground/tests/safe_test.cpp",
            "/IdeaProjects/wire_ground/src/main.cpp", 
            "/IdeaProjects/wire_ground/tests/default_test.cpp"
        ]
        
        demo_file = None
        for file_path in demo_files:
            if Path(file_path).exists():
                demo_file = file_path
                break
        
        if not demo_file:
            print("❌ No suitable demo file found. Please specify a C++ file manually.")
            return False
        
        print(f"📝 Using demo file: {demo_file}")
        
        # Run quick analysis
        print("\n🔍 Phase 1: Quick Analysis Demo...")
        await self.analyze_file(demo_file, scope="comprehensive")
        
        # Ask if user wants full workflow
        print("\n🚀 Would you like to run the complete 5-phase workflow? (y/n): ", end="")
        try:
            response = input().strip().lower()
            if response in ['y', 'yes']:
                return await self.run_full_workflow(demo_file)
            else:
                print("Demo completed. Use --interactive for more exploration.")
                return True
        except KeyboardInterrupt:
            print("\nDemo interrupted.")
            return False


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Clang-Tidy Factory Orchestrator - AI-Enhanced C++ Code Quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive mode
  python cli.py --interactive
  
  # Analyze single file
  python cli.py --analyze tests/safe_test.cpp
  
  # Run complete workflow
  python cli.py --workflow src/main.cpp
  
  # Analyze project
  python cli.py --project "src/**/*.cpp"
  
  # Demo mode
  python cli.py --demo
  
  # Test mode (for validation)
  python cli.py --test --analyze dummy.cpp
"""
    )
    
    parser.add_argument('--analyze', '-a', metavar='FILE',
                       help='Analyze a single C++ file')
    parser.add_argument('--workflow', '-w', metavar='FILE',
                       help='Run complete 5-phase workflow on a file')
    parser.add_argument('--project', '-p', metavar='PATTERN',
                       help='Analyze project files matching pattern (e.g. "src/**/*.cpp")')
    parser.add_argument('--interactive', '-i', action='store_true',
                       help='Run in interactive mode')
    parser.add_argument('--demo', '-d', action='store_true',
                       help='Run demonstration mode')
    parser.add_argument('--scope', '-s', choices=['comprehensive', 'critical', 'performance', 'quality'],
                       default='comprehensive', help='Analysis scope')
    parser.add_argument('--config', '-c', metavar='CONFIG_PATH',
                       help='Path to configuration file')
    parser.add_argument('--test', '-t', action='store_true',
                       help='Run in test mode (for validation)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Create CLI instance
    cli = ClangTidyAICLI()
    
    # Initialize
    print("🔧 Initializing Clang-Tidy Factory Orchestrator...")
    if not await cli.initialize(config_path=args.config, test_mode=args.test):
        return 1
    
    success = True
    
    try:
        # Execute based on arguments
        if args.demo:
            success = await cli.demo_mode()
        elif args.interactive:
            await cli.interactive_mode()
        elif args.analyze:
            success = await cli.analyze_file(args.analyze, args.scope)
        elif args.workflow:
            success = await cli.run_full_workflow(args.workflow)
        elif args.project:
            success = await cli.analyze_project(args.project)
        else:
            # No specific command, show help and run demo
            parser.print_help()
            print("\n🎬 Running demo mode by default...")
            success = await cli.demo_mode()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    # Run the CLI
    exit_code = asyncio.run(main())
    sys.exit(exit_code)